# 🌐 AI-Powered Web Scraping System

A complete AI web scraping system with **intelligent reasoning agent** that understands natural language prompts, automatically finds content, and extracts full information.

## 🧠 NEW: Intelligent Reasoning Agent

**No URL needed!** Just tell it what you want:
- "scrape top 10 blogs ranking on digital marketing strategies"
- "get best SEO optimization tips"
- "extract latest tech news"
- "find best laptops under 50000"

The agent automatically:
- 🔍 **Removes only scraping words** - Keeps your query exactly as typed
- 🌐 **Searches Google** with the exact query
- 🖱️ **ACTUALLY VISITS each website** using Playwright (not just URLs!)
- 📄 Extracts **full content** (complete blogs, articles, news)
- ✅ Always includes: title, description, content, source_url
- 🤖 Plans strategy based on your goal
- 🎯 Context-aware extraction (blogs vs articles vs products)

---

## 📁 Project Structure

```
project/
├── docs/              ← All documentation (20+ guides)
├── src/
│   ├── tests/         ← All test files
│   ├── debug/         ← Debug logs (HTML + selectors)
│   ├── logs/          ← Execution logs
│   ├── output/        ← Scraped data
│   └── *.py           ← Source code
└── README.md          ← This file
```

---

## ⚡ Quick Start

```bash
cd src
pip install -r requirements.txt
playwright install
cp .env.example .env
# Edit .env and add your OpenRouter API key

# Run interactive mode (no URL needed!)
python scrape.py
```

**Example:**
```
Your prompt: top 10 blogs on SEO optimization
URL (optional): [press Enter]

✅ Agent finds URLs automatically!
✅ Extracts full content from each URL!
✅ Saves results with complete information!
```

---

## 📚 Documentation

All documentation is in the `docs/` directory:

- **[docs/INTELLIGENT_AGENT_QUICK_START.md](docs/INTELLIGENT_AGENT_QUICK_START.md)** - New intelligent agent guide ⭐⭐⭐
- **[docs/INTELLIGENT_AGENT_COMPLETE.md](docs/INTELLIGENT_AGENT_COMPLETE.md)** - Full intelligent agent docs
- **[docs/START_HERE.md](docs/START_HERE.md)** - Quick setup guide
- **[docs/HOW_TO_RUN.md](docs/HOW_TO_RUN.md)** - How to run
- **[docs/UNIVERSAL_SCRAPER.md](docs/UNIVERSAL_SCRAPER.md)** - Works with ANY URL
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Problem solving
- **[docs/README.md](docs/README.md)** - Full documentation index

---

## 🎯 Features

✅ **Intelligent reasoning agent** (AI brain that plans and decides) 🆕  
✅ **No URL needed** (auto-searches Google) 🆕  
✅ **Full content extraction** (complete blogs, articles, news) 🆕  
✅ **Mandatory fields** (title, description, content, source_url) 🆕  
✅ **Context-aware** (understands blogs vs articles vs products) 🆕  
✅ Natural language prompts  
✅ Automatic site detection  
✅ JavaScript rendering (Playwright)  
✅ Fast static scraping (Scrapy)  
✅ Vision AI selector generation  
✅ AI-powered intelligent cleaning  
✅ Data cleaning & validation  
✅ Multiple output formats (JSON, YAML, CSV, Excel, SQLite)  
✅ Comprehensive logging  
✅ Debug logging (HTML + selectors saved)  
✅ 30+ tests, all passing  

---

## 💻 Usage

### Interactive Mode (Recommended)
```bash
cd src
python scrape.py
```

**No URL needed!** Just enter your prompt:
```
Your prompt: top 10 blogs on SEO optimization
URL (optional): [press Enter]
```

### Command Line
```bash
cd src
# No URL needed!
python scrape.py --prompt "latest tech news"

# Or with specific URL
python scrape.py --prompt "scrape 10 articles" --url "https://news.ycombinator.com"
```

### Python API
```python
# From src/ directory
from main_scraper import WebScraper

scraper = WebScraper(use_intelligent_cleaning=True)

# No URL needed!
result = scraper.scrape(
    prompt="top 10 blogs on SEO optimization"
)

# Access full content
for item in result['items']:
    print(f"Title: {item['title']}")
    print(f"Full Content: {item['content'][:200]}...")
    print(f"Source: {item['source_url']}")
```

---

## 🧪 Testing

```bash
cd src

# Test intelligent agent (no URL needed!)
python test_intelligent_agent.py

# Test news extraction
python test_news_extraction.py

# Quick test with URL
python tests/quick_test.py https://news.ycombinator.com

# Test any URL
python tests/test_any_url.py https://example.com

# Run all tests
python tests/test_simple.py
```

---

## 🐛 Debug Logging

Every scrape saves debug information to `src/debug/`:

```json
{
  "url": "https://example.com",
  "html_length": 1080870,
  "html_full": "<!DOCTYPE html>...",
  "selectors": {"container": "div.article"},
  "items_found": 10,
  "extraction_method": "dom_analyzer"
}
```

View debug files:
```bash
cd src/debug
dir
```

---

## 📊 Output

All data is saved to `src/output/` directory:
- JSON (default)
- YAML (human-readable)
- CSV (Excel-compatible)
- Excel (.xlsx)
- SQLite (queryable)

---

## 🎯 System Status

✅ **Intelligent Agent**: Complete (reasoning, planning, full content) 🆕  
✅ **Google Search**: Auto-finds URLs (no URL needed!) 🆕  
✅ **Full Content**: Extracts complete blogs/articles/news 🆕  
✅ **Core System**: 9/9 steps (100%)  
✅ **Vision AI**: Integrated  
✅ **Tests**: 30+ passing  
✅ **Storage**: 5 formats  
✅ **Debug**: HTML + selectors logged  
✅ **Production**: Ready  

---

## 📞 Need Help?

1. **Quick Setup**: Read `docs/START_HERE.md`
2. **Full Docs**: Read `docs/README.md`
3. **How to Run**: Read `docs/HOW_TO_RUN.md`
4. **Troubleshooting**: Read `docs/TROUBLESHOOTING.md`
5. **Check Logs**: `src/logs/scraper.log`
6. **Check Debug**: `src/debug/*.json`

---

**Built with**: Python, OpenRouter, LangGraph, Playwright, Vision AI, Intelligent Reasoning Agent  
**Status**: Production Ready ✅  
**Version**: 2.0.0 (Intelligent Agent)
