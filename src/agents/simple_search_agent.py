"""
Simple Search Agent using duckduckgo_search library
More reliable than scraping HTML
"""

from typing import List, Dict, Optional
from logger import setup_logger

logger = setup_logger(__name__)


class SimpleSearchAgent:
    """
    Search agent using duckduckgo_search library
    No browser needed, no HTML parsing, just works!
    """
    
    def __init__(self):
        """Initialize Simple Search Agent"""
        try:
            # Try new package name first
            try:
                from ddgs import DDGS
            except ImportError:
                # Fallback to old package name
                from duckduckgo_search import DDGS
            
            self.ddgs = DDGS()
            logger.info("SimpleSearchAgent initialized (using DuckDuckGo search)")
        except ImportError:
            logger.error("DuckDuckGo search library not installed. Run: pip install ddgs")
            self.ddgs = None
    
    def search_and_get_urls(
        self,
        query: str,
        num_results: int = 10,
        skip_domains: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Search and get URLs
        
        Args:
            query: Search query
            num_results: Number of results
            skip_domains: Domains to skip
        
        Returns:
            List of dicts with 'url', 'title', 'snippet'
        """
        if not self.ddgs:
            logger.error("Search agent not initialized")
            return []
        
        logger.info(f"🔍 Searching for: {query}")
        logger.info(f"📊 Requesting {num_results} results")
        
        skip_domains = skip_domains or []
        results = []
        
        try:
            # Search using duckduckgo_search library
            search_results = self.ddgs.text(query, max_results=num_results * 2)
            
            for result in search_results:
                if len(results) >= num_results:
                    break
                
                url = result.get('href', '')
                title = result.get('title', '')
                snippet = result.get('body', '')
                
                # Skip unwanted domains
                if any(domain in url for domain in skip_domains):
                    continue
                
                if url and title:
                    results.append({
                        'url': url,
                        'title': title,
                        'snippet': snippet
                    })
            
            logger.info(f"✅ Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


def main():
    """Test Simple Search Agent"""
    agent = SimpleSearchAgent()
    
    if not agent.ddgs:
        print("\n❌ Please install: pip install duckduckgo-search")
        return
    
    results = agent.search_and_get_urls('digital marketing strategies', 5)
    
    print(f"\n✅ Found {len(results)} results\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title'][:60]}")
        print(f"   {r['url']}\n")


if __name__ == "__main__":
    main()
