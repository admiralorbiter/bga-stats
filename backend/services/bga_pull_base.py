"""
BGA Pull Base - Shared utilities for pulling data from BGA.
Provides rate limiting, retries, and common browser helpers.
"""

import time
from typing import Optional
from playwright.sync_api import Page, BrowserContext


class RateLimiter:
    """Simple rate limiter to avoid overwhelming BGA servers."""
    
    def __init__(self, min_delay_seconds=1.0):
        """
        Initialize rate limiter.
        
        Args:
            min_delay_seconds: Minimum delay between requests
        """
        self.min_delay = min_delay_seconds
        self.last_request_time = 0
    
    def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class BGAPullBase:
    """Base class for BGA data pulling services."""
    
    def __init__(self, context: BrowserContext, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize pull service.
        
        Args:
            context: Authenticated Playwright browser context
            rate_limiter: Optional rate limiter instance
        """
        self.context = context
        self.rate_limiter = rate_limiter or RateLimiter(min_delay_seconds=1.0)
    
    def create_page(self) -> Page:
        """Create a new page with common settings."""
        page = self.context.new_page()
        
        # Set a reasonable timeout
        page.set_default_timeout(30000)  # 30 seconds
        
        return page
    
    def safe_navigate(self, page: Page, url: str, wait_for: Optional[str] = None) -> bool:
        """
        Safely navigate to a URL with rate limiting.
        
        Args:
            page: Playwright page
            url: URL to navigate to
            wait_for: Optional selector to wait for after navigation
        
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            self.rate_limiter.wait()
            
            response = page.goto(url, wait_until='domcontentloaded')
            
            if response and response.status >= 400:
                print(f"HTTP {response.status} for {url}")
                return False
            
            if wait_for:
                page.wait_for_selector(wait_for, timeout=10000)
            
            return True
            
        except Exception as e:
            print(f"Navigation failed for {url}: {e}")
            return False
    
    def extract_text_safe(self, page: Page, selector: str, default: str = "") -> str:
        """
        Safely extract text from an element.
        
        Args:
            page: Playwright page
            selector: CSS selector
            default: Default value if element not found
        
        Returns:
            Extracted text or default
        """
        try:
            element = page.query_selector(selector)
            if element:
                return element.inner_text().strip()
            return default
        except Exception as e:
            print(f"Failed to extract text from {selector}: {e}")
            return default
    
    def extract_attribute_safe(self, page: Page, selector: str, attribute: str, default: str = "") -> str:
        """
        Safely extract an attribute from an element.
        
        Args:
            page: Playwright page
            selector: CSS selector
            attribute: Attribute name
            default: Default value if element not found
        
        Returns:
            Extracted attribute or default
        """
        try:
            element = page.query_selector(selector)
            if element:
                value = element.get_attribute(attribute)
                return value if value else default
            return default
        except Exception as e:
            print(f"Failed to extract attribute {attribute} from {selector}: {e}")
            return default
    
    def get_bga_request_token(self, page: Page) -> Optional[str]:
        """
        Extract BGA request token from page content.
        Some API endpoints require this token.
        
        Args:
            page: Playwright page
        
        Returns:
            Request token or None
        """
        try:
            # Navigate to main page if needed
            content = page.content()
            
            # Look for requestToken in the HTML
            import re
            match = re.search(r"requestToken:\s+'([^']+)'", content)
            if match:
                return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"Failed to extract request token: {e}")
            return None
