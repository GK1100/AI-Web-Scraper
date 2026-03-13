"""
Full Content Extractor
Extracts complete content (full blog, article, news story, etc.)
Always includes: title, description, full content, source_url
"""

from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re
from logger import setup_logger

logger = setup_logger(__name__)


class FullContentExtractor:
    """
    Extracts complete content from web pages
    Mandatory fields: title, description, content, source_url
    """
    
    def __init__(self):
        """Initialize full content extractor"""
        logger.info("FullContentExtractor initialized")
    
    def extract_full_content(
        self,
        html: str,
        url: str,
        content_type: str
    ) -> Dict:
        """
        Extract full content with mandatory fields
        
        Returns:
            {
                'title': 'Article/Blog/Product Title',
                'description': 'Brief summary',
                'content': 'FULL text content',
                'source_url': 'https://...',
                'author': 'Author name' (optional),
                'date': 'Publication date' (optional)
            }
        """
        logger.info(f"📄 Extracting full content from {url}")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            tag.decompose()
        
        # Extract mandatory fields
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        content = self._extract_main_content(soup, content_type)
        
        # Extract optional fields
        author = self._extract_author(soup)
        date = self._extract_date(soup)
        
        result = {
            'title': title or '',
            'description': description or '',
            'content': content or '',
            'source_url': url,
            'author': author or '',
            'date': date or ''
        }
        
        logger.info(f"✅ Extracted: title={bool(title)}, desc={bool(description)}, content={len(content) if content else 0} chars")
        
        return result

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title (h1, og:title, title tag)"""
        # Try h1 first
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # Try og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title.get('content')
        
        # Try title tag
        title = soup.find('title')
        if title:
            return title.get_text(strip=True)
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description (meta description, og:description, first paragraph)"""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content')
        
        # Try og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc.get('content')
        
        # Try first paragraph
        p = soup.find('p')
        if p:
            text = p.get_text(strip=True)
            if len(text) > 50:
                return text[:300]
        
        return None
    
    def _extract_main_content(self, soup: BeautifulSoup, content_type: str) -> Optional[str]:
        """
        Extract FULL main content
        For blogs/articles: complete text
        For products: full description
        For news: full story
        """
        # Try to find main content area (ordered by specificity)
        main_selectors = [
            'article',
            '[role="main"]',
            'main',
            '.post-content', '.article-content', '.entry-content',
            '.content-body', '.post-body', '.article-body',
            '.blog-content', '.blog-post', '.single-post',
            '.content', '#content', '#main-content',
            '.page-content', '.site-content',
            '.td-post-content', '.entry', '.post'
        ]
        
        content_element = None
        for selector in main_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                # Verify it has meaningful text (not just nav/header)
                text = content_element.get_text(strip=True)
                if len(text) > 200:
                    break
                content_element = None
        
        if not content_element:
            # Fallback: find the div with the most paragraph text
            best_div = None
            best_len = 0
            for div in soup.find_all(['div', 'section']):
                paragraphs = div.find_all('p')
                text_len = sum(len(p.get_text(strip=True)) for p in paragraphs)
                if text_len > best_len:
                    best_len = text_len
                    best_div = div
            
            content_element = best_div if best_div else soup.find('body')
        
        if content_element:
            # Extract all text from paragraphs and headings
            paragraphs = content_element.find_all(['p', 'h2', 'h3', 'h4', 'li'])
            text_parts = []
            
            for elem in paragraphs:
                text = elem.get_text(strip=True)
                if text and len(text) > 20:  # Skip very short text
                    text_parts.append(text)
            
            full_content = '\n\n'.join(text_parts)
            
            # If still empty, grab all text from the element
            if not full_content:
                full_content = content_element.get_text(separator='\n', strip=True)
            
            # Clean up
            full_content = re.sub(r'\n\s*\n\s*\n', '\n\n', full_content)
            
            return full_content
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author name"""
        # Try meta author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author.get('content')
        
        # Try common author selectors
        author_selectors = ['.author', '.by-author', '[rel="author"]', '.post-author']
        for selector in author_selectors:
            author = soup.select_one(selector)
            if author:
                return author.get_text(strip=True)
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date"""
        # Try time tag
        time_tag = soup.find('time')
        if time_tag:
            return time_tag.get('datetime') or time_tag.get_text(strip=True)
        
        # Try meta date
        meta_date = soup.find('meta', property='article:published_time')
        if meta_date and meta_date.get('content'):
            return meta_date.get('content')
        
        return None
