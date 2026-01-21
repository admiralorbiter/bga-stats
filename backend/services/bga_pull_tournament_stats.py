"""
BGA Pull Tournament Stats - Extract tournament data from BGA using Playwright.
Mirrors the functionality of the TournamentStats.js bookmarklet.
"""

import json
import re
from typing import Optional, List
from playwright.sync_api import BrowserContext, Page
from backend.services.bga_pull_base import BGAPullBase, RateLimiter


class BGATournamentStatsPuller(BGAPullBase):
    """Pull tournament statistics from BGA."""
    
    def __init__(self, context: BrowserContext, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(context, rate_limiter)
    
    def pull_all_tournaments(self) -> Optional[str]:
        """
        Pull all finished tournaments for the logged-in user.
        
        Process:
        1. Navigate to https://boardgamearena.com/tournamentlist
        2. Apply filters: finished tournaments + only my tournaments
        3. Scrape list of tournament IDs
        4. For each tournament, fetch detailed data
        5. Combine all data into TSV format
        
        Returns:
            TSV-formatted string with all tournament data or None on failure
        """
        page = self.create_page()
        
        try:
            # Navigate to tournament list
            if not self.safe_navigate(page, 'https://boardgamearena.com/tournamentlist'):
                print("Failed to navigate to tournament list")
                return None
            
            # Wait for page load
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # Apply filters using JavaScript to click checkboxes/radio buttons
            # Filter: Status = Finished, Only tournaments I registered for
            page.evaluate("""
                // Click "Finished" filter
                document.querySelector('input[value="finished"]')?.click();
                // Check "Only tournaments I registered for"
                document.querySelector('input#only_my_tournaments')?.click();
            """)
            
            # Wait for filtered results
            page.wait_for_timeout(2000)
            
            # Extract tournament IDs from the page
            tournament_ids = self._extract_tournament_ids(page)
            
            if not tournament_ids:
                print("No tournaments found")
                return ""  # Return empty string, not None (no tournaments is valid)
            
            print(f"Found {len(tournament_ids)} tournaments to pull")
            
            # Pull data for each tournament
            all_tournament_data = []
            
            for idx, tournament_id in enumerate(tournament_ids):
                print(f"Pulling tournament {idx + 1}/{len(tournament_ids)}: {tournament_id}")
                
                tournament_data = self._pull_tournament_data(page, tournament_id)
                
                if tournament_data:
                    all_tournament_data.append(tournament_data)
                
                # Rate limiting
                if self.rate_limiter:
                    self.rate_limiter.wait()
            
            # Combine all TSV data
            if not all_tournament_data:
                return ""
            
            return "\n\n".join(all_tournament_data)
            
        finally:
            page.close()
    
    def _extract_tournament_ids(self, page: Page) -> List[str]:
        """Extract tournament IDs from the tournament list page."""
        tournament_ids = page.evaluate("""
            () => {
                const links = document.querySelectorAll('a[href*="tournament?id="]');
                const ids = new Set();
                links.forEach(link => {
                    const match = link.href.match(/tournament\\?id=(\\d+)/);
                    if (match) {
                        ids.add(match[1]);
                    }
                });
                return Array.from(ids);
            }
        """)
        return tournament_ids or []
    
    def _pull_tournament_data(self, page: Page, tournament_id: str) -> Optional[str]:
        """
        Pull data for a specific tournament.
        Mirrors TournamentStats.js bookmarklet logic.
        """
        # Navigate to tournament page
        url = f'https://boardgamearena.com/tournament?id={tournament_id}'
        
        if not self.safe_navigate(page, url):
            print(f"Failed to navigate to tournament {tournament_id}")
            return None
        
        page.wait_for_load_state('networkidle', timeout=10000)
        
        # Wait a bit longer for dynamic content
        page.wait_for_timeout(2000)
        
        # Extract tournament data using the bookmarklet logic
        # This requires fetching BGA request token and making API calls
        tsv_data = page.evaluate("""
            async () => {
                // Get request token (same as bookmarklet)
                const tokenResponse = await fetch("https://boardgamearena.com");
                const tokenHtml = await tokenResponse.text();
                const tokenMatch = tokenHtml.match(/requestToken:\\s+'([^']+)'/);
                
                if (!tokenMatch) {
                    return null;
                }
                
                const headers = new Headers([["x-request-token", tokenMatch[1]]]);
                
                // Get tournament info
                const tournamentId = window.location.href.match(/tournament\\?id=(\\d+)/)?.[1];
                if (!tournamentId) return null;
                
                // Fetch the HTML directly to get the original timestamp before JavaScript converts it
                const tourResponse = await fetch(`https://boardgamearena.com/tournament?id=${tournamentId}`);
                const tourHtml = await tourResponse.text();
                
                // Extract tournament details from fetched HTML (like bookmarklet does)
                // Parse the HTML to get original timestamps
                const parser = new DOMParser();
                const tourDoc = parser.parseFromString(tourHtml, 'text/html');
                
                const tournamentName = tourDoc.querySelector("div.tournaments-presentation__title-tournament")?.innerText || "Unknown";
                const gameName = tourDoc.querySelector("div.tournaments-presentation__title-game > a")?.innerText || "Unknown";
                
                // Get start date from the parsed HTML (before JavaScript converts it)
                const startDateEl = tourDoc.querySelector("div.tournaments-presentation__subtitle-value > div.localDate");
                let startTime = "";
                if (startDateEl) {
                    const timestamp = startDateEl.innerText.trim();
                    const timestampNum = Number(timestamp);
                    if (!isNaN(timestampNum) && timestampNum > 0) {
                        startTime = new Date(timestampNum * 1000).toLocaleString();
                    }
                }
                
                const playerCount = tourDoc.querySelector("div.tournaments-presentation__subtitle-block-players > div > b")?.innerText || "0";
                
                // Get rounds and round limit from options (from parsed HTML)
                const dataRows = tourDoc.querySelectorAll("div.tournaments-option");
                let rounds = "0";
                let roundLimit = "0";
                let endTime = "";
                
                if (dataRows.length > 7) {
                    const roundsText = dataRows[6]?.innerText || "";
                    const roundsMatch = roundsText.match(/(\\d+)/);
                    rounds = roundsMatch ? roundsMatch[1] : "0";
                    
                    const roundLimitText = dataRows[7]?.innerText || "";
                    const roundLimitMatch = roundLimitText.match(/(\\d+)/);
                    roundLimit = roundLimitMatch ? roundLimitMatch[1] : "0";
                }
                
                // Get all matches
                const matches = document.querySelectorAll("div.v2tournament__encounter");
                const matchData = [];
                
                console.log('Found matches:', matches.length);
                
                for (const match of matches) {
                    if (match.classList.contains("v2tournament__encounter--status-skipped")) {
                        continue;
                    }
                    
                    const titleEl = match.querySelector("a.v2tournament__encounter-title");
                    if (!titleEl) continue;
                    
                    const tableIdMatch = titleEl.getAttribute("href")?.match(/table=(\\d+)/);
                    if (!tableIdMatch) {
                        console.log('No table ID found in match');
                        continue;
                    }
                    
                    const tableId = tableIdMatch[1];
                    console.log('Processing table:', tableId);
                    
                    try {
                        const tableResponse = await fetch(
                            `https://boardgamearena.com/table/table/tableinfos.html?id=${tableId}`,
                            { headers }
                        );
                        const tableInfo = await tableResponse.json();
                        
                        // Only process archived (finished) matches
                        if (tableInfo.data.status !== "archive") {
                            console.log('Skipping non-archived match:', tableId);
                            continue;
                        }
                        
                        const endReason = tableInfo.data.result.endgame_reason;
                        const isTimeout = endReason === "abandon_by_tournamenttimeout";
                        const timeLimit = tableInfo.data.options["204"]?.value || 0;
                        const progress = isTimeout ? tableInfo.data.progression : 100;
                        
                        // Track latest match end time
                        const matchEndTime = new Date(tableInfo.data.result.time_end);
                        if (!endTime || matchEndTime > new Date(endTime)) {
                            endTime = matchEndTime.toLocaleString();
                        }
                        
                        const players = match.querySelectorAll("div.v2tournament__encounter-player");
                        const playerData = [];
                        
                        for (const playerEl of players) {
                            const playerId = playerEl.getAttribute("data-tournament-player-id");
                            const playerNameEl = playerEl.querySelector("a.playername");
                            const playerName = playerNameEl?.textContent?.trim() || "Unknown";
                            const reflexionTime = tableInfo.data.result.stats.player.reflexion_time.values[playerId] || 0;
                            const remainingTime = timeLimit - reflexionTime;
                            const pointsEl = playerEl.querySelector("div.v2tournament__encounter-player-points");
                            const points = pointsEl ? Number(pointsEl.textContent) : 0;
                            
                            playerData.push({
                                name: playerName,
                                remainingTime: remainingTime,
                                points: points
                            });
                        }
                        
                        matchData.push({
                            tableId: tableId,
                            isTimeout: isTimeout,
                            progress: progress,
                            players: playerData
                        });
                        
                    } catch (error) {
                        console.error(`Error fetching table ${tableId}:`, error);
                    }
                }
                
                // Count stats
                const totalMatches = matchData.length;
                const timeoutMatches = matchData.filter(m => m.isTimeout).length;
                // Use playerCount from DOM (already extracted above)
                
                // Format as TSV (matches TournamentStats.js bookmarklet format)
                // Summary row: tournament_id, name, empty column (double tab), game, times, counts
                let tsv = `${tournamentId}\\t${tournamentName}\\t\\t${gameName}\\t${startTime}\\t${endTime}\\t${rounds}\\t${roundLimit}\\t${totalMatches}\\t${timeoutMatches}\\t${playerCount}\\n`;
                
                // Match rows: tournament_id, table_id, is_timeout, progress, player_name, remaining_time, points
                matchData.forEach(match => {
                    match.players.forEach(player => {
                        tsv += `${tournamentId}\\t${match.tableId}\\t${match.isTimeout ? 1 : 0}\\t${match.progress}\\t${player.name}\\t${player.remainingTime}\\t${player.points}\\n`;
                    });
                });
                
                // Debug output
                console.log('Matches processed:', matchData.length, '| Start:', startTime || 'MISSING', '| End:', endTime || 'MISSING');
                
                return tsv;
            }
        """)
        
        if tsv_data:
            print(f"  Tournament {tournament_id}: Generated {len(tsv_data)} chars of TSV data")
            # Print first 200 chars to see the structure
            print(f"  Preview: {tsv_data[:200]}")
        else:
            print(f"  Tournament {tournament_id}: No TSV data generated")
        
        return tsv_data
