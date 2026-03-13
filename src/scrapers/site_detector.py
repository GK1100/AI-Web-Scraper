"""
Step 2: Site Type Detection
Determines if a site needs JavaScript rendering (Playwright) or works with static HTML (Scrapy)
"""

import requests
from bs4 import BeautifulSoup
from typing import Literal
from dataclasses import dataclass

from logger import setup_logger, log_step

logger = setup_logger(__name__)


@dataclass
class SiteInfo:
    """Information about a website"""
    url: str
    tool: Literal["scrapy", "playwright"]
    reasoning: str
    has_js_frameworks: bool
    content_length: int


class SiteDetector:
    """Detects whether a site needs JavaScript rendering"""
    
    # JavaScript framework indicators
    JS_INDICATORS = [
        'react', 'vue', 'angular', 'next', 'nuxt',
        '__NEXT_DATA__', 'data-reactroot', 'ng-app', 'v-app',
        'gatsby', 'svelte', 'ember'
    ]
    
    # Sites known to need Playwright
    KNOWN_JS_SITES = [
        'amazon.com', 'twitter.com', 'facebook.com', 
        'instagram.com', 'linkedin.com', 'youtube.com'
    ]
    
    # Sites known to work with Scrapy
    KNOWN_STATIC_SITES = [
        'news.ycombinator.com', 'reddit.com', 'craigslist.org',
        'stackoverflow.com', 'wikipedia.org'
    ]
    
    def __init__(self):
        """Initialize detector"""
        self.cache = {}  # Cache results by domain
        logger.info("SiteDetector initialized")
    
    def detect(self, url: str) -> SiteInfo:
        """
        Detect if site needs JavaScript rendering
        
        Args:
            url: Website URL to check
        
        Returns:
            SiteInfo with detection results
        """
        log_step(logger, "Site Detection", "STARTED", {"url": url})
        
        try:
            # Extract domain
            domain = self._extract_domain(url)
            
            # Check cache
            if domain in self.cache:
                logger.info(f"Using cached result for {domain}")
                return self.cache[domain]
            
            # Check known sites first
            if self._is_known_js_site(domain):
                site_info = SiteInfo(
                    url=url,
                    tool="playwright",
                    reasoning="Known JavaScript-heavy site",
                    has_js_frameworks=True,
                    content_length=0
                )
                self.cache[domain] = site_info
                log_step(logger, "Site Detection", "SUCCESS", site_info.__dict__)
                return site_info
            
            if self._is_known_static_site(domain):
                site_info = SiteInfo(
                    url=url,
                    tool="scrapy",
                    reasoning="Known static HTML site",
                    has_js_frameworks=False,
                    content_length=0
                )
                self.cache[domain] = site_info
                log_step(logger, "Site Detection", "SUCCESS", site_info.__dict__)
                return site_info
            
            # Fetch and analyze
            logger.info(f"Analyzing {url}...")
            html = self._fetch_html(url)
            
            if not html:
                # Default to Playwright if fetch fails
                site_info = SiteInfo(
                    url=url,
                    tool="playwright",
                    reasoning="Fetch failed, defaulting to Playwright",
                    has_js_frameworks=False,
                    content_length=0
                )
                log_step(logger, "Site Detection", "SUCCESS", site_info.__dict__)
                return site_info
            
            # Analyze HTML
            has_js = self._has_js_frameworks(html)
            content_length = self._get_content_length(html)
            
            # Decide tool
            if has_js:
                tool = "playwright"
                reasoning = "Detected JavaScript frameworks"
            elif content_length < 500:
                tool = "playwright"
                reasoning = "Low content, likely needs JS rendering"
            else:
                tool = "scrapy"
                reasoning = "Static HTML with sufficient content"
            
            site_info = SiteInfo(
                url=url,
                tool=tool,
                reasoning=reasoning,
                has_js_frameworks=has_js,
                content_length=content_length
            )
            
            # Cache result
            self.cache[domain] = site_info
            
            log_step(logger, "Site Detection", "SUCCESS", site_info.__dict__)
            return site_info
        
        except Exception as e:
            log_step(logger, "Site Detection", "FAILED", {"error": str(e)})
            logger.exception("Site detection failed")
            
            # Default to Playwright on error
            return SiteInfo(
                url=url,
                tool="playwright",
                reasoning=f"Error during detection: {str(e)}",
                has_js_frameworks=False,
                content_length=0
            )
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            # Remove protocol
            domain = url.split('//')[1] if '//' in url else url
            # Remove path
            domain = domain.split('/')[0]
            # Remove www
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return url
    
    def _is_known_js_site(self, domain: str) -> bool:
        """Check if domain is known to need JavaScript"""
        return any(known in domain for known in self.KNOWN_JS_SITES)
    
    def _is_known_static_site(self, domain: str) -> bool:
        """Check if domain is known to be static"""
        return any(known in domain for known in self.KNOWN_STATIC_SITES)
    
    def _fetch_html(self, url: str, timeout: int = 10) -> str:
        """Fetch HTML with requests"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return ""
    
    def _has_js_frameworks(self, html: str) -> bool:
        """Check if HTML contains JavaScript framework indicators"""
        html_lower = html.lower()
        found_indicators = [ind for ind in self.JS_INDICATORS if ind in html_lower]
        
        if found_indicators:
            logger.debug(f"Found JS indicators: {found_indicators}")
            return True
        return False
    
    def _get_content_length(self, html: str) -> int:
        """Get length of text content (excluding scripts/styles)"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove scripts and styles
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            
            # Get text
            text = soup.get_text(strip=True)
            return len(text)
        except:
            return 0
