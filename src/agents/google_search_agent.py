"""
Google Search Agent
Searches Google, extracts top organic results, and scrapes them
No URL needed - just provide a query!
"""

import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page
from logger import setup_logger

logger = setup_logger(__name__)


class GoogleSearchAgent:
    """
    Intelligent agent that:
    1. Searches Google for a query
    2. Extracts top organic results (skips ads)
    3. Returns URLs to scrape
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize Google Search Agent
        
        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        logger.info("GoogleSearchAgent initialized")
    
    def search_and_get_urls(
        self,
        query: str,
        num_results: int = 10,
        skip_domains: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Search Google and extract top organic result URLs
        
        Args:
            query: Search query
            num_results: Number of results to return
            skip_domains: Domains to skip (e.g., ['youtube.com', 'facebook.com'])
        
        Returns:
            List of dicts with 'url', 'title', 'snippet'
        """
        logger.info(f"🔍 Searching Google for: {query}")
        logger.info(f"📊 Requesting {num_results} results")
        
        skip_domains = skip_domains or []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            
            # Create context with user agent to avoid being blocked
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            try:
                # Search Google - encode query properly
                from urllib.parse import quote_plus
                encoded_query = quote_plus(query)
                search_url = f"https://www.google.com/search?q={encoded_query}&num={num_results * 2}"
                logger.info(f"🌐 Navigating to: {search_url}")
                
                page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(2000)  # Wait for results to load
                
                # Get HTML
                html = page.content()
                
                # Debug: Save HTML to see what we're getting
                try:
                    import os
                    from datetime import datetime
                    debug_dir = 'debug'
                    if not os.path.exists(debug_dir):
                        os.makedirs(debug_dir)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    debug_file = f"{debug_dir}/google_search_{timestamp}.html"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(html)
                    logger.info(f"🐛 Debug: Saved HTML to {debug_file}")
                except Exception as e:
                    logger.debug(f"Could not save debug HTML: {e}")
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract organic results
                results = self._extract_organic_results(soup, num_results, skip_domains)
                
                logger.info(f"✅ Found {len(results)} organic results")
                
                browser.close()
                return results
                
            except Exception as e:
                logger.error(f"Google search failed: {e}")
                browser.close()
                return []
    
    def _extract_organic_results(
        self,
        soup: BeautifulSoup,
        num_results: int,
        skip_domains: List[str]
    ) -> List[Dict[str, str]]:
        """
        Extract organic search results from Google HTML
        Skips ads, featured snippets, and unwanted domains
        Uses multiple selectors as Google's HTML changes frequently
        """
        results = []
        
        # Try multiple selectors (Google changes these frequently)
        selectors_to_try = [
            'div.g',                          # Classic selector
            'div[data-sokoban-container]',    # New selector
            'div.Gx5Zad',                     # Alternative
            'div[jscontroller]',              # Generic container
            'div[data-hveid]',                # Another option
        ]
        
        search_divs = []
        for selector in selectors_to_try:
            divs = soup.select(selector)
            if divs:
                search_divs = divs
                logger.info(f"📦 Found {len(divs)} containers using selector: {selector}")
                break
        
        if not search_divs:
            logger.warning("⚠️ No result containers found with any selector")
            logger.debug("Trying to find any links in the page...")
            
            # Fallback: Find all links that look like search results
            all_links = soup.find_all('a', href=True)
            logger.info(f"📦 Found {len(all_links)} total links on page")
            
            for link in all_links:
                if len(results) >= num_results:
                    break
                
                url = link.get('href', '')
                
                # Skip internal Google links
                if not url or url.startswith('/') or 'google.com' in url:
                    continue
                
                # Skip unwanted domains
                if any(domain in url for domain in skip_domains):
                    continue
                
                # Must start with http
                if not url.startswith('http'):
                    continue
                
                # Get title from link text or nearby h3
                title = link.get_text(strip=True)
                if not title:
                    h3 = link.find('h3')
                    title = h3.get_text(strip=True) if h3 else ""
                
                if url and title and len(title) > 10:  # Reasonable title length
                    results.append({
                        'url': url,
                        'title': title,
                        'snippet': ''
                    })
                    logger.debug(f"✅ Found result: {title[:50]}...")
            
            return results
        
        # Normal extraction with found containers
        for div in search_divs:
            if len(results) >= num_results:
                break
            
            # Skip ads (they have specific markers)
            if div.find('span', text=re.compile(r'Ad|Sponsored', re.IGNORECASE)):
                logger.debug("⏭️ Skipping ad")
                continue
            
            # Find link - try multiple approaches
            link = div.find('a', href=True)
            if not link:
                # Try finding link in child elements
                link = div.select_one('a[href]')
            
            if not link or not link.get('href'):
                continue
            
            url = link.get('href')
            
            # Skip Google's own URLs
            if url.startswith('/search') or 'google.com' in url:
                continue
            
            # Skip unwanted domains
            if any(domain in url for domain in skip_domains):
                logger.debug(f"⏭️ Skipping domain: {url}")
                continue
            
            # Extract title - try multiple approaches
            title = ""
            title_elem = div.find('h3')
            if title_elem:
                title = title_elem.get_text(strip=True)
            elif link:
                title = link.get_text(strip=True)
            
            # Extract snippet - try multiple class patterns
            snippet = ""
            snippet_patterns = [
                'VwiC3b', 's3v9rd', 'st', 'IsZvec',
                'aCOpRe', 'yDYNvb', 'lyLwlc'
            ]
            for pattern in snippet_patterns:
                snippet_elem = div.find('div', class_=re.compile(pattern))
                if snippet_elem:
                    snippet = snippet_elem.get_text(strip=True)
                    break
            
            if url and title:
                results.append({
                    'url': url,
                    'title': title,
                    'snippet': snippet
                })
                logger.debug(f"✅ Result {len(results)}: {title[:50]}...")
        
        return results


def main():
    """Test Google Search Agent"""
    agent = GoogleSearchAgent()
    
    test_queries = [
        "SEO optimization best practices",
        "pitch deck writing tips",
        "top movie scripts of all time"
    ]
    
    print("\n" + "="*70)
    print("Google Search Agent Test")
    print("="*70)
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-"*70)
        
        results = agent.search_and_get_urls(query, num_results=5)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Snippet: {result['snippet'][:100]}...")


if __name__ == "__main__":
    main()
