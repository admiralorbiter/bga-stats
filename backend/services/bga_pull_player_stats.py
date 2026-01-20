"""
BGA Pull Player Stats - Extract player statistics from BGA using Playwright.
Mirrors the functionality of the PlayerStats.js bookmarklet.
"""

import re
from typing import List, Dict, Optional
from playwright.sync_api import BrowserContext, Page
from backend.services.bga_pull_base import BGAPullBase, RateLimiter


class BGAPlayerStatsPuller(BGAPullBase):
    """Pull player statistics from BGA."""
    
    def __init__(self, context: BrowserContext, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(context, rate_limiter)
    
    def pull_group_members(self, group_id: str) -> List[Dict[str, str]]:
        """
        Get list of members from a BGA group.
        
        Args:
            group_id: BGA group ID
        
        Returns:
            List of dicts with 'name' and 'id' keys
        """
        page = self.create_page()
        members = []
        
        try:
            url = f'https://boardgamearena.com/group?id={group_id}'
            
            if not self.safe_navigate(page, url, wait_for='.list_of_players'):
                return members
            
            # Extract member list
            member_elements = page.query_selector_all('.list_of_players .player_in_list a.playername')
            
            for element in member_elements:
                name = element.inner_text().strip()
                href = element.get_attribute('href')
                
                if href:
                    player_id_match = re.search(r'id=(\d+)', href)
                    if player_id_match:
                        members.append({
                            'name': name,
                            'id': player_id_match.group(1)
                        })
            
            return members
            
        except Exception as e:
            print(f"Failed to pull group members for {group_id}: {e}")
            return members
        finally:
            page.close()
    
    def pull_player_stats(self, player_id: str) -> Optional[str]:
        """
        Pull statistics for a single player.
        Returns data in TSV format compatible with the existing parser.
        
        Args:
            player_id: BGA player ID
        
        Returns:
            TSV-formatted string or None on failure
        """
        page = self.create_page()
        
        try:
            url = f'https://boardgamearena.com/player?id={player_id}'
            
            if not self.safe_navigate(page, url):
                return None
            
            # Wait for key elements to load
            try:
                page.wait_for_selector('#player_name', timeout=10000)
            except:
                print(f"Player page did not load properly for ID {player_id}")
                return None
            
            # Extract player name
            player_name = self.extract_text_safe(page, '#player_name', 'Unknown')
            
            # Extract XP
            xp_text = self.extract_text_safe(page, '#pageheader_prestige', '0')
            xp_text = xp_text.replace('k', '000').replace(' XP', '').strip()
            try:
                xp = int(xp_text)
            except:
                xp = 0
            
            # Extract karma
            karma_text = self.extract_text_safe(page, '.progressbar_label .value', '0')
            karma_text = karma_text.replace('%', '').strip()
            try:
                karma = int(karma_text)
            except:
                karma = 0
            
            # Extract penalties (abandoned, timeout, recent matches)
            penalties_text = self.extract_text_safe(page, '#pagesection_reputation .row-value', '')
            penalties = re.findall(r'(\d+)', penalties_text)
            
            abandoned = int(penalties[0]) if len(penalties) > 0 else 0
            timeout = int(penalties[1]) if len(penalties) > 1 else 0
            recent_matches = int(penalties[2]) if len(penalties) > 2 else 0
            
            # Extract last seen days
            last_seen_text = self.extract_text_safe(page, '#last_seen', '')
            last_seen_days = self._parse_last_seen(last_seen_text)
            
            # Extract per-game stats
            game_divs = page.query_selector_all('#pagesection_prestige .row .palmares_game')
            
            game_stats = []
            matches_total = 0
            wins_total = 0
            
            for game_div in game_divs:
                try:
                    game_name_elem = game_div.query_selector('.gamename')
                    if not game_name_elem:
                        continue
                    
                    game_name = game_name_elem.inner_text().strip()
                    
                    # Extract played/won from palmares_details
                    details_elem = game_div.query_selector('.palmares_details')
                    if not details_elem:
                        continue
                    
                    details = details_elem.inner_text()
                    numbers = re.findall(r'(\d+[\s0-9]*)', details)
                    
                    played = 0
                    if len(numbers) > 0:
                        played = int(numbers[0].replace(' ', ''))
                    
                    # If 4 numbers, it's "X normal + Y arena = Z total" format
                    if len(numbers) == 4:
                        played += int(numbers[1].replace(' ', ''))
                    
                    # Won is the second-to-last number
                    won = 0
                    if len(numbers) >= 2:
                        won = int(numbers[-2].replace(' ', ''))
                    
                    matches_total += played
                    wins_total += won
                    
                    # Extract ELO
                    elo_elem = game_div.query_selector('.gamerank_value')
                    elo = elo_elem.inner_text().strip() if elo_elem else 'N/A'
                    
                    # Extract rank
                    rank = ''
                    rank_elem = game_div.query_selector('.gamerank_no')
                    if rank_elem:
                        rank_text = rank_elem.inner_text()
                        rank_match = re.search(r'(\d+)', rank_text)
                        if rank_match:
                            rank = rank_match.group(1)
                    
                    game_stats.append({
                        'game_name': game_name,
                        'elo': elo,
                        'rank': rank,
                        'played': played,
                        'won': won
                    })
                    
                except Exception as e:
                    print(f"Failed to parse game stat: {e}")
                    continue
            
            # Build TSV output (same format as bookmarklet)
            output_lines = []
            
            # XP row
            output_lines.append(f"{player_name}\t{player_id}\tXP\t{xp}\t{karma}\t{matches_total}\t{wins_total}")
            
            # Recent games row
            output_lines.append(f"{player_name}\t{player_id}\tRecent games\t{abandoned}\t{timeout}\t{recent_matches}\t{last_seen_days}")
            
            # Per-game rows
            for stat in game_stats:
                output_lines.append(
                    f"{player_name}\t{player_id}\t{stat['game_name']}\t{stat['elo']}\t{stat['rank']}\t{stat['played']}\t{stat['won']}"
                )
            
            return '\n'.join(output_lines)
            
        except Exception as e:
            print(f"Failed to pull stats for player {player_id}: {e}")
            return None
        finally:
            page.close()
    
    def pull_multiple_players(self, player_ids: List[str], progress_callback=None) -> str:
        """
        Pull stats for multiple players and combine into single TSV.
        
        Args:
            player_ids: List of player IDs
            progress_callback: Optional callback(current, total) for progress updates
        
        Returns:
            Combined TSV string
        """
        all_stats = []
        total = len(player_ids)
        
        for i, player_id in enumerate(player_ids, 1):
            if progress_callback:
                progress_callback(i, total)
            
            stats = self.pull_player_stats(player_id)
            if stats:
                all_stats.append(stats)
        
        return '\n'.join(all_stats)
    
    def _parse_last_seen(self, last_seen_str: str) -> int:
        """
        Parse last seen string into days.
        Mirrors the logic from PlayerStats.js bookmarklet.
        
        Args:
            last_seen_str: Last seen text from BGA
        
        Returns:
            Days since last seen
        """
        if not last_seen_str or last_seen_str == "{LAST_SEEN}":
            return 0
        
        # Match number and time unit
        match = re.search(r'(\d+|NaN)?\s*(.*)', last_seen_str)
        if not match:
            return 0
        
        number_str = match.group(1)
        time_unit = match.group(2)
        
        if number_str == "NaN" or not number_str:
            # Check if it's "moments ago" type
            if re.search(r'(mn|h|seconds|perc|óra|néhány pillanattal) (ezelőtt|ago)', time_unit):
                return 0
            return 1  # Default to 1 day
        
        try:
            days = int(number_str)
        except:
            return 0
        
        # Convert to days based on unit
        if re.search(r'év|year', time_unit):
            days *= 365
        elif re.search(r'hónap|month', time_unit):
            days *= 30
        elif re.search(r'(mn|h|seconds|perc|óra|néhány pillanattal) (ezelőtt|ago)', time_unit):
            days = 0
        
        return days


def parse_player_ids_input(ids_input: str) -> tuple[Optional[str], List[str]]:
    """
    Parse the player IDs input string.
    Supports:
    - Comma-separated player IDs: "12345,67890"
    - Group ID: "group:123" or "g:123"
    
    Args:
        ids_input: Input string
    
    Returns:
        Tuple of (group_id or None, list of player IDs)
    """
    ids_input = ids_input.strip()
    
    # Check for group ID format
    group_match = re.match(r'(?:group|g):(\d+)', ids_input, re.IGNORECASE)
    if group_match:
        return (group_match.group(1), [])
    
    # Parse as comma-separated player IDs
    player_ids = [pid.strip() for pid in ids_input.split(',') if pid.strip()]
    
    # Validate they're all numeric
    player_ids = [pid for pid in player_ids if pid.isdigit()]
    
    return (None, player_ids)
