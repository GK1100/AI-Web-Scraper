"""
Configuration for AI Web Scraper
"""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection with fallback
# Using OpenRouter with correct model names
# Primary: GPT-3.5 Turbo (fast, reliable, works with OpenRouter)
# Fallback: GPT-3.5 Turbo (same model for consistency)
PRIMARY_MODEL = "openai/gpt-3.5-turbo"
FALLBACK_MODEL = "openai/gpt-3.5-turbo"
DEFAULT_MODEL = PRIMARY_MODEL

# LLM Settings
LLM_TEMPERATURE = 0.1  # Low for consistent JSON output
LLM_MAX_TOKENS = 1000
LLM_TIMEOUT = 30

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/scraper.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Paths
OUTPUT_DIR = "output"
CACHE_DIR = "cache"
