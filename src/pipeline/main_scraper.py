"""
Main integrated web scraper
Combines all components into a complete scraping system
"""

import sys
import os

# Ensure all subpackage directories are on the path
_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _sub in ("agents", "extractors", "scrapers", "pipeline"):
    sys.path.insert(0, os.path.join(_src, _sub))
sys.path.insert(0, _src)

from typing import List, Dict, Optional
from intent_analyzer import IntentAnalyzer
from site_detector import SiteDetector
from playwright_scraper import PlaywrightScraper
from scrapy_scraper import ScrapyScraper
from data_cleaner import DataCleaner
from intelligent_cleaner import IntelligentCleaner
from vision_selector import VisionEnhancedScraper
from data_storage import DataStorage
from logger import setup_logger, log_step

logger = setup_logger(__name__)


class WebScraper:
    """
    Complete web scraping system
    Integrates all components for end-to-end scraping
    """
    
    def __init__(
        self, 
        use_vision: bool = False, 
        vision_model: str = "openai/gpt-4o", 
        output_dir: str = "output",
        use_intelligent_cleaning: bool = True
    ):
        """
        Initialize web scraper with all components
        
        Args:
            use_vision: Enable vision AI for selector generation
            vision_model: Vision model to use (if use_vision=True)
            output_dir: Directory to save output files
            use_intelligent_cleaning: Enable AI-powered intelligent cleaning
        """
        logger.info("="*70)
        logger.info("INITIALIZING WEB SCRAPER")
        logger.info("="*70)
        
        self.intent_analyzer = IntentAnalyzer()
        self.site_detector = SiteDetector()
        self.playwright_scraper = PlaywrightScraper(headless=True)
        self.scrapy_scraper = ScrapyScraper(timeout=30)
        self.data_cleaner = DataCleaner()
        self.data_storage = DataStorage(output_dir=output_dir)
        
        # Intelligent cleaning (optional)
        self.use_intelligent_cleaning = use_intelligent_cleaning
        if use_intelligent_cleaning:
            try:
                self.intelligent_cleaner = IntelligentCleaner()
                logger.info("✅ AI-powered intelligent cleaning enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize intelligent cleaner: {e}")
                self.use_intelligent_cleaning = False
                self.intelligent_cleaner = None
        else:
            self.intelligent_cleaner = None
            logger.info("ℹ️ Using traditional cleaning (set use_intelligent_cleaning=True for AI)")
        
        # Vision AI (optional)
        self.use_vision = use_vision
        if use_vision:
            self.vision_scraper = VisionEnhancedScraper(
                base_scraper=self.playwright_scraper,
                vision_model=vision_model
            )
            logger.info(f"✅ Vision AI enabled with model: {vision_model}")
        else:
            self.vision_scraper = None
            logger.info("ℹ️ Vision AI disabled (use use_vision=True to enable)")
        
        # URL Generator (for automatic URL generation)
        from url_generator import URLGenerator
        from simple_search_agent import SimpleSearchAgent
        from google_search_agent import GoogleSearchAgent
        from smart_url_visitor import SmartURLVisitor
        from reasoning_agent import ReasoningAgent
        
        self.output_dir = output_dir
        self.url_generator = URLGenerator()
        self.search_agent = SimpleSearchAgent()
        self.google_agent = GoogleSearchAgent(headless=True)
        self.reasoning_agent = ReasoningAgent()
        
        logger.info("✅ URL Generator initialized (auto-generates URLs from prompts)")
        logger.info("✅ Simple Search Agent initialized (primary - DuckDuckGo library, reliable)")
        logger.info("✅ Google Search Agent initialized (backup if needed)")
        logger.info("✅ Smart URL Visitor initialized (visits URLs, skips login pages)")
        logger.info("✅ Reasoning Agent initialized (AI brain for planning and decisions)")
        
        logger.info(f"✅ Output directory: {output_dir}")
        logger.info("✅ All components initialized")
    
    def scrape(
        self,
        prompt: str,
        url: Optional[str] = None,
        validate_fields: bool = True,
        deduplicate: bool = True,
        save_to_file: bool = True,
        output_format: str = "json",
        output_filename: Optional[str] = None
    ) -> Dict:
        """
        Scrape data from URL based on user prompt
        
        Args:
            prompt: User's scraping request
            url: URL to scrape (optional - will be auto-generated if not provided)
            validate_fields: Whether to validate required fields
            deduplicate: Whether to remove duplicates
            save_to_file: Whether to save results to file
            output_format: Output format (json, csv, excel, sqlite, all)
            output_filename: Custom filename (auto-generated if None)
        
        Returns:
            Dictionary with results and metadata
        """
        logger.info("\n" + "="*70)
        logger.info("STARTING SCRAPING WORKFLOW")
        logger.info("="*70)
        logger.info(f"📝 Prompt: {prompt}")
        
        # Auto-generate URL if not provided
        if not url:
            logger.info("🔍 No URL provided - using Google Search Agent...")

            # Step 1 (early): Analyze intent to get quantity BEFORE searching
            # so we know how many URLs to fetch
            logger.info("🔍 Pre-analyzing intent to determine quantity...")
            try:
                _early_intent = self.intent_analyzer.analyze(prompt)
                target_quantity = _early_intent.quantity or 10
            except Exception:
                target_quantity = 10
            logger.info(f"🎯 Target quantity from prompt: {target_quantity}")

            # Extract search query from prompt
            url_result = self.url_generator.generate_url(prompt)
            search_query = url_result['search_query']
            logger.info(f"🔎 Search query: {search_query}")

            # Fetch 3x quantity so we have enough even after skipping login/blocked pages
            fetch_count = max(10, target_quantity * 3)
            logger.info(f"🔍 Using DuckDuckGo search (fetching {fetch_count} URLs for {target_quantity} target)")
            search_results = self.search_agent.search_and_get_urls(
                query=search_query,
                num_results=fetch_count,
                skip_domains=['youtube.com', 'facebook.com', 'twitter.com', 'instagram.com']
            )
            
            # Fallback to Google if DuckDuckGo fails
            if not search_results:
                logger.warning("⚠️ DuckDuckGo failed, trying Google as fallback...")
                search_results = self.google_agent.search_and_get_urls(
                    query=search_query,
                    num_results=10,
                    skip_domains=['youtube.com', 'facebook.com', 'twitter.com', 'instagram.com']
                )
            
            if not search_results:
                logger.error("❌ No search results found")
                return {
                    'success': False,
                    'items': [],
                    'error': 'No search results found',
                    'metadata': {'prompt': prompt}
                }
            
            logger.info(f"✅ Found {len(search_results)} URLs to scrape")
            
            # Save ALL URLs to load_url.json
            urls_json_file = None
            logger.info("\n" + "="*70)
            logger.info("💾 SAVING URLs to load_url.json")
            logger.info("="*70)
            
            try:
                import os
                import json
                from datetime import datetime
                
                # Create output directory if needed
                output_dir = 'output'
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                urls_json_file = os.path.join(output_dir, "load_url.json")
                
                # Prepare data
                data = {
                    'search_query': search_query,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_results': len(search_results),
                    'urls': [
                        {
                            'rank': i + 1,
                            'title': result['title'],
                            'url': result['url'],
                            'snippet': result.get('snippet', '')
                        }
                        for i, result in enumerate(search_results)
                    ]
                }
                
                # Save to JSON
                with open(urls_json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ All URLs saved to: {urls_json_file}")
                logger.info(f"📊 Total URLs: {len(search_results)}")
            except Exception as e:
                logger.error(f"Failed to save load_url.json: {e}")
            
            # Also save top 3 URLs to text file (for easy viewing)
            top_3_urls = search_results[:3]
            urls_filename = None
            
            logger.info("\n💾 SAVING TOP 3 URLs to text file")
            
            try:
                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                urls_filename = f"{output_dir}/search_urls_{timestamp}.txt"
                
                # Save URLs to file
                with open(urls_filename, 'w', encoding='utf-8') as f:
                    f.write(f"Search Query: {search_query}\n")
                    f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total Results: {len(search_results)}\n")
                    f.write("\n" + "="*70 + "\n")
                    f.write("TOP 3 URLS FROM SEARCH RESULTS\n")
                    f.write("="*70 + "\n\n")
                    
                    for i, result in enumerate(top_3_urls, 1):
                        f.write(f"{i}. {result['title']}\n")
                        f.write(f"   URL: {result['url']}\n")
                        if result.get('snippet'):
                            f.write(f"   Snippet: {result['snippet'][:200]}...\n")
                        f.write("\n")
                
                logger.info(f"✅ Top 3 URLs saved to: {urls_filename}")
                logger.info("\nTop 3 URLs:")
                for i, result in enumerate(top_3_urls, 1):
                    logger.info(f"  {i}. {result['title'][:60]}...")
                    logger.info(f"     {result['url']}")
                
                logger.info("="*70)
                
            except Exception as e:
                logger.error(f"Failed to save text file: {e}")
            
            # Extract URLs for scraping
            urls_to_scrape = [r['url'] for r in search_results]
        else:
            urls_filename = None  # No search performed
            urls_json_file = None
        
        logger.info(f"🌐 URL: {url if url else 'Multiple URLs from Google'}")
        
        try:
            # Step 0: Reasoning Agent - Plan the extraction
            logger.info("\n🧠 STEP 0: AI Planning...")
            extraction_plan = self.reasoning_agent.plan_extraction(prompt, "unknown")
            logger.info(f"📋 Plan: {extraction_plan['reasoning']}")
            logger.info(f"📊 Mandatory fields: {extraction_plan['mandatory_fields']}")
            
            # Step 1: Analyze intent
            logger.info("\n🔍 STEP 1: Analyzing intent...")
            intent = self.intent_analyzer.analyze(prompt)
            logger.info(f"✅ Content type: {intent.content_type}")
            
            # Override fields with mandatory fields from plan
            intent.fields = extraction_plan['mandatory_fields']
            logger.info(f"✅ Fields (from AI plan): {intent.fields}")
            logger.info(f"✅ Quantity: {intent.quantity}")
            
            # Step 2: Detect site type (skip if using multi-URL from Google)
            logger.info("\n🌐 STEP 2: Detecting site type...")
            if url:
                site_info = self.site_detector.detect(url)
                logger.info(f"✅ Tool: {site_info.tool}")
                logger.info(f"✅ Has JS: {site_info.has_js_frameworks}")
            else:
                # Using Google search - will scrape multiple URLs
                # Create a default site_info for playwright
                from site_detector import SiteInfo
                site_info = SiteInfo(
                    url="multiple_urls",
                    tool="playwright",
                    has_js_frameworks=True,
                    reasoning="Multi-URL scraping from Google search",
                    content_length=0
                )
                logger.info(f"✅ Tool: playwright (multi-URL mode)")
                logger.info(f"✅ Has JS: {site_info.has_js_frameworks}")
            
            # Step 3: Try vision AI if enabled
            selectors = None
            if self.use_vision and site_info.tool == 'playwright' and url:
                logger.info("\n🔍 STEP 3: Trying vision AI for selector generation...")
                try:
                    screenshot_path = self.playwright_scraper.capture_screenshot(url, "temp_vision.png")
                    from vision_selector import VisionSelectorGenerator
                    vision_gen = VisionSelectorGenerator()
                    selectors = vision_gen.generate_selectors(
                        screenshot_path=screenshot_path,
                        content_type=intent.content_type,
                        fields=intent.fields
                    )
                    if selectors:
                        logger.info("✅ Vision AI generated selectors successfully")
                    else:
                        logger.info("ℹ️ Vision AI failed, will use automatic extraction")
                except Exception as e:
                    logger.warning(f"Vision AI failed: {e}, falling back to automatic extraction")
            else:
                logger.info("\n📚 STEP 3: Skipping vision AI (disabled)")
                logger.info("ℹ️ Will use automatic extraction")
            
            # Step 4: Scrape data
            logger.info("\n📦 STEP 4: Scraping data...")
            
            # Check if we have multiple URLs from Google search
            if not url and 'urls_json_file' in locals() and urls_json_file:
                logger.info(f"🌐 Visiting URLs from load_url.json (target: {intent.quantity} items, skipping login pages)...")
                from smart_url_visitor import SmartURLVisitor
                visitor = SmartURLVisitor(load_url_path=urls_json_file)
                items = visitor.visit_and_scrape(
                    content_type=intent.content_type,
                    fields=intent.fields,
                    target_count=intent.quantity or 10
                )
            elif site_info.tool == 'playwright':
                items = self.playwright_scraper.scrape(
                    url=url,
                    content_type=intent.content_type,
                    fields=intent.fields,
                    quantity=intent.quantity,
                    selectors=selectors
                )
            else:
                items = self.scrapy_scraper.scrape(
                    url=url,
                    content_type=intent.content_type,
                    fields=intent.fields,
                    quantity=intent.quantity,
                    selectors=selectors
                )
            
            logger.info(f"✅ Extracted {len(items)} items")
            
            # Save raw items BEFORE cleaning
            raw_saved_files = {}
            if save_to_file and len(items) > 0:
                logger.info("\n💾 Saving RAW items (before cleaning)...")
                
                # Generate filename for raw data
                from urllib.parse import urlparse
                if url:
                    domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
                else:
                    domain = "google_search"
                raw_filename = f"{intent.content_type}_{domain}_raw"
                
                # Save raw data
                if output_format == "all":
                    raw_saved_files = self.data_storage.save_all_formats(
                        data=items,
                        filename=raw_filename,
                        metadata={
                            'prompt': prompt,
                            'url': url,
                            'content_type': intent.content_type,
                            'fields': intent.fields,
                            'tool_used': site_info.tool,
                            'data_stage': 'raw_before_cleaning'
                        }
                    )
                    logger.info(f"✅ Raw data saved in {len(raw_saved_files)} formats")
                else:
                    raw_filepath = self.data_storage.save(
                        data=items,
                        filename=raw_filename,
                        format=output_format,
                        metadata={
                            'prompt': prompt,
                            'url': url,
                            'content_type': intent.content_type,
                            'fields': intent.fields,
                            'tool_used': site_info.tool,
                            'data_stage': 'raw_before_cleaning'
                        }
                    )
                    raw_saved_files[output_format] = raw_filepath
                    logger.info(f"✅ Raw data saved to: {raw_filepath}")
            
            # Step 5: Clean data
            logger.info("\n🧹 STEP 5: Cleaning data...")
            
            # Use intelligent cleaning if enabled
            if self.use_intelligent_cleaning and self.intelligent_cleaner:
                logger.info("🤖 Using AI-powered intelligent cleaning...")
                cleaned_items = self.intelligent_cleaner.intelligent_clean(
                    items=items,
                    prompt=prompt,
                    content_type=intent.content_type,
                    fields=intent.fields
                )
                logger.info(f"✅ AI cleaned {len(cleaned_items)} items")
                
                # Skip traditional validation since AI already validated
                validate_fields = False
            else:
                # Traditional cleaning
                cleaned_items = self.data_cleaner.clean(items, intent.fields)
                logger.info(f"✅ Cleaned {len(cleaned_items)} items")
            
            # Step 6: Validate fields (optional, skipped if AI cleaning used)
            if validate_fields and len(cleaned_items) > 0:
                logger.info("\n✅ STEP 6: Validating fields...")
                cleaned_items = self.data_cleaner.validate_fields(
                    cleaned_items,
                    intent.fields
                )
                logger.info(f"✅ {len(cleaned_items)} items passed validation")
            
            # Step 7: Deduplicate (optional)
            if deduplicate and len(cleaned_items) > 0:
                logger.info("\n🔄 STEP 7: Removing duplicates...")
                cleaned_items = self.data_cleaner.deduplicate(
                    cleaned_items,
                    key_field='url' if 'url' in intent.fields else intent.fields[0]
                )
                logger.info(f"✅ {len(cleaned_items)} unique items")
            
            # Success
            logger.info("\n" + "="*70)
            logger.info("SCRAPING COMPLETED SUCCESSFULLY")
            logger.info("="*70)
            logger.info(f"✅ Extracted: {len(items)} items")
            logger.info(f"✅ Cleaned: {len(cleaned_items)} items")
            logger.info(f"✅ Success rate: {len(cleaned_items)/max(len(items), 1)*100:.1f}%")
            
            # Save to file if requested
            saved_files = {}
            if save_to_file and len(cleaned_items) > 0:
                logger.info("\n💾 Saving CLEANED results to file...")
                
                # Generate filename if not provided
                if not output_filename:
                    from urllib.parse import urlparse
                    if url:
                        domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
                    else:
                        domain = "google_search"
                    output_filename = f"{intent.content_type}_{domain}_cleaned"
                
                # Save based on format
                if output_format == "all":
                    saved_files = self.data_storage.save_all_formats(
                        data=cleaned_items,
                        filename=output_filename,
                        metadata={
                            'prompt': prompt,
                            'url': url,
                            'content_type': intent.content_type,
                            'fields': intent.fields,
                            'tool_used': site_info.tool,
                            'data_stage': 'cleaned'
                        }
                    )
                    logger.info(f"✅ Cleaned data saved in {len(saved_files)} formats")
                else:
                    filepath = self.data_storage.save(
                        data=cleaned_items,
                        filename=output_filename,
                        format=output_format,
                        metadata={
                            'prompt': prompt,
                            'url': url,
                            'content_type': intent.content_type,
                            'fields': intent.fields,
                            'tool_used': site_info.tool,
                            'data_stage': 'cleaned'
                        }
                    )
                    saved_files[output_format] = filepath
                    logger.info(f"✅ Cleaned data saved to: {filepath}")
            
            return {
                'success': True,
                'items': cleaned_items,
                'raw_items': items,  # Include raw items
                'search_urls_file': urls_filename if 'urls_filename' in locals() else None,  # Top 3 URLs text file
                'load_url_json': urls_json_file if 'urls_json_file' in locals() else None,  # All URLs JSON file
                'saved_files': {
                    'raw': raw_saved_files,
                    'cleaned': saved_files
                },
                'metadata': {
                    'prompt': prompt,
                    'url': url,
                    'content_type': intent.content_type,
                    'fields': intent.fields,
                    'quantity_requested': intent.quantity,
                    'quantity_extracted': len(items),
                    'quantity_cleaned': len(cleaned_items),
                    'tool_used': site_info.tool,
                    'pattern_used': selectors is not None
                }
            }
            
        except Exception as e:
            logger.error(f"\n❌ SCRAPING FAILED: {e}")
            logger.exception("Full error details:")
            
            return {
                'success': False,
                'items': [],
                'raw_items': [],
                'error': str(e),
                'metadata': {
                    'prompt': prompt,
                    'url': url,
                    'tool_used': 'unknown'
                }
            }


def main():
    """Example usage"""
    scraper = WebScraper()
    
    # Example 1: Scrape Hacker News
    result = scraper.scrape(
        prompt="scrape 5 tech articles",
        url="https://news.ycombinator.com"
    )
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Success: {result['success']}")
    print(f"Items: {len(result['items'])}")
    
    if result['items']:
        print("\nSample items:")
        for i, item in enumerate(result['items'][:3], 1):
            print(f"\n{i}. {item}")


if __name__ == "__main__":
    main()
