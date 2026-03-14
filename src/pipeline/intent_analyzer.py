"""
Step 1: Intent Understanding
Analyzes user prompt to determine what to scrape and which fields are needed
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import openai

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    DEFAULT_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS
)
from logger import setup_logger, log_step


logger = setup_logger(__name__)


@dataclass
class ScrapingIntent:
    """Structured intent from user prompt"""
    content_type: str  # products, articles, reviews, images, etc.
    fields: List[str]  # Fields to extract
    quantity: int  # Number of items
    filters: List[str]  # Any filters (price, date, etc.)
    reasoning: str  # Why these fields were chosen
    
    def to_dict(self) -> dict:
        return {
            "content_type": self.content_type,
            "fields": self.fields,
            "quantity": self.quantity,
            "filters": self.filters,
            "reasoning": self.reasoning
        }


class IntentAnalyzer:
    """Analyzes user prompts to understand scraping intent"""
    
    def __init__(self):
        """Initialize OpenRouter client"""
        self.client = openai.OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL
        )
        logger.info("IntentAnalyzer initialized with OpenRouter")
    
    def analyze(self, user_prompt: str) -> Optional[ScrapingIntent]:
        """
        Analyze user prompt to extract intent
        
        Args:
            user_prompt: Natural language request from user
        
        Returns:
            ScrapingIntent object or None if analysis fails
        """
        log_step(logger, "Intent Analysis", "STARTED", {"prompt": user_prompt})
        
        try:
            # Create prompt for LLM
            system_prompt = self._create_system_prompt()
            user_message = self._create_user_message(user_prompt)
            
            logger.debug(f"Calling OpenRouter with model: {DEFAULT_MODEL}")
            
            # Call OpenRouter
            response = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            # Extract response
            content = response.choices[0].message.content
            logger.debug(f"LLM Response: {content[:200]}...")
            
            # Parse JSON
            intent_data = json.loads(content)
            
            # Validate and create intent object
            intent = self._validate_and_create_intent(intent_data)
            
            if intent:
                log_step(logger, "Intent Analysis", "SUCCESS", intent.to_dict())
                return intent
            else:
                log_step(logger, "Intent Analysis", "FAILED", {"reason": "Invalid intent data"})
                return None
        
        except json.JSONDecodeError as e:
            log_step(logger, "Intent Analysis", "FAILED", {"error": f"JSON parse error: {e}"})
            logger.error(f"Failed to parse JSON: {content}")
            return self._default_intent(user_prompt)
        
        except Exception as e:
            log_step(logger, "Intent Analysis", "FAILED", {"error": str(e)})
            logger.exception("Unexpected error in intent analysis")
            return self._default_intent(user_prompt)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for intent understanding"""
        return """You are an expert at understanding web scraping requests.

Your task: Analyze the user's request and determine:
1. What type of content they want to scrape
2. Which fields are relevant for that content type
3. How many items they want
4. Any filters or constraints

CONTENT TYPES & TYPICAL FIELDS:
- products: name, url (or name, price, url if price mentioned)
- articles: title, url (or title, content, author, date if detailed)
- reviews: text, rating, reviewer (or text, rating, date)
- images: url, caption, alt_text
- videos: title, url, duration, thumbnail

RULES:
1. Choose minimal fields - only what user needs
2. Always include 'url' or 'link' field
3. If user says "scrape products", they likely just need name + url
4. If user says "scrape articles with authors", add author field
5. Default quantity is 10 if not specified

Return ONLY valid JSON with this exact structure:
{
  "content_type": "products|articles|reviews|images|videos",
  "fields": ["field1", "field2"],
  "quantity": 10,
  "filters": ["filter1", "filter2"],
  "reasoning": "Brief explanation of field choices"
}"""
    
    def _create_user_message(self, user_prompt: str) -> str:
        """Create user message with examples"""
        return f"""Analyze this scraping request:

"{user_prompt}"

Examples for reference:

Request: "scrape 5 headsets from amazon"
Response: {{"content_type": "products", "fields": ["name", "url"], "quantity": 5, "filters": [], "reasoning": "Products need name to identify and url to access. No price mentioned so not included."}}

Request: "get 10 tech news articles with authors"
Response: {{"content_type": "articles", "fields": ["title", "author", "url"], "quantity": 10, "filters": [], "reasoning": "Articles need title and url. Author explicitly requested."}}

Request: "scrape product reviews with ratings"
Response: {{"content_type": "reviews", "fields": ["text", "rating", "reviewer"], "quantity": 10, "filters": [], "reasoning": "Reviews need text content and rating. Reviewer helps identify source."}}

Now analyze the user's request and return JSON:"""
    
    def _default_intent(self, user_prompt: str) -> 'ScrapingIntent':
        """Return a sensible default intent when AI analysis fails."""
        import re
        # Try to extract a quantity from the prompt (e.g. "top 10", "5 articles")
        match = re.search(r'\b(\d+)\b', user_prompt)
        quantity = int(match.group(1)) if match else 10

        logger.warning(f"⚠️ Using default intent (quantity={quantity})")
        return ScrapingIntent(
            content_type="articles",
            fields=["title", "description", "content", "source_url"],
            quantity=quantity,
            filters=[],
            reasoning="Default intent — AI analysis unavailable"
        )

    def _validate_and_create_intent(self, data: dict) -> 'ScrapingIntent':
        """
        Validate intent data and create ScrapingIntent object
        
        Args:
            data: Parsed JSON from LLM
        
        Returns:
            ScrapingIntent object or None if invalid
        """
        try:
            # Required fields
            content_type = data.get("content_type")
            fields = data.get("fields", [])
            quantity = data.get("quantity", 10)
            filters = data.get("filters", [])
            reasoning = data.get("reasoning", "")
            
            # Validation
            if not content_type:
                logger.error("Missing content_type in intent")
                return self._default_intent("")
            
            if not fields or not isinstance(fields, list):
                logger.error("Missing or invalid fields in intent")
                return self._default_intent("")
            
            if not isinstance(quantity, int) or quantity <= 0:
                logger.warning(f"Invalid quantity {quantity}, using default 10")
                quantity = 10
            
            # Create intent
            intent = ScrapingIntent(
                content_type=content_type,
                fields=fields,
                quantity=quantity,
                filters=filters if isinstance(filters, list) else [],
                reasoning=reasoning
            )
            
            logger.info(f"Created intent: {content_type} with fields {fields}")
            return intent
        
        except Exception as e:
            logger.error(f"Failed to validate intent: {e}")
            return self._default_intent("")
