"""
Intelligent URL Generator
Automatically generates search URLs based on user prompts
No URL needed - AI figures out where to search!
"""

import re
from typing import Optional, Dict
from urllib.parse import quote_plus
from logger import setup_logger

logger = setup_logger(__name__)


class URLGenerator:
    """
    Generates appropriate URLs based on user prompts
    Supports Google Search, specific sites, and more
    """
    
    def __init__(self):
        """Initialize URL generator"""
        logger.info("URLGenerator initialized")
    
    def generate_url(self, prompt: str) -> Dict[str, str]:
        """
        Generate URL based on user prompt
        
        Args:
            prompt: User's natural language prompt
        
        Returns:
            Dict with 'url' and 'search_query'
        """
        logger.info(f"🔍 Generating URL from prompt: {prompt}")
        
        # Extract search intent
        search_query = self._extract_search_query(prompt)
        
        # Determine search type
        if self._is_ranking_query(prompt):
            url = self._generate_google_search_url(search_query)
            logger.info(f"📊 Ranking query detected: {search_query}")
        elif self._is_news_query(prompt):
            url = self._generate_google_news_url(search_query)
            logger.info(f"📰 News query detected: {search_query}")
        elif self._is_shopping_query(prompt):
            url = self._generate_shopping_url(search_query)
            logger.info(f"🛒 Shopping query detected: {search_query}")
        else:
            url = self._generate_google_search_url(search_query)
            logger.info(f"🔎 General search: {search_query}")
        
        logger.info(f"✅ Generated URL: {url}")
        
        return {
            'url': url,
            'search_query': search_query
        }
    
    def _extract_search_query(self, prompt: str) -> str:
        """
        Extract search query by removing ONLY scraping-related words
        Keep everything else EXACTLY as user typed
        
        Examples:
        "scrape top 10 blogs ranking on digital marketing strategies" 
            → "top 10 blogs ranking on digital marketing strategies"
        
        "get best SEO optimization tips" 
            → "best SEO optimization tips"
        
        "extract latest tech news" 
            → "latest tech news"
        """
        # Remove ONLY scraping-related words
        scraping_words = [
            r'\bscrape\b', r'\bscrap\b', r'\bscraping\b',
            r'\bextract\b', r'\bextracting\b', r'\bextraction\b',
            r'\bget\b', r'\bgetting\b',
            r'\bfetch\b', r'\bfetching\b',
            r'\bfind\b', r'\bfinding\b',
            r'\bcollect\b', r'\bcollecting\b',
            r'\bgrab\b', r'\bgrabbing\b',
            r'\bpull\b', r'\bpulling\b',
            r'\bretrieve\b', r'\bretrieving\b'
        ]
        
        cleaned = prompt
        for word_pattern in scraping_words:
            cleaned = re.sub(word_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        result = cleaned if cleaned else prompt
        logger.info(f"📌 Search query (removed scraping words only): {result}")
        return result

    def _is_ranking_query(self, prompt: str) -> bool:
        """Check if query is about rankings/top results"""
        ranking_keywords = [
            'ranking', 'ranked', 'top', 'best', 'leading',
            'popular', 'trending', 'most viewed'
        ]
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in ranking_keywords)
    
    def _is_news_query(self, prompt: str) -> bool:
        """Check if query is about news"""
        news_keywords = ['news', 'latest', 'recent', 'breaking', 'today']
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in news_keywords)
    
    def _is_shopping_query(self, prompt: str) -> bool:
        """Check if query is about products/shopping"""
        shopping_keywords = [
            'product', 'buy', 'price', 'shop', 'purchase',
            'deal', 'offer', 'discount'
        ]
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in shopping_keywords)
    
    def _generate_google_search_url(self, query: str) -> str:
        """Generate Google search URL"""
        encoded_query = quote_plus(query)
        return f"https://www.google.com/search?q={encoded_query}&num=20"
    
    def _generate_google_news_url(self, query: str) -> str:
        """Generate Google News URL"""
        encoded_query = quote_plus(query)
        return f"https://news.google.com/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    def _generate_shopping_url(self, query: str) -> str:
        """Generate Google Shopping URL"""
        encoded_query = quote_plus(query)
        return f"https://www.google.com/search?q={encoded_query}&tbm=shop"


def main():
    """Test URL generator"""
    generator = URLGenerator()
    
    test_prompts = [
        "scrape top 10 blogs ranking on SEO optimization",
        "scrape top 10 blogs ranking on pitch deck writing",
        "top 10 movie scripts of all time",
        "latest tech news",
        "best laptops under 50000"
    ]
    
    print("\n" + "="*70)
    print("URL Generator Test")
    print("="*70)
    
    for prompt in test_prompts:
        result = generator.generate_url(prompt)
        print(f"\nPrompt: {prompt}")
        print(f"Query: {result['search_query']}")
        print(f"URL: {result['url']}")
        print("-"*70)


if __name__ == "__main__":
    main()
