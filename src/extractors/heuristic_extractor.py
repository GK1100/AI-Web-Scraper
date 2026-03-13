"""
Step 5: Heuristic Extraction
Extracts data using common patterns without LLM
Fast, free, and works for most common content types
"""

import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

from logger import setup_logger, log_step

logger = setup_logger(__name__)


class HeuristicExtractor:
    """
    Extracts data using heuristic patterns
    No LLM needed - uses common HTML patterns
    """
    
    def __init__(self):
        """Initialize heuristic extractor"""
        logger.info("HeuristicExtractor initialized")
        log_step(logger, "Heuristic Extractor", "INITIALIZED", {})
    
    def extract(
        self,
        html: str,
        content_type: str,
        fields: List[str],
        quantity: int = 10
    ) -> List[Dict]:
        """
        Extract data using heuristic patterns
        
        Args:
            html: HTML content
            content_type: Type of content (products, articles, reviews)
            fields: Fields to extract
            quantity: Number of items to extract
        
        Returns:
            List of extracted items
        """
        log_step(logger, "Heuristic Extraction", "STARTED", {
            "content_type": content_type,
            "fields": fields,
            "quantity": quantity,
            "html_length": len(html)
        })
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            logger.info(f"Parsed HTML: {len(soup.find_all())} elements")
            
            # Choose extraction method based on content type
            if content_type == "products":
                items = self._extract_products(soup, fields, quantity)
            elif content_type == "articles":
                items = self._extract_articles(soup, fields, quantity)
            elif content_type == "reviews":
                items = self._extract_reviews(soup, fields, quantity)
            else:
                logger.warning(f"Unknown content type: {content_type}, using generic extraction")
                items = self._extract_generic(soup, fields, quantity)
            
            log_step(logger, "Heuristic Extraction", "SUCCESS", {
                "items_found": len(items),
                "content_type": content_type
            })
            
            return items
        
        except Exception as e:
            log_step(logger, "Heuristic Extraction", "FAILED", {
                "error": str(e),
                "content_type": content_type
            })
            logger.exception("Heuristic extraction failed")
            return []
    
    def _extract_products(
        self,
        soup: BeautifulSoup,
        fields: List[str],
        quantity: int
    ) -> List[Dict]:
        """
        Extract products using heuristic patterns
        
        Products typically have:
        - Price indicators ($, €, price, cost)
        - Product names (h2, h3, product-title)
        - Images
        - "Add to cart" buttons
        """
        logger.info("🛍️ Extracting products using heuristics...")
        
        items = []
        
        # Find potential product containers
        # Look for elements with price indicators
        price_patterns = [
            r'\$\d+',  # $99
            r'€\d+',   # €99
            r'£\d+',   # £99
            r'\d+\.\d{2}',  # 99.99
        ]
        
        # Find all elements with text
        all_elements = soup.find_all(['div', 'article', 'li', 'section'])
        logger.info(f"Found {len(all_elements)} potential containers")
        
        for element in all_elements[:quantity * 3]:  # Check more than needed
            text = element.get_text()
            
            # Check if element contains price
            has_price = any(re.search(pattern, text) for pattern in price_patterns)
            
            if has_price:
                item = {}
                
                # Extract name
                if 'name' in fields or 'title' in fields:
                    name = self._extract_product_name(element)
                    if name:
                        item['name'] = name
                        logger.debug(f"Found product name: {name[:50]}")
                
                # Extract price
                if 'price' in fields:
                    price = self._extract_price(element)
                    if price:
                        item['price'] = price
                        logger.debug(f"Found price: {price}")
                
                # Extract URL
                if 'url' in fields or 'link' in fields:
                    url = self._extract_url(element)
                    if url:
                        item['url'] = url
                        logger.debug(f"Found URL: {url[:50]}")
                
                # Extract image
                if 'image' in fields:
                    image = self._extract_image(element)
                    if image:
                        item['image'] = image
                        logger.debug(f"Found image: {image[:50]}")
                
                # Extract rating
                if 'rating' in fields:
                    rating = self._extract_rating(element)
                    if rating:
                        item['rating'] = rating
                        logger.debug(f"Found rating: {rating}")
                
                # Only add if we got at least 2 fields
                if len(item) >= 2:
                    items.append(item)
                    logger.info(f"✅ Extracted product {len(items)}: {item.get('name', 'Unknown')[:30]}")
                    
                    if len(items) >= quantity:
                        break
        
        logger.info(f"🛍️ Extracted {len(items)} products")
        return items
    
    def _extract_articles(
        self,
        soup: BeautifulSoup,
        fields: List[str],
        quantity: int
    ) -> List[Dict]:
        """
        Extract articles using heuristic patterns
        
        Articles typically have:
        - Headings (h1, h2, h3)
        - Links to full article
        - Author names
        - Dates/timestamps
        """
        logger.info("📰 Extracting articles using heuristics...")
        
        items = []
        
        # Find article containers - try multiple strategies
        # Strategy 1: Look for <article> tags
        article_containers = soup.find_all('article')
        
        # Strategy 2: Look for divs with article-related classes
        if len(article_containers) < 3:
            article_divs = soup.find_all('div', class_=lambda x: x and any(
                keyword in ' '.join(x).lower() 
                for keyword in ['article', 'story', 'post', 'item', 'card']
            ))
            article_containers.extend(article_divs)
        
        # Strategy 3: Look for list items that might be articles
        if len(article_containers) < 3:
            list_items = soup.find_all('li', class_=lambda x: x and any(
                keyword in ' '.join(x).lower()
                for keyword in ['article', 'story', 'post', 'item']
            ))
            article_containers.extend(list_items)
        
        logger.info(f"Found {len(article_containers)} potential article containers")
        
        for container in article_containers[:quantity * 3]:
            item = {}
            
            # Extract title
            if 'title' in fields:
                title = self._extract_article_title(container)
                if title:
                    item['title'] = title
                    logger.debug(f"Found article title: {title[:50]}")
            
            # Extract URL
            if 'url' in fields or 'link' in fields:
                url = self._extract_url(container)
                if url:
                    item['url'] = url
                    logger.debug(f"Found URL: {url[:50]}")
            
            # Extract author
            if 'author' in fields:
                author = self._extract_author(container)
                if author:
                    item['author'] = author
                    logger.debug(f"Found author: {author}")
            
            # Extract date
            if 'date' in fields:
                date = self._extract_date(container)
                if date:
                    item['date'] = date
                    logger.debug(f"Found date: {date}")
            
            # Extract content/summary
            if 'content' in fields or 'summary' in fields:
                content = self._extract_content(container)
                if content:
                    item['content'] = content
                    logger.debug(f"Found content: {content[:50]}")
            
            # Only add if we got at least 2 fields
            if len(item) >= 2:
                items.append(item)
                logger.info(f"✅ Extracted article {len(items)}: {item.get('title', 'Unknown')[:30]}")
                
                if len(items) >= quantity:
                    break
        
        logger.info(f"📰 Extracted {len(items)} articles")
        return items
    
    def _extract_reviews(
        self,
        soup: BeautifulSoup,
        fields: List[str],
        quantity: int
    ) -> List[Dict]:
        """
        Extract reviews using heuristic patterns
        
        Reviews typically have:
        - Star ratings
        - Review text
        - Reviewer name
        - Date
        """
        logger.info("⭐ Extracting reviews using heuristics...")
        
        items = []
        
        # Find review containers
        review_containers = soup.find_all(['div', 'article', 'li'])
        logger.info(f"Found {len(review_containers)} potential review containers")
        
        for container in review_containers[:quantity * 3]:
            # Check if container has rating indicator
            text = container.get_text()
            has_rating = any(word in text.lower() for word in ['star', 'rating', '★', '⭐'])
            
            if has_rating:
                item = {}
                
                # Extract rating
                if 'rating' in fields:
                    rating = self._extract_rating(container)
                    if rating:
                        item['rating'] = rating
                        logger.debug(f"Found rating: {rating}")
                
                # Extract review text
                if 'text' in fields or 'review' in fields:
                    text = self._extract_review_text(container)
                    if text:
                        item['text'] = text
                        logger.debug(f"Found review text: {text[:50]}")
                
                # Extract reviewer
                if 'reviewer' in fields or 'author' in fields:
                    reviewer = self._extract_author(container)
                    if reviewer:
                        item['reviewer'] = reviewer
                        logger.debug(f"Found reviewer: {reviewer}")
                
                # Extract date
                if 'date' in fields:
                    date = self._extract_date(container)
                    if date:
                        item['date'] = date
                        logger.debug(f"Found date: {date}")
                
                # Only add if we got at least 2 fields
                if len(item) >= 2:
                    items.append(item)
                    logger.info(f"✅ Extracted review {len(items)}")
                    
                    if len(items) >= quantity:
                        break
        
        logger.info(f"⭐ Extracted {len(items)} reviews")
        return items
    
    def _extract_generic(
        self,
        soup: BeautifulSoup,
        fields: List[str],
        quantity: int
    ) -> List[Dict]:
        """Generic extraction for unknown content types"""
        logger.info("🔍 Using generic extraction...")
        
        items = []
        containers = soup.find_all(['div', 'article', 'li'])[:quantity]
        
        for container in containers:
            item = {}
            
            # Try to extract common fields
            for field in fields:
                if field in ['title', 'name']:
                    value = self._extract_article_title(container)
                elif field in ['url', 'link']:
                    value = self._extract_url(container)
                elif field == 'price':
                    value = self._extract_price(container)
                elif field == 'rating':
                    value = self._extract_rating(container)
                else:
                    value = None
                
                if value:
                    item[field] = value
            
            if item:
                items.append(item)
        
        logger.info(f"🔍 Extracted {len(items)} items generically")
        return items
    
    # Helper methods for extracting specific fields
    
    def _extract_product_name(self, element: BeautifulSoup) -> Optional[str]:
        """Extract product name from element"""
        # Try common product name selectors
        for selector in ['h2', 'h3', '.product-title', '.title', 'a']:
            found = element.find(selector)
            if found:
                text = found.get_text().strip()
                if len(text) > 5 and len(text) < 200:  # Reasonable length
                    return text
        return None
    
    def _extract_article_title(self, element: BeautifulSoup) -> Optional[str]:
        """Extract article title from element"""
        # Try headings first
        for tag in ['h1', 'h2', 'h3', 'h4']:
            found = element.find(tag)
            if found:
                text = found.get_text().strip()
                if len(text) > 10 and len(text) < 300:  # Reasonable title length
                    return text
        
        # Try elements with title-related classes
        for class_keyword in ['title', 'headline', 'heading']:
            found = element.find(class_=lambda x: x and class_keyword in ' '.join(x).lower())
            if found:
                text = found.get_text().strip()
                if len(text) > 10 and len(text) < 300:
                    return text
        
        # Try links with substantial text
        links = element.find_all('a')
        for link in links:
            text = link.get_text().strip()
            if len(text) > 15 and len(text) < 300:  # Longer than typical nav text
                return text
        
        return None
    
    def _extract_price(self, element: BeautifulSoup) -> Optional[str]:
        """Extract price from element"""
        text = element.get_text()
        
        # Try to find price patterns
        patterns = [
            r'\$\d+\.?\d*',  # $99.99
            r'€\d+\.?\d*',   # €99.99
            r'£\d+\.?\d*',   # £99.99
            r'\d+\.\d{2}',   # 99.99
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None
    
    def _extract_url(self, element: BeautifulSoup) -> Optional[str]:
        """Extract URL from element"""
        link = element.find('a')
        if link and link.get('href'):
            return link['href']
        return None
    
    def _extract_image(self, element: BeautifulSoup) -> Optional[str]:
        """Extract image URL from element"""
        img = element.find('img')
        if img:
            return img.get('src') or img.get('data-src')
        return None
    
    def _extract_rating(self, element: BeautifulSoup) -> Optional[str]:
        """Extract rating from element"""
        text = element.get_text()
        
        # Look for star ratings
        star_match = re.search(r'(\d+\.?\d*)\s*(?:star|★|⭐)', text, re.IGNORECASE)
        if star_match:
            return star_match.group(1)
        
        # Look for X out of Y ratings
        rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|/)\s*(\d+)', text)
        if rating_match:
            return f"{rating_match.group(1)}/{rating_match.group(2)}"
        
        return None
    
    def _extract_author(self, element: BeautifulSoup) -> Optional[str]:
        """Extract author/reviewer name from element"""
        # Try common author selectors
        for selector in ['.author', '.by', '.reviewer', '.username']:
            found = element.select_one(selector)
            if found:
                text = found.get_text().strip()
                if len(text) > 2 and len(text) < 50:
                    return text
        
        # Look for "by" pattern
        text = element.get_text()
        by_match = re.search(r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        if by_match:
            return by_match.group(1)
        
        return None
    
    def _extract_date(self, element: BeautifulSoup) -> Optional[str]:
        """Extract date from element"""
        # Try common date selectors
        for selector in ['.date', '.time', '.timestamp', 'time']:
            found = element.select_one(selector)
            if found:
                # Try datetime attribute first
                if found.get('datetime'):
                    return found['datetime']
                text = found.get_text().strip()
                if text:
                    return text
        
        # Look for date patterns in text
        text = element.get_text()
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2026-03-13
            r'\d{2}/\d{2}/\d{4}',  # 03/13/2026
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',  # Mar 13, 2026
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None
    
    def _extract_content(self, element: BeautifulSoup) -> Optional[str]:
        """Extract content/summary from element"""
        # Try common content selectors
        for selector in ['.content', '.summary', '.description', 'p']:
            found = element.select_one(selector)
            if found:
                text = found.get_text().strip()
                if len(text) > 20:  # Reasonable content length
                    return text[:500]  # Limit to 500 chars
        
        return None
    
    def _extract_review_text(self, element: BeautifulSoup) -> Optional[str]:
        """Extract review text from element"""
        # Try common review text selectors
        for selector in ['.review-text', '.review-body', '.comment', 'p']:
            found = element.select_one(selector)
            if found:
                text = found.get_text().strip()
                if len(text) > 20:
                    return text[:500]  # Limit to 500 chars
        
        return None
