"""
Vision-based CSS selector generation
Uses vision AI to analyze screenshots and generate CSS selectors
"""

import base64
import json
from typing import Dict, List, Optional
from pathlib import Path
import openai

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS
)
from logger import setup_logger, log_step

logger = setup_logger(__name__)


class VisionSelectorGenerator:
    """
    Generates CSS selectors by analyzing page screenshots with vision AI
    """
    
    # Vision-capable models on OpenRouter
    VISION_MODELS = [
        "openai/gpt-4o",  # Best quality
        "anthropic/claude-3.5-sonnet",  # Good alternative
        "google/gemini-pro-vision"  # Budget option
    ]
    
    def __init__(self, model: str = "openai/gpt-4o"):
        """
        Initialize vision selector generator
        
        Args:
            model: Vision-capable model to use
        """
        self.client = openai.OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL
        )
        self.model = model
        logger.info(f"VisionSelectorGenerator initialized with model: {model}")
    
    def generate_selectors(
        self,
        screenshot_path: str,
        content_type: str,
        fields: List[str],
        html_sample: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Generate CSS selectors by analyzing screenshot
        
        Args:
            screenshot_path: Path to screenshot image
            content_type: Type of content (products, articles, reviews)
            fields: Fields to extract
            html_sample: Optional HTML sample for context
        
        Returns:
            Dictionary with container and field selectors
        """
        logger.info(f"🔍 Generating selectors for {content_type} using vision AI...")
        log_step(logger, "Vision Selector Generation", "STARTED", {
            'content_type': content_type,
            'fields': fields
        })
        
        try:
            # Encode image
            image_data = self._encode_image(screenshot_path)
            
            # Create prompt
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(content_type, fields, html_sample)
            
            # Call vision API
            logger.info(f"📸 Analyzing screenshot with {self.model}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            selectors = json.loads(content)
            
            logger.info(f"✅ Generated selectors:")
            logger.info(f"   Container: {selectors.get('container', 'N/A')}")
            logger.info(f"   Fields: {list(selectors.get('selectors', {}).keys())}")
            
            log_step(logger, "Vision Selector Generation", "SUCCESS", {
                'container': selectors.get('container'),
                'field_count': len(selectors.get('selectors', {}))
            })
            
            return selectors
            
        except Exception as e:
            logger.error(f"❌ Vision selector generation failed: {e}")
            log_step(logger, "Vision Selector Generation", "FAILED", {'error': str(e)})
            return None
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for vision AI"""
        return """You are an expert at analyzing web pages and generating CSS selectors.

Your task: Look at the screenshot and identify the repeating elements (products, articles, reviews, etc.) and generate CSS selectors to extract them.

RULES:
1. Identify the container element that wraps each item
2. For each field, provide a CSS selector relative to the container
3. Use specific, robust selectors (prefer classes over generic tags)
4. Use ::text for text content, ::attr(href) for links, ::attr(src) for images
5. Test mentally if the selector would work on similar pages

Return ONLY valid JSON with this structure:
{
  "container": "div.product-card",
  "selectors": {
    "title": "h2.product-title::text",
    "price": "span.price::text",
    "url": "a.product-link::attr(href)",
    "image": "img.product-image::attr(src)"
  },
  "reasoning": "Brief explanation of selector choices"
}"""
    
    def _create_user_prompt(
        self,
        content_type: str,
        fields: List[str],
        html_sample: Optional[str]
    ) -> str:
        """Create user prompt with context"""
        prompt = f"""Analyze this screenshot and generate CSS selectors.

Content Type: {content_type}
Fields to Extract: {', '.join(fields)}

Look for repeating {content_type} on the page and identify:
1. The container element that wraps each {content_type[:-1] if content_type.endswith('s') else content_type}
2. Selectors for each field: {', '.join(fields)}

"""
        
        if html_sample:
            prompt += f"""
HTML Sample (for reference):
```html
{html_sample[:500]}...
```

"""
        
        prompt += """Generate robust CSS selectors that will work reliably.
Return JSON with container and field selectors."""
        
        return prompt


class VisionEnhancedScraper:
    """
    Wrapper that adds vision capabilities to existing scrapers
    """
    
    def __init__(self, base_scraper, vision_model: str = "openai/gpt-4o"):
        """
        Initialize vision-enhanced scraper
        
        Args:
            base_scraper: Playwright or Scrapy scraper instance
            vision_model: Vision model to use
        """
        self.base_scraper = base_scraper
        self.vision_generator = VisionSelectorGenerator(model=vision_model)
        logger.info("VisionEnhancedScraper initialized")
    
    def scrape_with_vision(
        self,
        url: str,
        content_type: str,
        fields: List[str],
        quantity: int = 10,
        screenshot_path: Optional[str] = None
    ) -> List[Dict]:
        """
        Scrape using vision-generated selectors
        
        Args:
            url: URL to scrape
            content_type: Type of content
            fields: Fields to extract
            quantity: Number of items
            screenshot_path: Optional screenshot path (will capture if not provided)
        
        Returns:
            List of extracted items
        """
        logger.info(f"🎯 Starting vision-enhanced scraping for {url}")
        
        try:
            # Capture screenshot if needed
            if not screenshot_path:
                screenshot_path = self._capture_screenshot(url)
            
            # Get HTML sample for context
            html_sample = self._get_html_sample(url)
            
            # Generate selectors using vision
            selectors = self.vision_generator.generate_selectors(
                screenshot_path=screenshot_path,
                content_type=content_type,
                fields=fields,
                html_sample=html_sample
            )
            
            if not selectors:
                logger.warning("Vision selector generation failed, falling back to heuristics")
                return self.base_scraper.scrape(
                    url=url,
                    content_type=content_type,
                    fields=fields,
                    quantity=quantity
                )
            
            # Scrape using generated selectors
            logger.info("📦 Scraping with vision-generated selectors...")
            items = self.base_scraper.scrape(
                url=url,
                content_type=content_type,
                fields=fields,
                quantity=quantity,
                selectors=selectors
            )
            
            logger.info(f"✅ Vision-enhanced scraping extracted {len(items)} items")
            return items
            
        except Exception as e:
            logger.error(f"❌ Vision-enhanced scraping failed: {e}")
            logger.exception("Full error:")
            return []
    
    def _capture_screenshot(self, url: str) -> str:
        """Capture screenshot of page"""
        # This assumes base_scraper is PlaywrightScraper
        # For ScrapyScraper, we'd need to use Playwright separately
        screenshot_path = "temp_screenshot.png"
        
        if hasattr(self.base_scraper, 'capture_screenshot'):
            self.base_scraper.capture_screenshot(url, screenshot_path)
        else:
            # Fallback: use Playwright directly
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)
                page.screenshot(path=screenshot_path, full_page=True)
                browser.close()
        
        return screenshot_path
    
    def _get_html_sample(self, url: str) -> str:
        """Get HTML sample for context"""
        try:
            import requests
            response = requests.get(url, timeout=10)
            return response.text[:1000]  # First 1000 chars
        except:
            return ""
