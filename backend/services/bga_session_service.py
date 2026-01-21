"""
BGA Session Service - Manages Playwright browser sessions for BGA authentication.
Handles login, session persistence, and session validation.
"""

import os
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

# Session state file location (local to the app)
SESSION_STATE_DIR = Path(__file__).parent.parent.parent / '.bga_session'
SESSION_STATE_FILE = SESSION_STATE_DIR / 'session_state.json'
PLAYER_INFO_FILE = SESSION_STATE_DIR / 'player_info.json'


class BGASessionService:
    """
    Manages BGA authentication sessions using Playwright.
    Supports headless and headed browser modes for login.
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        
    def ensure_session_dir(self):
        """Ensure session directory exists."""
        SESSION_STATE_DIR.mkdir(exist_ok=True)
    
    def has_saved_session(self):
        """Check if a saved session exists."""
        return SESSION_STATE_FILE.exists()
    
    def get_session_info(self):
        """Get information about the current session."""
        if not self.has_saved_session():
            return None
        
        try:
            with open(SESSION_STATE_FILE, 'r') as f:
                state = json.load(f)
                # Check if we have cookies
                if 'cookies' in state and len(state['cookies']) > 0:
                    info = {
                        'exists': True,
                        'cookie_count': len(state['cookies']),
                        'file_path': str(SESSION_STATE_FILE)
                    }
                    
                    # Add player info if available
                    player_info = self._load_player_info()
                    if player_info:
                        info.update(player_info)
                    
                    return info
        except Exception as e:
            return None
        
        return None
    
    def clear_session(self):
        """Delete saved session state."""
        if SESSION_STATE_FILE.exists():
            SESSION_STATE_FILE.unlink()
            return True
        return False
    
    def create_browser(self, headless=False):
        """
        Create a Playwright browser instance.
        
        Args:
            headless: If True, run in headless mode. If False, show browser window.
        
        Returns:
            Browser instance
        """
        if not self.playwright:
            self.playwright = sync_playwright().start()
        
        self.browser = self.playwright.chromium.launch(headless=headless)
        return self.browser
    
    def create_context_from_saved_session(self):
        """
        Create a browser context from saved session state.
        
        Returns:
            BrowserContext or None if no saved session
        """
        if not self.has_saved_session():
            return None
        
        if not self.browser:
            self.create_browser(headless=True)
        
        try:
            self.context = self.browser.new_context(
                storage_state=str(SESSION_STATE_FILE)
            )
            return self.context
        except Exception as e:
            print(f"Failed to load session: {e}")
            return None
    
    def save_session(self, context):
        """
        Save browser context session state to file.
        
        Args:
            context: BrowserContext to save
        """
        self.ensure_session_dir()
        context.storage_state(path=str(SESSION_STATE_FILE))
    
    def initiate_login(self, callback_url=None):
        """
        Open a browser window for the user to log in to BGA.
        Returns when login is detected or window is closed.
        
        Args:
            callback_url: Optional callback URL to notify when login is complete
        
        Returns:
            dict with success status and message
        """
        browser = None
        context = None
        page = None
        
        try:
            print("Starting login process...")
            
            # Create browser in headed mode (visible to user)
            browser = self.create_browser(headless=False)
            print("Browser created")
            
            context = browser.new_context()
            page = context.new_page()
            print("Navigating to BGA...")
            
            # Navigate to BGA
            page.goto('https://boardgamearena.com', timeout=30000)
            print("Page loaded, checking if already logged in...")
            
            # First check if already logged in
            try:
                # Quick check for logged-in indicators
                page.wait_for_selector('a[href*="/player?id="]', timeout=3000)
                print("Already logged in! Saving session...")
                # Skip the login wait - already logged in
                self.save_session(context)
                print("Session saved")
                
                # Try to extract player ID from the page
                player_id = self._extract_player_id(page)
                print(f"Extracted player ID: {player_id}")
                
                # Save player ID alongside session
                if player_id:
                    self._save_player_info({'player_id': player_id})
                
                page.close()
                context.close()
                browser.close()
                
                return {
                    'success': True,
                    'message': 'Already logged in. Session saved.',
                    'player_id': player_id
                }
            except:
                print("Not logged in yet, waiting for login...")
            
            # Wait for user to log in (check for player menu or similar)
            # We'll wait for either login completion or page close
            try:
                # Wait up to 5 minutes for login
                # Look for elements that only appear when logged in
                # Try multiple selectors as fallback
                print("Checking for login indicators...")
                
                # Try different selectors that indicate logged-in state
                selectors_to_try = [
                    '#player_panel',  # Player panel in header
                    'a[href*="/player?id="]',  # Player profile link
                    '.bgabutton_red',  # Logout button
                    '#avatar_active',  # Active avatar
                    'div.main_player_area',  # Main player area
                ]
                
                login_detected = False
                for selector in selectors_to_try:
                    try:
                        print(f"Trying selector: {selector}")
                        page.wait_for_selector(selector, timeout=10000)
                        print(f"Found login indicator: {selector}")
                        login_detected = True
                        break
                    except:
                        continue
                
                if not login_detected:
                    # If none of the specific selectors work, just wait for any indication
                    # Check if URL changed from login page
                    print("Checking URL and page state...")
                    current_url = page.url
                    # If we're not on the login page and the page has loaded, assume login success
                    if 'boardgamearena.com' in current_url and 'account/account/login' not in current_url:
                        print("Appears to be logged in (no login page detected)")
                        login_detected = True
                
                if not login_detected:
                    raise Exception("Could not detect login state")
                
                print("Login detected!")
                
                # Give it a moment to fully load
                page.wait_for_timeout(2000)
                
                # Login successful - save session
                self.save_session(context)
                print("Session saved")
                
                # Try to extract player ID from the page
                player_id = self._extract_player_id(page)
                print(f"Extracted player ID: {player_id}")
                
                # Save player ID alongside session
                if player_id:
                    self._save_player_info({'player_id': player_id})
                
                page.close()
                context.close()
                browser.close()
                
                return {
                    'success': True,
                    'message': 'Login successful. Session saved.',
                    'player_id': player_id
                }
                
            except Exception as e:
                # Timeout or error
                error_type = type(e).__name__
                error_msg = str(e)
                print(f"Login failed: {error_type} - {error_msg}")
                
                if page and not page.is_closed():
                    page.close()
                if context:
                    context.close()
                if browser:
                    browser.close()
                
                # Provide more specific error messages
                if "Timeout" in error_type:
                    return {
                        'success': False,
                        'message': 'Login timeout: You have 5 minutes to complete login. The browser window may have closed before you finished logging in.'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Login failed: {error_msg}'
                    }
                
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to initiate login: {error_msg}")
            
            # Clean up
            if page and not page.is_closed():
                page.close()
            if context:
                context.close()
            if browser:
                browser.close()
            
            return {
                'success': False,
                'message': f'Failed to open browser: {error_msg}'
            }
        finally:
            if self.playwright:
                try:
                    self.playwright.stop()
                except:
                    pass
                self.playwright = None
    
    def validate_session(self):
        """
        Validate that the saved session is still valid by making a test request.
        
        Returns:
            bool: True if session is valid, False otherwise
        """
        if not self.has_saved_session():
            return False
        
        try:
            browser = self.create_browser(headless=True)
            context = self.create_context_from_saved_session()
            
            if not context:
                browser.close()
                return False
            
            page = context.new_page()
            page.goto('https://boardgamearena.com')
            
            # Check if we're logged in (look for player menu)
            try:
                page.wait_for_selector('#menu_option_playernotif', timeout=5000)
                is_valid = True
            except:
                is_valid = False
            
            page.close()
            context.close()
            browser.close()
            
            return is_valid
            
        except Exception as e:
            print(f"Session validation failed: {e}")
            return False
        finally:
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
    
    def cleanup(self):
        """Clean up browser resources."""
        # Playwright objects are not thread-safe; ensure we always tear them down
        # between requests and never raise during cleanup (best-effort).
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
    
    def _extract_player_id(self, page):
        """
        Extract the logged-in player's ID from the BGA page.
        
        Args:
            page: Playwright page object
        
        Returns:
            str: Player ID or None
        """
        try:
            # Try to find player profile link
            player_link = page.query_selector('a[href*="/player?id="]')
            if player_link:
                href = player_link.get_attribute('href')
                import re
                match = re.search(r'id=(\d+)', href)
                if match:
                    return match.group(1)
            
            # Alternative: check if there's a player ID in the page data
            content = page.content()
            match = re.search(r'"player_id["\s:]+(\d+)', content)
            if match:
                return match.group(1)
                
        except Exception as e:
            print(f"Failed to extract player ID: {e}")
        
        return None
    
    def _save_player_info(self, player_info):
        """Save player information to file."""
        self.ensure_session_dir()
        try:
            with open(PLAYER_INFO_FILE, 'w') as f:
                json.dump(player_info, f)
        except Exception as e:
            print(f"Failed to save player info: {e}")
    
    def _load_player_info(self):
        """Load player information from file."""
        if not PLAYER_INFO_FILE.exists():
            return None
        
        try:
            with open(PLAYER_INFO_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load player info: {e}")
            return None


# Singleton instance
_session_service = None

def get_session_service():
    """Get or create the global session service instance."""
    global _session_service
    if _session_service is None:
        _session_service = BGASessionService()
    return _session_service
