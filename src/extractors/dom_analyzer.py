"""
Advanced DOM Analyzer - Detects repeating patterns in webpage structure
Analyzes DOM tree to find repeating containers and generate CSS selectors
"""

from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from collections import Counter, defaultdict
import re
from logger import setup_logger

logger = setup_logger(__name__)


class DOMAnalyzer:
    """
    Analyzes DOM structure to detect repeating patterns
    Generates CSS selectors based on structural analysis
    """
    
    def __init__(self):
        """Initialize DOM analyzer"""
        logger.info("DOMAnalyzer initialized")
        
        # Semantic field mappings
        self.field_keywords = {
            'title': ['title', 'heading', 'name', 'product-name', 'article-title', 'h1', 'h2', 'h3'],
            'price': ['price', 'cost', 'amount', 'value', 'currency'],
            'rating': ['rating', 'stars', 'score', 'review'],
            'author': ['author', 'by', 'writer', 'username', 'user'],
            'date': ['date', 'time', 'timestamp', 'published', 'posted'],
            'image': ['image', 'img', 'photo', 'picture', 'thumbnail'],
            'url': ['link', 'href', 'url'],
            'description': ['description', 'summary', 'content', 'text', 'body'],
        }
    
    def analyze_and_extract(
        self,
        html: str,
        content_type: str,
        fields: List[str],
        quantity: int = 10
    ) -> Tuple[Optional[Dict[str, str]], List[Dict]]:
        """
        Analyze DOM structure and extract data
        
        Args:
            html: HTML content
            content_type: Type of content (products, articles, reviews)
            fields: Fields to extract
            quantity: Number of items to extract
        
        Returns:
            Tuple of (selectors_dict, extracted_items)
        """
        logger.info(f"🔍 Analyzing DOM structure for {content_type}...")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Step 1: Find repeating containers
        repeating_containers = self._find_repeating_containers(soup, quantity)
        
        if not repeating_containers:
            logger.warning("No repeating containers found")
            return None, []
        
        logger.info(f"✅ Found {len(repeating_containers)} repeating container patterns")
        
        # Step 2: Analyze best container pattern
        best_pattern = self._select_best_pattern(repeating_containers, content_type)
        
        if not best_pattern:
            logger.warning("Could not determine best pattern")
            return None, []
        
        logger.info(f"✅ Selected pattern: {best_pattern['selector']} ({best_pattern['count']} instances)")
        
        # Step 3: Generate field selectors
        selectors = self._generate_field_selectors(
            soup,
            best_pattern,
            fields,
            content_type
        )
        
        logger.info(f"✅ Generated selectors for {len(selectors)} fields")
        
        # Step 4: Extract data using selectors
        items = self._extract_with_selectors(soup, best_pattern, selectors, quantity)
        
        logger.info(f"✅ Extracted {len(items)} items using DOM analysis")
        
        return selectors, items
    
    def _find_repeating_containers(
        self,
        soup: BeautifulSoup,
        min_count: int = 3
    ) -> List[Dict]:
        """
        Find repeating container patterns in DOM
        
        Returns list of patterns with their selectors and counts
        """
        logger.info("🔍 Scanning DOM for repeating containers...")
        
        patterns = []
        
        # Track elements by their signature (tag + classes)
        element_signatures = defaultdict(list)
        
        # Scan all elements
        for element in soup.find_all(['div', 'article', 'li', 'section', 'tr']):
            if not isinstance(element, Tag):
                continue
            
            # Create signature: tag + sorted classes
            tag = element.name
            classes = sorted(element.get('class', []))
            
            if classes:
                signature = f"{tag}.{'.'.join(classes)}"
            else:
                # For elements without classes, use tag + parent context
                parent = element.parent
                if parent and parent.name:
                    parent_classes = sorted(parent.get('class', []))
                    if parent_classes:
                        signature = f"{parent.name}.{'.'.join(parent_classes)} > {tag}"
                    else:
                        signature = f"{parent.name} > {tag}"
                else:
                    signature = tag
            
            element_signatures[signature].append(element)
        
        # Find patterns that repeat enough times
        for signature, elements in element_signatures.items():
            count = len(elements)
            
            if count >= min_count:
                # Analyze structure consistency
                consistency_score = self._calculate_consistency(elements)
                
                if consistency_score > 0.5:  # At least 50% consistent
                    patterns.append({
                        'selector': signature,
                        'count': count,
                        'consistency': consistency_score,
                        'elements': elements[:20],  # Keep first 20 for analysis
                        'sample_element': elements[0]
                    })
        
        # Sort by count * consistency
        patterns.sort(key=lambda x: x['count'] * x['consistency'], reverse=True)
        
        logger.info(f"Found {len(patterns)} repeating patterns")
        for i, pattern in enumerate(patterns[:5], 1):
            logger.info(f"  {i}. {pattern['selector']}: {pattern['count']} instances (consistency: {pattern['consistency']:.2f})")
        
        return patterns
    
    def _calculate_consistency(self, elements: List[Tag]) -> float:
        """
        Calculate how consistent the structure is across elements
        
        Returns score between 0 and 1
        """
        if len(elements) < 2:
            return 1.0
        
        # Compare child structure
        child_structures = []
        
        for element in elements[:10]:  # Sample first 10
            # Get child tags and classes
            children = []
            for child in element.find_all(recursive=False):
                if isinstance(child, Tag):
                    child_sig = f"{child.name}.{'.'.join(sorted(child.get('class', [])))}"
                    children.append(child_sig)
            child_structures.append(tuple(children))
        
        if not child_structures:
            return 0.5
        
        # Calculate most common structure
        structure_counts = Counter(child_structures)
        most_common_count = structure_counts.most_common(1)[0][1]
        
        consistency = most_common_count / len(child_structures)
        return consistency
    
    def _select_best_pattern(
        self,
        patterns: List[Dict],
        content_type: str
    ) -> Optional[Dict]:
        """
        Select the best pattern based on content type and structure
        """
        if not patterns:
            return None
        
        # Content type hints
        preferred_tags = {
            'products': ['div', 'article', 'li'],
            'articles': ['article', 'div', 'li'],
            'reviews': ['div', 'article', 'li'],
        }
        
        # Tags to avoid
        avoid_tags = ['tr', 'td', 'th', 'tbody', 'thead']
        
        # Overly generic patterns to filter out
        generic_patterns = [
            'div > div',
            'div',
            'span',
            'p',
            'a',
            'li',  # Without parent context
        ]
        
        preferred = preferred_tags.get(content_type, ['div', 'article'])
        
        # Score patterns
        valid_patterns = []
        for pattern in patterns:
            selector = pattern['selector']
            
            # Skip overly generic patterns
            if selector in generic_patterns:
                logger.debug(f"Skipping generic pattern: {selector}")
                continue
            
            # Skip patterns with no class names (too generic)
            if '.' not in selector and '>' not in selector and '#' not in selector:
                logger.debug(f"Skipping pattern without identifiers: {selector}")
                continue
            
            score = pattern['count'] * pattern['consistency']
            
            # Get tag from selector
            tag = pattern['selector'].split('.')[0].split('>')[0].strip()
            
            # Penalize avoided tags
            if tag in avoid_tags:
                score *= 0.1
                logger.debug(f"Penalizing {pattern['selector']} (table element)")
            
            # Bonus for preferred tags
            if tag in preferred:
                score *= 1.2
            
            # Bonus for semantic class names
            selector_lower = pattern['selector'].lower()
            semantic_keywords = ['product', 'article', 'item', 'card', 'post', 'review', 'story', 'listing', 'result']
            if any(keyword in selector_lower for keyword in semantic_keywords):
                score *= 2.0  # Increased from 1.5
                logger.debug(f"Boosting {pattern['selector']} (semantic keyword)")
            
            # Penalize obfuscated class names (css-xxxxx, _xxxxx)
            if re.search(r'(css-[a-z0-9]{6,}|_[A-Za-z0-9]{6,})', selector_lower):
                score *= 0.5  # Increased penalty from 0.7
                logger.debug(f"Penalizing {pattern['selector']} (obfuscated classes)")
            
            # Bonus for having multiple class names (more specific)
            class_count = selector.count('.')
            if class_count >= 2:
                score *= 1.3
                logger.debug(f"Boosting {pattern['selector']} (multiple classes)")
            
            # Minimum count threshold
            if pattern['count'] < 3:
                score *= 0.5
                logger.debug(f"Penalizing {pattern['selector']} (too few instances)")
            
            pattern['score'] = score
            valid_patterns.append(pattern)
        
        if not valid_patterns:
            logger.warning("No valid patterns found after filtering")
            return None
        
        # Return highest scoring pattern
        valid_patterns.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"Top 3 patterns after scoring:")
        for i, p in enumerate(valid_patterns[:3], 1):
            logger.info(f"  {i}. {p['selector']}: score={p['score']:.2f}")
        
        # Only return if score is above minimum threshold
        best_pattern = valid_patterns[0]
        if best_pattern['score'] < 5.0:  # Minimum quality threshold
            logger.warning(f"Best pattern score ({best_pattern['score']:.2f}) below threshold (5.0)")
            return None
        
        return best_pattern
    
    def _generate_field_selectors(
        self,
        soup: BeautifulSoup,
        pattern: Dict,
        fields: List[str],
        content_type: str
    ) -> Dict[str, str]:
        """
        Generate CSS selectors for each field based on semantic analysis
        """
        logger.info(f"🔍 Generating selectors for fields: {fields}")
        
        selectors = {}
        sample_element = pattern['sample_element']
        base_selector = pattern['selector']
        
        for field in fields:
            selector = self._find_field_selector(
                sample_element,
                field,
                base_selector
            )
            
            if selector:
                selectors[field] = selector
                logger.info(f"  ✅ {field}: {selector}")
            else:
                logger.warning(f"  ⚠️ {field}: No selector found")
        
        return selectors
    
    def _find_field_selector(
        self,
        container: Tag,
        field: str,
        base_selector: str
    ) -> Optional[str]:
        """
        Find CSS selector for a specific field within container
        Uses semantic analysis of tag names and class attributes
        """
        keywords = self.field_keywords.get(field, [field])
        
        # Special handling for different field types
        if field in ['image', 'img']:
            img = container.find('img')
            if img:
                if img.get('class'):
                    classes = '.'.join(img.get('class'))
                    return f"{base_selector} img.{classes}"
                return f"{base_selector} img"
        
        if field in ['url', 'link']:
            link = container.find('a', href=True)
            if link:
                if link.get('class'):
                    classes = '.'.join(link.get('class'))
                    return f"{base_selector} a.{classes}"
                return f"{base_selector} a"
        
        # For text fields, search by semantic clues
        candidates = []
        
        # Search all descendants (limit depth to avoid too nested elements)
        for element in container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'p', 'a'], recursive=True):
            if not isinstance(element, Tag):
                continue
            
            # Skip if element is too deep (more than 5 levels)
            depth = len(list(element.parents))
            if depth > 10:
                continue
            
            # Get element text (skip if empty or too long)
            text = element.get_text(strip=True)
            if not text or len(text) > 500:  # Skip very long text
                continue
            
            # Check classes for semantic matches
            classes = element.get('class', [])
            class_str = ' '.join(classes).lower()
            
            score = 0
            
            # Check if any keyword matches in class name
            for keyword in keywords:
                if keyword in class_str:
                    score = 10  # High score for class match
                    break
            
            # Check tag name for semantic matches
            if field in ['title', 'name']:
                if element.name in ['h1', 'h2', 'h3', 'h4']:
                    score = max(score, 9)
                elif element.name == 'a' and element.get('href'):
                    score = max(score, 7)
            
            # Check for price patterns in text
            if field == 'price':
                if re.search(r'[\$€£₹]\s*\d+|price|₹\d+', text, re.IGNORECASE):
                    score = max(score, 9)
                # Check for numeric patterns
                if re.search(r'\d+[,.]?\d*', text):
                    score = max(score, 5)
            
            # Check for author patterns
            if field == 'author':
                if re.search(r'by\s+\w+|author', text, re.IGNORECASE):
                    score = max(score, 8)
            
            # Check for date patterns
            if field == 'date':
                if re.search(r'\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}\s+\w+\s+\d{4}', text):
                    score = max(score, 9)
            
            # Bonus for having data attributes
            if element.get('data-price') or element.get('data-title'):
                score += 5
            
            # Penalize very short text (likely not the main content)
            if len(text) < 3:
                score *= 0.5
            
            # Penalize elements with too many children (likely containers)
            if len(list(element.children)) > 5:
                score *= 0.7
            
            if score > 0:
                candidates.append((score, element, text))
        
        # Select best candidate
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_element = candidates[0][1]
            
            logger.debug(f"  Best candidate for {field}: score={candidates[0][0]}, text='{candidates[0][2][:50]}'")
            
            # Generate selector
            if best_element.get('class'):
                classes = '.'.join(best_element.get('class'))
                return f"{base_selector} {best_element.name}.{classes}"
            else:
                return f"{base_selector} {best_element.name}"
        
        return None
    
    def _extract_with_selectors(
        self,
        soup: BeautifulSoup,
        pattern: Dict,
        selectors: Dict[str, str],
        quantity: int
    ) -> List[Dict]:
        """
        Extract data using generated selectors
        """
        logger.info(f"📦 Extracting data with selectors...")
        
        items = []
        containers = soup.select(pattern['selector'])[:quantity]
        
        logger.info(f"Found {len(containers)} containers matching {pattern['selector']}")
        
        for i, container in enumerate(containers, 1):
            item = {}
            
            for field, selector in selectors.items():
                # Extract relative to container
                # Remove base selector to make it relative
                relative_selector = selector.replace(pattern['selector'], '').strip()
                if relative_selector.startswith('>'):
                    relative_selector = relative_selector[1:].strip()
                
                try:
                    if field in ['image', 'img']:
                        element = container.select_one(relative_selector)
                        if element:
                            value = element.get('src') or element.get('data-src')
                    elif field in ['url', 'link']:
                        element = container.select_one(relative_selector)
                        if element:
                            value = element.get('href')
                    else:
                        element = container.select_one(relative_selector)
                        if element:
                            value = element.get_text().strip()
                    
                    if value:
                        item[field] = value
                
                except Exception as e:
                    logger.debug(f"Failed to extract {field}: {e}")
                    continue
            
            if len(item) >= 2:  # At least 2 fields
                items.append(item)
                logger.info(f"  ✅ Item {i}: {list(item.keys())}")
        
        return items


def main():
    """Test DOM analyzer"""
    analyzer = DOMAnalyzer()
    
    # Test HTML
    html = """
    <div class="products">
        <div class="product-card">
            <h2 class="product-title">Laptop</h2>
            <span class="price">$999</span>
            <img src="laptop.jpg" class="product-image">
            <a href="/laptop" class="product-link">View</a>
        </div>
        <div class="product-card">
            <h2 class="product-title">Mouse</h2>
            <span class="price">$29</span>
            <img src="mouse.jpg" class="product-image">
            <a href="/mouse" class="product-link">View</a>
        </div>
        <div class="product-card">
            <h2 class="product-title">Keyboard</h2>
            <span class="price">$79</span>
            <img src="keyboard.jpg" class="product-image">
            <a href="/keyboard" class="product-link">View</a>
        </div>
    </div>
    """
    
    selectors, items = analyzer.analyze_and_extract(
        html=html,
        content_type='products',
        fields=['title', 'price', 'image', 'url'],
        quantity=10
    )
    
    print("\n" + "="*70)
    print("GENERATED SELECTORS")
    print("="*70)
    for field, selector in selectors.items():
        print(f"{field}: {selector}")
    
    print("\n" + "="*70)
    print("EXTRACTED ITEMS")
    print("="*70)
    for i, item in enumerate(items, 1):
        print(f"\n{i}. {item}")


if __name__ == "__main__":
    main()
