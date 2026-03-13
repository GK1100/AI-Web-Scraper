# AI Web Scraper

An AI-powered web scraping system that understands natural language prompts, automatically searches for content, visits websites, skips login/paywalled pages, and extracts structured data.

No URL needed — just describe what you want.

---

## How it works

1. You enter a natural language prompt (e.g. `top 10 blogs on digital marketing`)
2. The AI analyzes intent — content type, fields, quantity
3. DuckDuckGo (or Google fallback) searches for relevant URLs
4. All URLs saved to `load_url.json`, top 3 to a text file
5. Playwright visits each URL, skips login/paywall/403 pages
6. Full content extracted from valid pages
7. AI cleans and validates the data
8. Results saved as JSON/CSV/Excel + displayed in UI

---

## Project Structure

```
src/
├── app.py                  ← Streamlit web UI
├── scrape.py               ← CLI entry point
├── config.py               ← Settings & API keys
├── logger.py               ← Logging setup
├── agents/
│   ├── simple_search_agent.py   ← DuckDuckGo + Google search
│   ├── smart_url_visitor.py     ← Visits URLs, skips login pages
│   ├── url_generator.py         ← URL generation fallback
│   └── google_search_agent.py   ← Google search agent
├── pipeline/
│   ├── main_scraper.py          ← Orchestrates all steps
│   ├── intent_analyzer.py       ← Parses user prompt with AI
│   ├── reasoning_agent.py       ← AI planning agent
│   ├── intelligent_cleaner.py   ← AI data validation
│   ├── data_cleaner.py          ← Rule-based cleaning
│   └── data_storage.py          ← Saves output files
├── extractors/
│   ├── full_content_extractor.py ← Main HTML content extractor
│   ├── universal_extractor.py    ← Multi-strategy extractor
│   ├── heuristic_extractor.py    ← Pattern-based extraction
│   ├── dom_analyzer.py           ← DOM structure analysis
│   └── vision_selector.py        ← GPT-4o vision CSS selectors
├── scrapers/
│   ├── playwright_scraper.py     ← JS-rendered pages
│   ├── scrapy_scraper.py         ← Fast static pages
│   └── site_detector.py          ← Chooses scraper per site
├── logs/                   ← scraper.log (gitignored)
├── debug/                  ← Raw HTML debug dumps (gitignored)
└── output/                 ← Scraped results (gitignored)
```

---

## Setup

```bash
# 1. Clone and install dependencies
pip install -r src/requirements.txt
playwright install chromium

# 2. Configure API key
cp src/.env.example src/.env
# Edit src/.env and set your OpenRouter API key
# Get one free at: https://openrouter.ai/keys
```

---

## Usage

### Streamlit UI

```bash
streamlit run src/app.py
```

Opens at `http://localhost:8501` — enter your prompt, adjust settings in the sidebar, click Start Scraping.

### CLI — Interactive

```bash
python src/scrape.py
```

### CLI — Arguments

```bash
# Auto-search (no URL needed)
python src/scrape.py --prompt "top 10 email marketing platforms"

# With a specific URL
python src/scrape.py --prompt "scrape 5 articles" --url "https://news.ycombinator.com"

# Save as CSV
python src/scrape.py --prompt "best laptops under 50000" --format csv

# Enable Vision AI (uses GPT-4o for CSS selector generation)
python src/scrape.py --prompt "scrape products" --url "https://example.com" --vision
```

### Python API

```python
import sys
sys.path.insert(0, "src")
from pipeline.main_scraper import WebScraper

scraper = WebScraper(use_intelligent_cleaning=True)
result = scraper.scrape(prompt="top 5 blogs on machine learning")

for item in result["items"]:
    print(item["title"], item["source_url"])
```

---

## Output

Each run saves two versions:

- `*_raw.*` — data as extracted, before any cleaning
- `*_cleaned.*` — validated and cleaned by AI

Supported formats: `json`, `csv`, `excel`, `yaml`, `sqlite`, `all`

All files go to `src/output/`.

---

## Environment Variables

```env
OPENROUTER_API_KEY=sk-or-v1-...   # Required — get from openrouter.ai/keys
```

Model used: `openai/gpt-3.5-turbo` via OpenRouter.

---

## Tech Stack

- Python 3.10+
- [LangGraph](https://github.com/langchain-ai/langgraph) — agent orchestration
- [Playwright](https://playwright.dev/python/) — JS rendering & URL visiting
- [Scrapy](https://scrapy.org/) — fast static scraping
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing
- [OpenRouter](https://openrouter.ai/) — LLM API (GPT-3.5-Turbo)
- [Streamlit](https://streamlit.io/) — web UI
- [ddgs](https://pypi.org/project/ddgs/) — DuckDuckGo search
