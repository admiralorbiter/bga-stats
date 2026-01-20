"""
BGA Pull Game List - Extract complete game catalog from BGA using Playwright.
Mirrors the functionality of the GameList.js bookmarklet.
"""

import json
from typing import Optional
from playwright.sync_api import BrowserContext, Page
from backend.services.bga_pull_base import BGAPullBase, RateLimiter


class BGAGameListPuller(BGAPullBase):
    """Pull complete game catalog from BGA."""
    
    def __init__(self, context: BrowserContext, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(context, rate_limiter)
    
    def pull_game_list(self) -> Optional[str]:
        """
        Pull complete game list from BGA.
        Returns data in TSV format compatible with the existing parser.
        
        Mirrors the GameList.js bookmarklet logic:
        1. Fetch https://boardgamearena.com/gamelist?allGames=
        2. Extract HTML content
        3. Parse JSON between '"game_list"' and '"game_tags"'
        4. Convert to TSV format: ID\tNAME\tDISPLAY_NAME\tSTATUS\tPREMIUM
        5. Convert status "private" -> "alpha"
        6. Convert premium to 0 or 1
        
        Returns:
            TSV-formatted string or None on failure
        """
        page = self.create_page()
        
        try:
            url = 'https://boardgamearena.com/gamelist?allGames='
            
            if not self.safe_navigate(page, url):
                print("Failed to navigate to game list page")
                return None
            
            # Wait a moment for page to fully load
            try:
                page.wait_for_load_state('networkidle', timeout=10000)
            except:
                # Continue anyway, the data might already be in the HTML
                pass
            
            # Extract HTML content
            html_str = page.content()
            
            # Parse JSON substring (same logic as bookmarklet)
            start = html_str.find('"game_list"') + 12
            end = html_str.find('"game_tags"') - 1
            
            if start < 12 or end < 0:
                print("Could not find game_list JSON in page content")
                return None
            
            json_str = html_str[start:end]
            
            # Parse JSON array
            try:
                games = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Failed to parse game list JSON: {e}")
                return None
            
            if not games or not isinstance(games, list):
                print("Game list is empty or not a list")
                return None
            
            # Convert to TSV format
            rows = []
            
            for game in games:
                try:
                    # Extract fields with defaults
                    game_id = game.get('id', '')
                    name = game.get('name', '')
                    display_name = game.get('display_name_en', game.get('display_name', ''))
                    status = game.get('status', 'published')
                    premium = game.get('premium', False)
                    
                    # Convert status values to match our schema
                    # "private" -> "alpha" (bookmarklet logic)
                    # "public" -> "published" (BGA API returns this)
                    if status == 'private':
                        status = 'alpha'
                    elif status == 'public':
                        status = 'published'
                    
                    # Convert premium to 0 or 1
                    premium_flag = 1 if premium else 0
                    
                    # Skip if essential fields are missing
                    if not game_id or not name:
                        continue
                    
                    # Build TSV row
                    row = f"{game_id}\t{name}\t{display_name}\t{status}\t{premium_flag}"
                    rows.append(row)
                    
                except Exception as e:
                    print(f"Failed to process game: {e}")
                    continue
            
            if not rows:
                print("No valid games extracted")
                return None
            
            print(f"Successfully extracted {len(rows)} games")
            return '\n'.join(rows)
            
        except Exception as e:
            print(f"Failed to pull game list: {e}")
            return None
        finally:
            page.close()
