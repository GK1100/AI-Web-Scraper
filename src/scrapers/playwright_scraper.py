"""
Step 6: Playwright Scraper
Handles JavaScript-heavy websites using Playwright
"""

from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup
import time

from logger import setup_logger, log_step
from heuristic_extractor import HeuristicExtractor
from dom_analyzer import DOMAnalyzer
from universal_extractor import UniversalExtractor
from debug_logger import get_debug_logger

logger = setup_logger(__name__)


class PlaywrightScraper:
    """
    Scrapes JavaScript-heavy websites using Playwright
    Handles dynamic content, pagination, and scrolling
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize Playwright scraper
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.extractor = HeuristicExtractor()
        self.dom_analyzer = DOMAnalyzer()
        self.universal_extractor = UniversalExtractor()
        
        logger.info(f"PlaywrightScraper initialized (headless={headless}, timeout={timeout}ms)")
        log_step(logger, "Playwright Scraper", "INITIALIZED", {
            "headless": headless,
            "timeout": timeout
        })
    
    def capture_screenshot(self, url: str, output_path: str = "screenshot.png") -> str:
        """
        Capture screenshot of page for vision AI analysis
        
        Args:
            url: URL to capture
            output_path: Path to save screenshot
        
        Returns:
            Path to saved screenshot
        """
        logger.info(f"📸 Capturing screenshot of {url}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                page.set_viewport_size({"width": 1920, "height": 1080})
                
                logger.info(f"📄 Navigating to: {url}")
                page.goto(url, wait_until='networkidle', timeout=self.timeout)
                
                logger.info(f"⏳ Waiting for content to render...")
                page.wait_for_timeout(2000)
                
                logger.info(f"💾 Saving screenshot to: {output_path}")
                page.screenshot(path=output_path, full_page=False)  # Viewport only
                
                browser.close()
                logger.info(f"✅ Screenshot saved successfully")
                
                return output_path
                
        except Exception as e:
            logger.error(f"❌ Screenshot capture failed: {e}")
            return ""
    
    def scrape(
        self,
        url: str,
        content_type: str,
        fields: List[str],
        quantity: int = 10,
        selectors: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Scrape website using Playwright
        
        Args:
            url: Target website URL
            content_type: Type of content (products, articles, reviews)
            fields: Fields to extract
            quantity: Number of items to extract
            selectors: Optional CSS selectors (if None, use heuristics)
        
        Returns:
            List of extracted items
        """
        log_step(logger, "Playwright Scraping", "STARTED", {
            "url": url,
            "content_type": content_type,
            "fields": fields,
            "quantity": quantity,
            "has_selectors": selectors is not None
        })
        
        try:
            with sync_playwright() as p:
                # Launch browser
                logger.info("🌐 Launching Chromium browser...")
                browser = p.chromium.launch(headless=self.headless)
                
                # Create context with realistic settings
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                # Create page
                page = context.new_page()
                page.set_default_timeout(self.timeout)
                
                logger.info(f"📄 Navigating to: {url}")
                
                # Navigate to URL
                page.goto(url, wait_until='networkidle')
                logger.info("✅ Page loaded successfully")
                
                # Wait for content to load
                time.sleep(2)  # Give JS time to render
                logger.info("⏳ Waited for JavaScript to render")
                
                # Scroll to load lazy content
                self._scroll_page(page)
                
                # Get HTML content
                html = page.content()
                logger.info(f"📝 Retrieved HTML: {len(html)} characters")
                
                # Close browser
                browser.close()
                logger.info("🔒 Browser closed")
                
                # Initialize variables
                items = []
                extraction_method = "unknown"
                
                # Extract data using heuristics or selectors
                if selectors:
                    logger.info("🎯 Using provided selectors for extraction")
                    items = self._extract_with_selectors(html, selectors, quantity)
                    extraction_method = "provided_selectors"
                    
                    # If selectors failed, fall back to automatic extraction
                    if not items or len(items) == 0:
                        logger.warning("⚠️ Provided selectors found 0 items, falling back to automatic extraction")
                        selectors = None  # Clear selectors to trigger fallback
                
                if not selectors or not items:
                    logger.info("🔍 Trying DOM analyzer first...")
                    selectors_dict, items = self.dom_analyzer.analyze_and_extract(
                        html, content_type, fields, quantity
                    )
                    extraction_method = "dom_analyzer"
                    
                    if items and len(items) >= quantity * 0.5:  # Got at least 50% of requested
                        logger.info(f"✅ DOM analyzer extracted {len(items)} items")
                    else:
                        logger.info("🔍 DOM analyzer insufficient, trying heuristics...")
                        items = self.extractor.extract(html, content_type, fields, quantity)
                        extraction_method = "heuristic"
                        
                        if not items or len(items) < quantity * 0.3:  # Less than 30%
                            logger.info("🌐 Heuristics insufficient, trying universal extractor...")
                            items = self.universal_extractor.extract(html, content_type, fields, quantity)
                            extraction_method = "universal"
                            
                            if not items or len(items) < quantity * 0.3:  # Still insufficient
                                logger.info("🤖 Trying LLM extraction as last resort...")
                                try:
                                    from llm_extractor import LLMExtractor
                                    llm_extractor = LLMExtractor()
                                    items = llm_extractor.extract(html, content_type, fields, quantity)
                                    extraction_method = "llm"
                                    
                                    if items:
                                        logger.info(f"✅ LLM extracted {len(items)} items")
                                    else:
                                        logger.warning("⚠️ All extraction methods failed")
                                        extraction_method = "failed"
                                except Exception as e:
                                    logger.warning(f"LLM extraction failed: {e}")
                                    extraction_method = "failed"
                            elif items:
                                logger.info(f"✅ Universal extractor found {len(items)} items")
                
                # Log debug information
                debug_logger = get_debug_logger()
                debug_file = debug_logger.log_scrape_attempt(
                    url=url,
                    html=html,
                    selectors=selectors or selectors_dict if 'selectors_dict' in locals() else None,
                    items_found=len(items),
                    extraction_method=extraction_method
                )
                logger.info(f"💾 Debug info saved to: {debug_file}")
                
                log_step(logger, "Playwright Scraping", "SUCCESS", {
                    "items_extracted": len(items),
                    "url": url
                })
                
                return items
        
        except Exception as e:
            log_step(logger, "Playwright Scraping", "FAILED", {
                "error": str(e),
                "url": url
            })
            logger.exception("Playwright scraping failed")
            return []
    
    def _scroll_page(self, page: Page, scrolls: int = 3):
        """
        Scroll page to load lazy content
        
        Args:
            page: Playwright page object
            scrolls: Number of times to scroll
        """
        logger.info(f"📜 Scrolling page {scrolls} times to load lazy content...")
        
        for i in range(scrolls):
            # Scroll to bottom
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1)  # Wait for content to load
            logger.debug(f"   Scroll {i+1}/{scrolls} completed")
        
        # Scroll back to top
        page.evaluate('window.scrollTo(0, 0)')
        logger.info("✅ Scrolling completed")
    
    def _extract_with_selectors(
        self,
        html: str,
        selectors: Dict,
        quantity: int
    ) -> List[Dict]:
        """
        Extract data using provided CSS selectors
        
        Args:
            html: HTML content
            selectors: Dict with 'container' and field selectors
            quantity: Number of items to extract
        
        Returns:
            List of extracted items
        """
        logger.info("🎯 Extracting with CSS selectors...")
        
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        # Get container selector
        container_selector = selectors.get('container', 'div')
        field_selectors = selectors.get('selectors', {})
        
        logger.info(f"   Container: {container_selector}")
        logger.info(f"   Fields: {list(field_selectors.keys())}")
        
        # Find all containers
        containers = soup.select(container_selector)
        logger.info(f"   Found {len(containers)} containers")
        
        for i, container in enumerate(containers[:quantity]):
            item = {}
            
            # Extract each field
            for field, selector in field_selectors.items():
                try:
                    # Handle ::text and ::attr() pseudo-selectors
                    if '::text' in selector:
                        css_selector = selector.replace('::text', '')
                        element = container.select_one(css_selector)
                        if element:
                            item[field] = element.get_text().strip()
                    
                    elif '::attr(' in selector:
                        # Extract attribute
                        css_selector, attr = selector.split('::attr(')
                        attr = attr.rstrip(')')
                        element = container.select_one(css_selector)
                        if element:
                            item[field] = element.get(attr, '')
                    
                    else:
                        # Regular selector
                        element = container.select_one(selector)
                        if element:
                            item[field] = element.get_text().strip()
                
                except Exception as e:
                    logger.debug(f"   Failed to extract {field}: {e}")
            
            if item:
                items.append(item)
                logger.info(f"✅ Extracted item {len(items)}")
        
        logger.info(f"🎯 Extracted {len(items)} items with selectors")
        return items
    
    def scrape_with_pagination(
        self,
        url: str,
        content_type: str,
        fields: List[str],
        quantity: int = 10,
        max_pages: int = 5
    ) -> List[Dict]:
        """
        Scrape multiple pages with pagination
        
        Args:
            url: Target website URL
            content_type: Type of content
            fields: Fields to extract
            quantity: Total items to extract
            max_pages: Maximum pages to scrape
        
        Returns:
            List of extracted items from all pages
        """
        log_step(logger, "Paginated Scraping", "STARTED", {
            "url": url,
            "quantity": quantity,
            "max_pages": max_pages
        })
        
        all_items = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                page.set_default_timeout(self.timeout)
                
                logger.info(f"📄 Starting pagination from: {url}")
                page.goto(url, wait_until='networkidle')
                
                for page_num in range(1, max_pages + 1):
                    logger.info(f"📄 Scraping page {page_num}/{max_pages}")
                    
                    # Wait and scroll
                    time.sleep(2)
                    self._scroll_page(page, scrolls=2)
                    
                    # Extract data
                    html = page.content()
                    items = self.extractor.extract(
                        html, content_type, fields,
                        quantity=quantity - len(all_items)
                    )
                    
                    all_items.extend(items)
                    logger.info(f"   Extracted {len(items)} items (total: {len(all_items)})")
                    
                    # Check if we have enough
                    if len(all_items) >= quantity:
                        logger.info(f"✅ Reached target quantity: {quantity}")
                        break
                    
                    # Try to find and click "Next" button
                    if not self._click_next(page):
                        logger.info("⚠️ No more pages available")
                        break
                    
                    time.sleep(2)  # Wait between pages
                
                browser.close()
                
                log_step(logger, "Paginated Scraping", "SUCCESS", {
                    "total_items": len(all_items),
                    "pages_scraped": page_num
                })
                
                return all_items[:quantity]  # Return only requested quantity
        
        except Exception as e:
            log_step(logger, "Paginated Scraping", "FAILED", {
                "error": str(e)
            })
            logger.exception("Paginated scraping failed")
            return all_items  # Return what we got
    
    def _click_next(self, page: Page) -> bool:
        """
        Try to click "Next" button for pagination
        
        Args:
            page: Playwright page object
        
        Returns:
            True if next button was clicked, False otherwise
        """
        # Common "Next" button selectors
        next_selectors = [
            'a:has-text("Next")',
            'button:has-text("Next")',
            '.next',
            '.pagination-next',
            'a[rel="next"]',
            'a:has-text("›")',
            'a:has-text("→")'
        ]
        
        for selector in next_selectors:
            try:
                if page.locator(selector).count() > 0:
                    logger.info(f"   Found next button: {selector}")
                    page.click(selector)
                    page.wait_for_load_state('networkidle')
                    logger.info("   ✅ Clicked next button")
                    return True
            except Exception as e:
                logger.debug(f"   Failed to click {selector}: {e}")
                continue
        
        logger.debug("   No next button found")
        return False
