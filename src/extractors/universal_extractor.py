"""
Universal Extractor - Works with ANY website dynamically
Automatically adapts to any webpage structure
"""

from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from collections import Counter, defaultdict
import re
from logger import setup_logger

logger = setup_logger(__name__)


class UniversalExtractor:
    """
    Universal extractor that works with any website
    Dynamically adapts to any structure
    """
    
    def __init__(self):
        """Initialize universal extractor"""
        logger.info("UniversalExtractor initialized")
    
    def extract(
        self,
        html: str,
        content_type: str,
        fields: List[str],
        quantity: int = 10
    ) -> List[Dict]:
        """
        Extract data from ANY website dynamically
        
        Args:
            html: HTML content
            content_type: Type of content (products, articles, etc.)
            fields: Fields to extract
            quantity: Number of items to extract
        
        Returns:
            List of extracted items
        """
        logger.info(f"🌐 Universal extraction for {content_type}...")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Step 1: Find all repeating patterns
        patterns = self._find_all_patterns(soup, min_count=max(3, quantity // 2))
        
        if not patterns:
            logger.warning("No repeating patterns found")
            return []
        
        logger.info(f"Found {len(patterns)} potential patterns")
        
        # Step 2: Try each pattern until we get good results
        for i, pattern in enumerate(patterns[:10], 1):  # Try top 10 patterns
            logger.info(f"Trying pattern {i}: {pattern['selector']} ({pattern['count']} items)")
            
            items = self._extract_from_pattern(soup, pattern, fields, quantity)
            
            # Check if we got good results
            if items and len(items) >= min(3, quantity // 2):
                quality_score = self._calculate_quality(items, fields)
                logger.info(f"  Quality score: {quality_score:.2f}")
                
                if quality_score > 0.3:  # At least 30% quality
                    logger.info(f"✅ Success with pattern: {pattern['selector']}")
                    return items[:quantity]
        
        logger.warning("No pattern produced good results")
        return []

    
    def _find_all_patterns(self, soup: BeautifulSoup, min_count: int = 3) -> List[Dict]:
        """Find all repeating patterns in the page"""
        patterns = []
        element_groups = defaultdict(list)
        
        # Group elements by their signature
        for element in soup.find_all(['div', 'article', 'li', 'section', 'a']):
            if not isinstance(element, Tag):
                continue
            
            # Create signature
            classes = element.get('class', [])
            if classes:
                sig = f"{element.name}.{'.'.join(sorted(classes))}"
            else:
                sig = element.name
            
            element_groups[sig].append(element)
        
        # Find patterns with enough repetitions
        for sig, elements in element_groups.items():
            if len(elements) >= min_count:
                # Calculate richness (how much content)
                avg_text_length = sum(len(e.get_text()) for e in elements[:5]) / min(5, len(elements))
                avg_children = sum(len(list(e.children)) for e in elements[:5]) / min(5, len(elements))
                
                richness = (avg_text_length / 100) * (avg_children / 5)
                
                patterns.append({
                    'selector': sig,
                    'count': len(elements),
                    'elements': elements,
                    'richness': richness,
                    'score': len(elements) * richness
                })
        
        # Sort by score
        patterns.sort(key=lambda x: x['score'], reverse=True)
        return patterns
    
    def _extract_from_pattern(
        self,
        soup: BeautifulSoup,
        pattern: Dict,
        fields: List[str],
        quantity: int
    ) -> List[Dict]:
        """Extract data from a specific pattern"""
        items = []
        
        for element in pattern['elements'][:quantity * 2]:
            item = {}
            
            # Extract each field dynamically
            for field in fields:
                value = self._extract_field(element, field)
                if value:
                    item[field] = value
            
            # Only add if we got at least 1 field
            if item:
                items.append(item)
        
        return items
    
    def _extract_field(self, element: Tag, field: str) -> Optional[str]:
        """Extract a specific field from element dynamically"""
        
        # Special handling for URLs
        if field in ['url', 'link', 'href']:
            link = element.find('a')
            if link and link.get('href'):
                return link['href']
            if element.name == 'a' and element.get('href'):
                return element['href']
        
        # Special handling for images
        if field in ['image', 'img', 'photo']:
            img = element.find('img')
            if img:
                return img.get('src') or img.get('data-src')
        
        # For text fields, use smart extraction
        keywords = self._get_field_keywords(field)
        
        # Strategy 1: Find by class name
        for keyword in keywords:
            found = element.find(class_=lambda x: x and keyword in ' '.join(x).lower())
            if found:
                text = found.get_text().strip()
                if self._is_valid_text(text, field):
                    return text
        
        # Strategy 2: Find by tag (for titles)
        if field in ['title', 'name', 'heading']:
            for tag in ['h1', 'h2', 'h3', 'h4']:
                found = element.find(tag)
                if found:
                    text = found.get_text().strip()
                    if self._is_valid_text(text, field):
                        return text
        
        # Strategy 3: Find by text pattern (for prices, ratings)
        if field == 'price':
            text = element.get_text()
            match = re.search(r'[\$€£¥]\s*\d+[.,]?\d*|\d+[.,]\d{2}\s*[\$€£¥]', text)
            if match:
                return match.group().strip()
        
        if field == 'rating':
            text = element.get_text()
            match = re.search(r'(\d+\.?\d*)\s*(?:star|★|⭐|out of|/)', text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Strategy 4: Get longest text in element
        if field in ['description', 'summary', 'content', 'text']:
            paragraphs = element.find_all(['p', 'div', 'span'])
            longest = max(paragraphs, key=lambda x: len(x.get_text()), default=None)
            if longest:
                text = longest.get_text().strip()
                if len(text) > 20:
                    return text[:500]
        
        return None
    
    def _get_field_keywords(self, field: str) -> List[str]:
        """Get keywords for field matching"""
        keywords_map = {
            'title': ['title', 'heading', 'headline', 'name'],
            'price': ['price', 'cost', 'amount'],
            'rating': ['rating', 'star', 'score'],
            'author': ['author', 'by', 'writer'],
            'date': ['date', 'time', 'published'],
            'description': ['description', 'summary', 'content'],
        }
        return keywords_map.get(field, [field])
    
    def _is_valid_text(self, text: str, field: str) -> bool:
        """Check if text is valid for field"""
        if not text or len(text) < 2:
            return False
        
        # Field-specific validation
        if field in ['title', 'name', 'heading']:
            return 10 <= len(text) <= 300
        
        if field in ['description', 'summary', 'content']:
            return len(text) >= 20
        
        if field in ['author', 'reviewer']:
            return 2 <= len(text) <= 100
        
        return True
    
    def _calculate_quality(self, items: List[Dict], fields: List[str]) -> float:
        """Calculate quality score of extracted items"""
        if not items:
            return 0.0
        
        # Check field coverage
        total_fields = len(items) * len(fields)
        filled_fields = sum(len(item) for item in items)
        
        coverage = filled_fields / total_fields if total_fields > 0 else 0
        
        # Check uniqueness (not all same)
        if len(items) > 1:
            first_item_str = str(items[0])
            all_same = all(str(item) == first_item_str for item in items)
            uniqueness = 0.0 if all_same else 1.0
        else:
            uniqueness = 1.0
        
        quality = (coverage * 0.7) + (uniqueness * 0.3)
        return quality


def main():
    """Test universal extractor"""
    extractor = UniversalExtractor()
    
    # Test HTML
    html = """
    <div class="container">
        <div class="item">
            <h2>Product 1</h2>
            <span class="price">$99</span>
        </div>
        <div class="item">
            <h2>Product 2</h2>
            <span class="price">$149</span>
        </div>
        <div class="item">
            <h2>Product 3</h2>
            <span class="price">$199</span>
        </div>
    </div>
    """
    
    items = extractor.extract(html, 'products', ['title', 'price'], 10)
    
    print("\nExtracted items:")
    for i, item in enumerate(items, 1):
        print(f"{i}. {item}")


if __name__ == "__main__":
    main()
