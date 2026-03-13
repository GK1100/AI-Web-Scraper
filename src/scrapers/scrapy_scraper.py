"""
Scrapy-based scraper for static HTML sites
Fast and efficient for sites without JavaScript
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from logger import setup_logger, log_step

logger = setup_logger(__name__)


class ScrapyScraper:
    """
    Scrapy-style scraper using requests + BeautifulSoup
    For static HTML sites (no JavaScript rendering needed)
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize Scrapy scraper
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logger.info(f"ScrapyScraper initialized (timeout={timeout}s)")
    
    def scrape(
        self,
        url: str,
        content_type: str,
        fields: List[str],
        quantity: int = 10,
        selectors: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Scrape data from static HTML site
        
        Args:
            url: URL to scrape
            content_type: Type of content (products, articles, reviews)
            fields: Fields to extract
            quantity: Number of items to extract
            selectors: Optional CSS selectors
        
        Returns:
            List of extracted items
        """
        logger.info(f"🌐 Fetching URL: {url}")
        
        try:
            # Fetch HTML
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            logger.info(f"📝 Retrieved HTML: {len(html)} characters")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data
            if selectors:
                items = self._extract_with_selectors(soup, selectors, fields, quantity)
            else:
                items = self._extract_with_heuristics(soup, content_type, fields, quantity)
            
            log_step(logger, "Scrapy Scraping", "SUCCESS", {
                'items_extracted': len(items),
                'url': url
            })
            
            return items[:quantity]
            
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            log_step(logger, "Scrapy Scraping", "FAILED", {'error': str(e)})
            return []
    
    def _extract_with_selectors(
        self,
        soup: BeautifulSoup,
        selectors: Dict,
        fields: List[str],
        quantity: int
    ) -> List[Dict]:
        """Extract data using provided CSS selectors"""
        logger.info("🎯 Using provided selectors for extraction")
        
        items = []
        container_selector = selectors.get('container', 'div')
        field_selectors = selectors.get('selectors', {})
        
        logger.info(f"🎯 Extracting with CSS selectors...")
        logger.info(f"   Container: {container_selector}")
        logger.info(f"   Fields: {fields}")
        
        # Find all containers
        containers = soup.select(container_selector)
        logger.info(f"   Found {len(containers)} containers")
        
        for i, container in enumerate(containers[:quantity], 1):
            item = {}
            
            for field in fields:
                selector = field_selectors.get(field, '')
                
                if '::text' in selector:
                    # Extract text content
                    css_selector = selector.replace('::text', '')
                    element = container.select_one(css_selector)
                    item[field] = element.get_text(strip=True) if element else None
                    
                elif '::attr(' in selector:
                    # Extract attribute
                    css_selector, attr = selector.split('::attr(')
                    attr = attr.rstrip(')')
                    element = container.select_one(css_selector)
                    item[field] = element.get(attr) if element else None
                    
                else:
                    # Default: extract text
                    element = container.select_one(selector)
                    item[field] = element.get_text(strip=True) if element else None
            
            if any(item.values()):
                items.append(item)
                logger.info(f"✅ Extracted item {i}")
        
        logger.info(f"🎯 Extracted {len(items)} items with selectors")
        return items
    
    def _extract_with_heuristics(
        self,
        soup: BeautifulSoup,
        content_type: str,
        fields: List[str],
        quantity: int
    ) -> List[Dict]:
        """Extract data using heuristic patterns"""
        logger.info("🔍 Using heuristic extraction")
        
        from heuristic_extractor import HeuristicExtractor
        
        extractor = HeuristicExtractor()
        items = extractor.extract(
            html=str(soup),
            content_type=content_type,
            fields=fields,
            quantity=quantity
        )
        
        return items
