"""
LLM Reasoning Agent - The Brain of the Scraper
Plans actions, makes decisions, interprets results, and adapts strategy
"""

import os
import json
import re
from typing import Dict, List, Optional
from openai import OpenAI
from logger import setup_logger

logger = setup_logger(__name__)


class ReasoningAgent:
    """
    The intelligent brain that:
    1. Understands user goals
    2. Plans extraction strategy
    3. Decides what fields to extract
    4. Interprets results
    5. Adapts approach based on feedback
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "openai/gpt-3.5-turbo"):
        """Initialize reasoning agent"""
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        logger.info(f"🧠 ReasoningAgent initialized with model: {model}")
    
    def plan_extraction(self, prompt: str, content_type: str) -> Dict:
        """
        Plan the extraction strategy based on user goal
        
        Returns:
            {
                'mandatory_fields': ['title', 'description', 'content', 'source_url'],
                'optional_fields': ['author', 'date'],
                'content_extraction': 'full_text|summary|metadata',
                'reasoning': 'why this strategy',
                'search_needed': True/False
            }
        """
        logger.info(f"🧠 Planning extraction strategy for: {prompt}")
        
        system_prompt = """You are an intelligent scraping agent. Analyze the user's goal and plan the extraction strategy.

MANDATORY FIELDS (always extract):
- title: headline/name (article title, product name, movie name, blog heading)
- description: brief summary or excerpt
- content: FULL content (complete blog text, full article, full review, etc.)
- source_url: where the data came from

CONTEXT-AWARE CONTENT:
- Blog → Extract full blog post text
- Article → Extract complete article body
- News → Extract full news story
- Product → Extract full product description
- Movie → Extract plot summary and details
- Review → Extract complete review text

Return JSON:
{
  "mandatory_fields": ["title", "description", "content", "source_url"],
  "optional_fields": ["author", "date", "rating"],
  "content_extraction": "full_text",
  "reasoning": "User wants blogs, so extract complete blog posts",
  "search_needed": true
}"""
        
        user_message = f"""User goal: "{prompt}"
Content type: {content_type}

Plan the extraction strategy. What fields should we extract? What content depth?"""
        
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
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                plan = json.loads(json_match.group())
                logger.info(f"✅ Strategy: {plan['reasoning']}")
                return plan
            
        except Exception as e:
            logger.warning(f"Planning failed: {e}, using default")
        
        # Default plan
        return {
            'mandatory_fields': ['title', 'description', 'content', 'source_url'],
            'optional_fields': ['author', 'date'],
            'content_extraction': 'full_text',
            'reasoning': 'Default comprehensive extraction',
            'search_needed': True
        }

    def interpret_results(
        self,
        prompt: str,
        items: List[Dict],
        plan: Dict
    ) -> Dict:
        """
        Interpret extraction results and decide next action
        
        Returns:
            {
                'quality': 'good|poor|failed',
                'issues': ['missing content', 'no descriptions'],
                'next_action': 'continue|retry|adjust',
                'reasoning': 'why this decision'
            }
        """
        logger.info(f"🧠 Interpreting results: {len(items)} items extracted")
        
        # Quick analysis
        if not items:
            return {
                'quality': 'failed',
                'issues': ['no items extracted'],
                'next_action': 'retry',
                'reasoning': 'No data extracted, need different approach'
            }
        
        # Check mandatory fields
        mandatory = plan.get('mandatory_fields', [])
        issues = []
        
        for field in mandatory:
            missing_count = sum(1 for item in items if not item.get(field))
            if missing_count > len(items) * 0.5:  # More than 50% missing
                issues.append(f'{field} missing in {missing_count}/{len(items)} items')
        
        # Determine quality
        if not issues:
            quality = 'good'
            next_action = 'continue'
            reasoning = 'All mandatory fields present, good quality data'
        elif len(issues) <= 2:
            quality = 'poor'
            next_action = 'continue'
            reasoning = 'Some fields missing but usable data'
        else:
            quality = 'failed'
            next_action = 'retry'
            reasoning = 'Too many missing fields, need better extraction'
        
        logger.info(f"📊 Quality: {quality}, Action: {next_action}")
        
        return {
            'quality': quality,
            'issues': issues,
            'next_action': next_action,
            'reasoning': reasoning
        }
    
    def decide_search_query(self, prompt: str) -> str:
        """
        Extract search query by removing ONLY scraping words
        Keep everything else exactly as user typed
        """
        logger.info(f"🧠 Deciding search query for: {prompt}")
        
        # Simple approach: Remove only scraping words
        scraping_words = [
            r'\bscrape\b', r'\bscrap\b', r'\bscraping\b',
            r'\bextract\b', r'\bextracting\b',
            r'\bget\b', r'\bgetting\b',
            r'\bfetch\b', r'\bfind\b',
            r'\bcollect\b', r'\bgrab\b',
            r'\bpull\b', r'\bretrieve\b'
        ]
        
        cleaned = prompt
        for word_pattern in scraping_words:
            cleaned = re.sub(word_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        query = cleaned if cleaned else prompt
        logger.info(f"🔍 Search query: {query}")
        return query

