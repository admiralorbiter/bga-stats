"""
BGA Pull Move Stats - Extract match move statistics from BGA using Playwright.
Mirrors the functionality of the MoveStats.js bookmarklet.
"""

import json
from typing import Optional, List, Dict, Any
from playwright.sync_api import BrowserContext, Page
from backend.services.bga_pull_base import BGAPullBase, RateLimiter


class BGAMoveStatsPuller(BGAPullBase):
    """Pull move statistics from BGA game review pages."""
    
    def __init__(self, context: BrowserContext, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(context, rate_limiter or RateLimiter(min_delay_seconds=0.5))
    
    def pull_multiple_matches(self, table_ids: List[str]) -> Optional[str]:
        """
        Pull move stats for multiple table IDs.
        
        Args:
            table_ids: List of BGA table IDs
            
        Returns:
            Semicolon-delimited string with all move data or None on failure
        """
        page = self.create_page()

        # Helpful diagnostics when BGA DOM changes.
        # (Playwright console logs show up in the Flask terminal.)
        try:
            page.on("console", lambda msg: print(f"  Browser console: {msg.text}"))
            page.on("pageerror", lambda err: print(f"  Browser pageerror: {err}"))
        except Exception:
            # Best-effort only; never fail pulling due to logging hooks.
            pass
        
        try:
            all_match_data = []
            
            for idx, table_id in enumerate(table_ids):
                print(f"Pulling match {idx + 1}/{len(table_ids)}: Table #{table_id}")
                
                match_data = self._extract_move_data(page, table_id)
                
                if match_data:
                    all_match_data.append(match_data)
                else:
                    print(f"Warning: Failed to extract data for table {table_id}")
                
                # Rate limiting
                if self.rate_limiter and idx < len(table_ids) - 1:
                    self.rate_limiter.wait()
            
            if not all_match_data:
                return None
            
            # Combine all match data (each match is already newline-separated rows)
            return "\n".join(all_match_data)
            
        finally:
            page.close()
    
    def discover_from_tournaments(self, limit: int = 50) -> List[str]:
        """
        Discover table IDs from already-imported tournaments.
        
        Args:
            limit: Maximum number of matches to discover
            
        Returns:
            List of table IDs from tournament matches
        """
        from backend.db import get_session
        from backend.models import TournamentMatch
        
        try:
            session = get_session()
            
            # Prefer completed matches (progress=100) and newest first.
            # DISTINCT + ORDER can be unreliable in sqlite, so we de-dupe in Python.
            rows = (
                session.query(TournamentMatch.bga_table_id)
                .filter(TournamentMatch.progress == 100)
                .order_by(TournamentMatch.created_at.desc())
                .all()
            )

            table_ids: List[str] = []
            seen: set[int] = set()
            for (bga_table_id,) in rows:
                if bga_table_id is None:
                    continue
                if bga_table_id in seen:
                    continue
                seen.add(bga_table_id)
                table_ids.append(str(bga_table_id))
                if len(table_ids) >= limit:
                    break

            print(f"Found {len(table_ids)} matches from imported tournaments")
            return table_ids
            
        except Exception as e:
            print(f"Error querying tournaments: {e}")
            return []
        finally:
            session.close()
    
    def discover_recent_matches(self, limit: int = 50) -> List[str]:
        """
        Discover recent match table IDs from user's game history.
        
        Args:
            limit: Maximum number of matches to discover
            
        Returns:
            List of table IDs
        """
        page = self.create_page()
        
        try:
            # Try multiple sources to find completed matches
            table_ids = []
            
            # Source 1: Game in progress page
            print("Checking gameinprogress page...")
            if self.safe_navigate(page, 'https://boardgamearena.com/gameinprogress'):
                page.wait_for_load_state('networkidle', timeout=10000)
                
                ids = page.evaluate(f"""
                    () => {{
                        const tableIds = [];
                        const limit = {limit};
                        
                        // Look for links to game reviews (completed matches)
                        const reviewLinks = document.querySelectorAll('a[href*="gamereview?table="]');
                        console.log('Found', reviewLinks.length, 'review links on gameinprogress');
                        
                        reviewLinks.forEach(link => {{
                            if (tableIds.length >= limit) return;
                            
                            const match = link.href.match(/gamereview\\?table=(\\d+)/);
                            if (match && !tableIds.includes(match[1])) {{
                                tableIds.push(match[1]);
                            }}
                        }});
                        
                        return tableIds;
                    }}
                """)
                
                if ids:
                    print(f"Found {len(ids)} matches on gameinprogress page")
                    table_ids.extend(ids)
            
            # Source 2: Try player profile page if not enough matches
            if len(table_ids) < limit:
                print("Checking player profile page...")
                if self.safe_navigate(page, 'https://boardgamearena.com/playerstat'):
                    page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Click on "Finished games" tab if it exists
                    try:
                        page.evaluate("""
                            () => {
                                const tabs = document.querySelectorAll('.bga-tab, .tablink');
                                for (const tab of tabs) {
                                    if (tab.innerText.toLowerCase().includes('finish') || 
                                        tab.innerText.toLowerCase().includes('completed')) {
                                        tab.click();
                                        return true;
                                    }
                                }
                                return false;
                            }
                        """)
                        page.wait_for_timeout(1000)
                    except:
                        pass
                    
                    ids = page.evaluate(f"""
                        () => {{
                            const tableIds = [];
                            const limit = {limit};
                            
                            // Look for any game review links
                            const links = document.querySelectorAll('a[href*="gamereview"]');
                            console.log('Found', links.length, 'review links on profile');
                            
                            links.forEach(link => {{
                                if (tableIds.length >= limit) return;
                                
                                const match = link.href.match(/table=(\\d+)/);
                                if (match && !tableIds.includes(match[1])) {{
                                    tableIds.push(match[1]);
                                }}
                            }});
                            
                            return tableIds;
                        }}
                    """)
                    
                    if ids:
                        print(f"Found {len(ids)} additional matches on profile page")
                        for id in ids:
                            if id not in table_ids and len(table_ids) < limit:
                                table_ids.append(id)
            
            print(f"Total discovered: {len(table_ids)} recent matches")
            
            # If still no matches found, try getting from imported tournaments
            if not table_ids:
                print("No matches found on BGA pages, checking imported tournaments...")
                tournament_ids = self.discover_from_tournaments(limit)
                if tournament_ids:
                    print(f"Using {len(tournament_ids)} matches from tournaments")
                    return tournament_ids
            
            return table_ids[:limit]
            
        finally:
            page.close()
    
    def _extract_move_data(self, page: Page, table_id: str) -> Optional[str]:
        """
        Extract move timeline data from a game review page.
        Mirrors MoveStats.js bookmarklet logic.
        
        Args:
            page: Playwright page object
            table_id: BGA table ID
            
        Returns:
            Semicolon-delimited string with move data for this match or None on error
        """
        # Navigate to game review page
        url = f'https://boardgamearena.com/gamereview?table={table_id}'
        if not self.safe_navigate(page, url):
            print(f"Failed to navigate to {url}")
            return None
        
        # Wait for game logs to load (BGA can be slow / dynamic)
        try:
            page.wait_for_selector('#gamelogs, .gamelogreview', timeout=15000)
            try:
                page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                pass
        except Exception as e:
            print(f"Timeout waiting for game logs: {e}")
            return None
        
        # Extract move data using JavaScript (mirrors bookmarklet logic, but more robust to DOM changes)
        # Use a raw Python string to avoid \s escape warnings (JS regexes inside).
        result: Dict[str, Any] = page.evaluate(r"""
            () => {
                function JSDateToExcelDate(inDate) {
                    var returnDateTime = 25569.0 + ((inDate.getTime() - (inDate.getTimezoneOffset() * 60 * 1000)) / (1000 * 60 * 60 * 24));
                    return returnDateTime.toString().substr(0,20).replace(".", ",");
                }
                
                const debug = {
                    href: window.location.href,
                    title: document.title,
                    reviewTitleText: "",
                    parsedTableID: "",
                    parsedGameName: "",
                    playersCount: 0,
                    logsContainerFound: false,
                    logsCount: 0,
                    sampleLogClasses: [],
                    errors: []
                };

                var output = "";

                // Table ID: prefer URL param, fallback to any "#123" in title.
                let tableID = "";
                try {
                    tableID = new URL(window.location.href).searchParams.get("table") || "";
                } catch (e) {
                    // ignore
                }

                // Game name + (sometimes) table id from the review title
                let gameName = "";
                try {
                    const reviewEl =
                        document.querySelector("#reviewtitle") ||
                        document.querySelector(".pageheader h1") ||
                        document.querySelector("h1");

                    const reviewText = (reviewEl ? reviewEl.innerText : "").trim();
                    debug.reviewTitleText = reviewText;

                    // If title contains "#12345" prefer that.
                    const idMatch = reviewText.match(/#(\\d+)/);
                    if (idMatch) {
                        tableID = idMatch[1];
                    }

                    // Try to remove leading label(s) and trailing "#id"
                    // Examples we've seen: "Replay Azul #123", "Game review: Azul #123"
                    gameName = reviewText
                        .replace(/#\\d+.*$/, "")
                        .replace(/^(Replay|Review|Game review|Game replay)\\s*:?\s*/i, "")
                        .trim();

                    // If still not great, fall back to document title
                    if (!gameName) {
                        gameName = (document.title || "").replace(/#\\d+.*$/, "").trim();
                    }
                } catch (error) {
                    debug.errors.push("title_parse: " + String(error));
                }

                debug.parsedTableID = String(tableID || "");
                debug.parsedGameName = String(gameName || "");

                if (!tableID) {
                    debug.errors.push("missing_table_id");
                    return { output: "", debug };
                }

                if (!gameName) {
                    gameName = "Unknown";
                }

                // Players
                const playerSelectors = [
                    "#game_result .name",
                    "#game_result .playername",
                    ".gameresult .name",
                    ".playername",
                ];
                let playerNodes = [];
                for (const sel of playerSelectors) {
                    const nodes = Array.from(document.querySelectorAll(sel));
                    if (nodes.length) {
                        playerNodes = nodes;
                        break;
                    }
                }
                var players = playerNodes.map(item => (item.innerText || "").trim()).filter(Boolean);
                debug.playersCount = players.length;

                // Logs container
                const logsContainer =
                    document.querySelector("#gamelogs") ||
                    document.querySelector("#gamelogs_inner") ||
                    document.querySelector(".gamelogs");

                if (!logsContainer) {
                    debug.errors.push("missing_gamelogs_container");
                    return { output: "", debug };
                }

                debug.logsContainerFound = true;
                var logs = logsContainer.children;
                debug.logsCount = logs ? logs.length : 0;
                debug.sampleLogClasses = Array.from(logs || []).slice(0, 15).map(el => el.className || "");

                var moveNo = 0;
                var datetime;
                var player;
                var remaining;
                var changed = false;
                var next = 1;
                var rowsProcessed = 0;
                
                for (var i = 0; i < logs.length; i++) {
                    try {
                        const cls = logs[i].className || "";
                        
                        // Check for move number and timestamp in smalltext
                        if (cls === "smalltext" || (logs[i].classList && logs[i].classList.contains("smalltext"))) {
                            player = undefined;
                            const txt = (logs[i].innerText || "").trim();
                            
                            // Try multiple regex patterns for move number
                            let mm = txt.match(/Move (\\d+|null)\\s*:/i);
                            if (!mm) mm = txt.match(/(\\d+|null)\\s*:/);
                            if (!mm) mm = txt.match(/^(\\d+|null)/);
                            
                            if (mm) {
                                const parsedMove = mm[1] === "null" ? next : Number(mm[1]);
                                if (!isNaN(parsedMove)) {
                                    moveNo = parsedMove;
                                    next = moveNo + 1;
                                } else {
                                    moveNo = next;
                                    next = moveNo + 1;
                                }
                            } else {
                                // If no match, use next sequential number
                                moveNo = next;
                                next++;
                            }

                            // Extract timestamp
                            const span = logs[i].querySelector("span");
                            var timeStr = span ? (span.innerText || "").trim() : "";
                            var parsed = new Date(timeStr);
                            if (isNaN(parsed.getTime())) {
                                if (datetime && timeStr) {
                                    datetime = new Date(datetime.toDateString() + ' ' + timeStr);
                                } else {
                                    datetime = new Date(txt);
                                }
                            } else {
                                datetime = parsed;
                            }
                            changed = true;
                        }
                        // Look for player name in gamelogreview
                        else if (player === undefined && cls.includes("gamelogreview")) {
                            const logText = logs[i].innerText || "";
                            var minidx = logText.length;
                            for (let j = 0; j < players.length; j++) {
                                let where = logText.indexOf(players[j]);
                                if (where >= 0 && where <= minidx) {
                                    minidx = where;
                                    player = players[j];
                                    changed = true;
                                }
                            }
                        }
                        // Look for remaining time
                        else if (player !== undefined && cls.includes("reflexiontimes")) {
                            const rows = Array.from(logs[i].children || []);
                            for (var j = 0; j < rows.length; j++) {
                                const rowText = (rows[j].innerText || "").trim();
                                if (rowText.indexOf(player) === 0) {
                                    const first = rows[j].children[0];
                                    remaining = first ? (first.innerText || "").trim() : "";
                                    changed = true;
                                    break;
                                }
                            }
                        }
                    } catch (error) {
                        debug.errors.push("parse_element_" + i + ": " + String(error));
                    }
                    
                    // Output row when we have all required data
                    if (changed && player !== undefined && moveNo !== undefined && datetime) {
                        if (!isNaN(datetime.getTime())) {
                            output += [tableID, gameName, moveNo, datetime.toLocaleString(), JSDateToExcelDate(datetime), player, remaining || ""].join(";") + "\n";
                            rowsProcessed++;
                            // Reset all state for next move (player will be reset on next smalltext anyway)
                            moveNo = undefined;
                            player = undefined;
                            remaining = undefined;
                            changed = false;
                        }
                    }
                }
                
                console.log("Total rows output:", rowsProcessed, "from", logs.length, "log entries");
                debug.rowsProcessed = rowsProcessed;
                
                return { output, debug };
            }
        """)
        
        output = (result or {}).get("output") if isinstance(result, dict) else None
        debug = (result or {}).get("debug") if isinstance(result, dict) else None

        if output and str(output).strip():
            output_str = str(output).strip()
            # Count actual newlines in the output
            rows = output_str.count('\n') + 1 if output_str else 0
            # Debug: show first 200 chars
            preview = output_str[:200].replace('\n', '\\n')
            print(f"  ✓ Extracted {rows} moves from table {table_id} (preview: {preview}...)")
            return output_str

        # High-signal diagnostics for why extraction produced no rows
        if isinstance(debug, dict):
            print(f"  MoveStats debug for table {table_id}:")
            print(f"    url: {debug.get('href')}")
            print(f"    title: {debug.get('title')}")
            print(f"    reviewTitleText: {debug.get('reviewTitleText')}")
            print(f"    parsedTableID: {debug.get('parsedTableID')}")
            print(f"    parsedGameName: {debug.get('parsedGameName')}")
            print(f"    playersCount: {debug.get('playersCount')}, logsCount: {debug.get('logsCount')}, rowsProcessed: {debug.get('rowsProcessed', 0)}")
            errs = debug.get("errors") or []
            if errs:
                print(f"    errors: {errs[:8]}")
            classes = debug.get("sampleLogClasses") or []
            if classes:
                print(f"    sampleLogClasses: {classes[:10]}")
        
        return None
