"""
AI-Powered Intelligent Data Cleaner
Uses LLM to understand user intent and clean data dynamically
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from logger import setup_logger, log_step

logger = setup_logger(__name__)


class IntelligentCleaner:
    """
    AI-powered data cleaner that understands user intent
    and dynamically validates/cleans data based on context
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "openai/gpt-3.5-turbo"):
        """
        Initialize intelligent cleaner
        
        Args:
            api_key: OpenRouter API key (or from env)
            model: Model to use for cleaning decisions
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        logger.info(f"IntelligentCleaner initialized with model: {model}")
    
    def intelligent_clean(
        self,
        items: List[Dict],
        prompt: str,
        content_type: str,
        fields: List[str]
    ) -> List[Dict]:
        """
        Clean and validate items using AI understanding
        
        Args:
            items: Raw extracted items
            prompt: Original user prompt
            content_type: Type of content (products, articles, etc.)
            fields: Expected fields
        
        Returns:
            List of cleaned and validated items
        """
        if not items:
            return []
        
        logger.info(f"🤖 AI-powered cleaning of {len(items)} items...")
        logger.info(f"📝 User prompt: {prompt}")
        logger.info(f"📊 Content type: {content_type}")
        
        # Step 1: Analyze user intent and create cleaning strategy
        strategy = self._create_cleaning_strategy(prompt, content_type, fields, items[:3])
        
        logger.info(f"🎯 Cleaning strategy: {strategy['approach']}")
        logger.info(f"🔍 Required fields: {strategy['required_fields']}")
        logger.info(f"📏 Quality threshold: {strategy['quality_threshold']}")
        
        # Step 2: Clean each item
        cleaned_items = []
        for i, item in enumerate(items, 1):
            cleaned_item = self._clean_item_intelligent(item, strategy, fields)
            
            # Step 3: Validate item based on strategy
            if self._validate_item_intelligent(cleaned_item, strategy, prompt):
                cleaned_items.append(cleaned_item)
                logger.debug(f"✅ Item {i} passed AI validation")
            else:
                logger.debug(f"❌ Item {i} failed AI validation")
        
        logger.info(f"✅ {len(cleaned_items)}/{len(items)} items passed AI validation")
        
        return cleaned_items

    def _create_cleaning_strategy(
        self,
        prompt: str,
        content_type: str,
        fields: List[str],
        sample_items: List[Dict]
    ) -> Dict:
        """
        Use AI to create a cleaning strategy based on user intent
        """
        system_prompt = """You are a data quality expert. Analyze the user's scraping request and create a cleaning strategy.

Your task:
1. Understand what the user REALLY wants
2. Determine which fields are truly required vs optional
3. Set appropriate quality thresholds
4. Decide validation approach

Return JSON with:
{
  "approach": "strict|lenient|flexible",
  "required_fields": ["field1", "field2"],
  "optional_fields": ["field3"],
  "quality_threshold": "high|medium|low",
  "reasoning": "why this strategy"
}"""
        
        user_message = f"""User prompt: "{prompt}"
Content type: {content_type}
Expected fields: {fields}

Sample items (first 3):
{json.dumps(sample_items, indent=2)}

What cleaning strategy should we use?"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                strategy = json.loads(json_match.group())
                logger.info(f"🤖 AI Strategy: {strategy['reasoning']}")
                return strategy
            
        except Exception as e:
            logger.warning(f"AI strategy creation failed: {e}, using default")
        
        # Default strategy
        return {
            "approach": "flexible",
            "required_fields": fields[:2] if len(fields) >= 2 else fields,
            "optional_fields": fields[2:] if len(fields) > 2 else [],
            "quality_threshold": "medium",
            "reasoning": "Default strategy"
        }

    def _clean_item_intelligent(
        self,
        item: Dict,
        strategy: Dict,
        fields: List[str]
    ) -> Dict:
        """
        Clean item based on AI strategy
        """
        cleaned = {}
        
        for field in fields:
            value = item.get(field)
            
            if value is None:
                cleaned[field] = None
            elif isinstance(value, str):
                # Clean text
                value = self._clean_text(value)
                
                # AI-powered field-specific cleaning
                if field == 'price':
                    value = self._clean_price(value)
                elif field in ['url', 'link']:
                    value = self._clean_url(value)
                elif field == 'date':
                    value = self._clean_date(value)
                
                cleaned[field] = value
            else:
                cleaned[field] = value
        
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """Clean text content"""
        if not text:
            return ""
        
        import html
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        text = text.replace('\x00', '')
        
        # Remove very long text (likely page content, not field value)
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        return text

    def _clean_price(self, price: str) -> str:
        """Extract clean price from text"""
        if not price:
            return ""
        
        # Extract price patterns
        patterns = [
            r'₹\s*[\d,]+(?:\.\d{2})?',
            r'\$\s*[\d,]+(?:\.\d{2})?',
            r'€\s*[\d,]+(?:\.\d{2})?',
            r'£\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:₹|\$|€|£)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, price)
            if match:
                return match.group().strip()
        
        # Just numbers
        match = re.search(r'[\d,]+(?:\.\d{2})?', price)
        if match:
            return match.group().strip()
        
        return price
    
    def _clean_url(self, url: str) -> str:
        """Clean and validate URL"""
        if not url or url == '/':
            return ""
        
        url = url.strip()
        
        # Make relative URLs absolute (basic)
        if url.startswith('/') and len(url) > 1:
            return url  # Keep relative URL
        
        return url
    
    def _clean_date(self, date: str) -> str:
        """Clean date string"""
        if not date:
            return ""
        return date.strip()

    def _validate_item_intelligent(
        self,
        item: Dict,
        strategy: Dict,
        prompt: str
    ) -> bool:
        """
        Validate item based on AI strategy
        
        Args:
            item: Cleaned item
            strategy: AI-generated strategy
            prompt: Original user prompt
        
        Returns:
            True if item passes validation
        """
        approach = strategy.get('approach', 'flexible')
        required_fields = strategy.get('required_fields', [])
        optional_fields = strategy.get('optional_fields', [])
        
        # Check required fields
        if approach == 'strict':
            # ALL required fields must be present and non-empty
            for field in required_fields:
                value = item.get(field)
                if not value or not str(value).strip() or str(value).strip() == '/':
                    return False
        
        elif approach == 'lenient':
            # At least ONE required field must be present
            has_any = any(
                item.get(field) and str(item.get(field)).strip() and str(item.get(field)).strip() != '/'
                for field in required_fields
            )
            if not has_any:
                return False
        
        else:  # flexible (default)
            # At least 50% of required fields must be present
            valid_count = sum(
                1 for field in required_fields
                if item.get(field) and str(item.get(field)).strip() and str(item.get(field)).strip() != '/'
            )
            required_count = len(required_fields)
            if required_count > 0 and valid_count / required_count < 0.5:
                return False
        
        # Check if item has at least SOME useful data
        all_fields = required_fields + optional_fields
        has_useful_data = any(
            item.get(field) and str(item.get(field)).strip() and len(str(item.get(field)).strip()) > 2
            for field in all_fields
        )
        
        return has_useful_data
