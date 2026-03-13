"""
Data cleaning and validation module
Cleans extracted data and ensures quality
"""

import re
import html
from typing import List, Dict, Any
from logger import setup_logger, log_step

logger = setup_logger(__name__)


class DataCleaner:
    """
    Cleans and validates extracted data
    """
    
    def __init__(self):
        """Initialize data cleaner"""
        logger.info("DataCleaner initialized")
    
    def clean(self, items: List[Dict], fields: List[str]) -> List[Dict]:
        """
        Clean list of items
        
        Args:
            items: List of extracted items
            fields: Expected fields
        
        Returns:
            List of cleaned items
        """
        logger.info(f"🧹 Cleaning {len(items)} items...")
        
        cleaned_items = []
        
        for i, item in enumerate(items, 1):
            cleaned_item = self._clean_item(item, fields)
            
            # Only keep items with at least one non-empty field
            if self._is_valid_item(cleaned_item):
                cleaned_items.append(cleaned_item)
                logger.debug(f"✅ Cleaned item {i}")
            else:
                logger.debug(f"❌ Skipped empty item {i}")
        
        logger.info(f"🧹 Cleaned {len(cleaned_items)}/{len(items)} items")
        
        log_step(logger, "Data Cleaning", "SUCCESS", {
            'items_cleaned': len(cleaned_items),
            'items_removed': len(items) - len(cleaned_items)
        })
        
        return cleaned_items
    
    def _clean_item(self, item: Dict, fields: List[str]) -> Dict:
        """Clean a single item"""
        cleaned = {}
        
        for field in fields:
            value = item.get(field)
            
            if value is None:
                cleaned[field] = None
            elif isinstance(value, str):
                cleaned[field] = self._clean_text(value)
            elif isinstance(value, (int, float)):
                cleaned[field] = value
            else:
                cleaned[field] = str(value)
        
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text content
        
        Args:
            text: Raw text
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        return text
    
    def _is_valid_item(self, item: Dict) -> bool:
        """
        Check if item has at least one non-empty field
        
        Args:
            item: Item to validate
        
        Returns:
            True if valid, False otherwise
        """
        for value in item.values():
            if value and str(value).strip():
                return True
        return False
    
    def validate_fields(self, items: List[Dict], required_fields: List[str]) -> List[Dict]:
        """
        Validate that items have required fields
        
        Args:
            items: List of items
            required_fields: Fields that must be present
        
        Returns:
            List of valid items
        """
        logger.info(f"✅ Validating {len(items)} items for required fields: {required_fields}")
        
        valid_items = []
        
        for i, item in enumerate(items, 1):
            has_all_fields = all(
                field in item and item[field] and str(item[field]).strip()
                for field in required_fields
            )
            
            if has_all_fields:
                valid_items.append(item)
                logger.debug(f"✅ Item {i} is valid")
            else:
                missing = [f for f in required_fields if not item.get(f)]
                logger.debug(f"❌ Item {i} missing: {missing}")
        
        logger.info(f"✅ {len(valid_items)}/{len(items)} items are valid")
        
        return valid_items
    
    def deduplicate(self, items: List[Dict], key_field: str = 'url') -> List[Dict]:
        """
        Remove duplicate items based on a key field
        
        Args:
            items: List of items
            key_field: Field to use for deduplication
        
        Returns:
            List of unique items
        """
        logger.info(f"🔄 Deduplicating {len(items)} items by '{key_field}'...")
        
        seen = set()
        unique_items = []
        
        for item in items:
            key = item.get(key_field)
            
            if key and key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        removed = len(items) - len(unique_items)
        logger.info(f"🔄 Removed {removed} duplicates, {len(unique_items)} unique items remain")
        
        return unique_items
