#!/usr/bin/env python
"""
AI Web Scraper - Command Line Interface
Run the scraper with user prompts

Usage:
    python scrape.py
    python scrape.py --prompt "scrape 10 articles" --url "https://news.ycombinator.com"
"""

import sys
import os

# Force UTF-8 output on Windows to support emoji characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add all subpackage directories to path so imports work across subfolders
_src = os.path.dirname(os.path.abspath(__file__))
for _sub in ("agents", "extractors", "scrapers", "pipeline"):
    sys.path.insert(0, os.path.join(_src, _sub))
sys.path.insert(0, _src)

import argparse

from pipeline.main_scraper import WebScraper


def interactive_mode():
    """Interactive mode - ask user for input"""
    
    print("\n" + "="*70)
    print("🤖 AI WEB SCRAPER - Interactive Mode")
    print("="*70)
    
    # Get user input
    print("\n📝 What do you want to scrape?")
    print("Examples:")
    print("  - top 10 blogs ranking on SEO optimization")
    print("  - top 10 movie scripts of all time")
    print("  - latest tech news")
    print("  - best laptops under 50000")
    
    prompt = input("\nYour prompt: ").strip()
    
    if not prompt:
        print("❌ Prompt cannot be empty")
        return
    
    print("\n🌐 Enter URL (or press Enter to auto-generate from prompt):")
    print("Leave empty to let AI find the right URL automatically!")
    print("\nOr provide specific URL:")
    print("  - https://news.ycombinator.com")
    print("  - https://www.amazon.com/s?k=laptop")
    
    url = input("\nURL (optional): ").strip() or None
    
    if not url:
        print("✅ Will auto-generate URL from your prompt")
    
    # Optional settings
    print("\n⚙️ Optional Settings (press Enter to skip):")
    
    # Output format
    print("\nOutput format? (json/yaml/csv/excel/all)")
    output_format = input("Format [json]: ").strip() or "json"
    
    # Vision AI
    use_vision = input("\nUse Vision AI? (y/n) [n]: ").strip().lower() == 'y'
    
    # Custom filename
    custom_filename = input("\nCustom filename (optional): ").strip() or None
    
    # Run scraper
    print("\n" + "="*70)
    print("🚀 STARTING SCRAPER")
    print("="*70)
    print(f"📝 Prompt: {prompt}")
    if url:
        print(f"🌐 URL: {url}")
    else:
        print(f"🔍 URL: Auto-generating...")
    print(f"📊 Format: {output_format}")
    print(f"👁️ Vision AI: {'Enabled' if use_vision else 'Disabled'}")
    print("-"*70)
    
    try:
        scraper = WebScraper(
            use_vision=use_vision,
            use_intelligent_cleaning=True  # Enable AI cleaning by default
        )
        
        result = scraper.scrape(
            prompt=prompt,
            url=url,
            output_format=output_format,
            output_filename=custom_filename
        )
        
        # Show results
        print("\n" + "="*70)
        print("✅ SCRAPING COMPLETE")
        print("="*70)
        print(f"Success: {result['success']}")
        print(f"Items scraped: {len(result.get('raw_items', []))}")
        print(f"Items cleaned: {len(result['items'])}")
        
        # Tool used (may not exist if error occurred)
        if 'metadata' in result and 'tool_used' in result['metadata']:
            print(f"Tool used: {result['metadata']['tool_used']}")
        
        # Show search URLs file if exists
        if result.get('search_urls_file'):
            print(f"\n📋 Top 3 Search URLs saved to: {result['search_urls_file']}")
        
        # Show load_url.json if exists
        if result.get('load_url_json'):
            print(f"📋 All Search URLs (JSON) saved to: {result['load_url_json']}")
        
        if result.get('saved_files'):
            if result['saved_files'].get('raw'):
                print(f"\n📁 Raw data files (before cleaning):")
                for format, filepath in result['saved_files']['raw'].items():
                    print(f"   {format.upper()}: {filepath}")
            
            if result['saved_files'].get('cleaned'):
                print(f"\n📁 Cleaned data files:")
                for format, filepath in result['saved_files']['cleaned'].items():
                    print(f"   {format.upper()}: {filepath}")
        
        # Show sample items
        if result['items']:
            qty = result.get('metadata', {}).get('quantity_requested') or len(result['items'])
            show_n = min(qty, len(result['items']))
            print(f"\n📊 Sample cleaned items (first {show_n}):")
            for i, item in enumerate(result['items'][:show_n], 1):
                print(f"\n{i}. {item}")
        
        print("\n" + "="*70)
        print("✅ Done! Check the output/ directory for your files.")
        print("📝 Raw data saved with '_raw' suffix")
        print("✨ Cleaned data saved with '_cleaned' suffix")
        if result.get('search_urls_file'):
            print("📋 Top 3 search URLs saved separately")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


def command_line_mode(args):
    """Command line mode - use arguments"""
    
    print("\n" + "="*70)
    print("🤖 AI WEB SCRAPER")
    print("="*70)
    print(f"📝 Prompt: {args.prompt}")
    print(f"🌐 URL: {args.url}")
    print(f"📊 Format: {args.format}")
    print(f"👁️ Vision AI: {'Enabled' if args.vision else 'Disabled'}")
    print("-"*70)
    
    try:
        scraper = WebScraper(
            use_vision=args.vision,
            output_dir=args.output_dir,
            use_intelligent_cleaning=True  # Enable AI cleaning by default
        )
        
        result = scraper.scrape(
            prompt=args.prompt,
            url=args.url,
            output_format=args.format,
            output_filename=args.filename
        )
        
        # Show results
        print("\n" + "="*70)
        print("✅ SCRAPING COMPLETE")
        print("="*70)
        print(f"Success: {result['success']}")
        print(f"Items scraped: {len(result.get('raw_items', []))}")
        print(f"Items cleaned: {len(result['items'])}")
        
        # Tool used (may not exist if error occurred)
        if 'metadata' in result and 'tool_used' in result['metadata']:
            print(f"Tool used: {result['metadata']['tool_used']}")
        
        if result.get('saved_files'):
            if result['saved_files'].get('raw'):
                print(f"\n📁 Raw data files (before cleaning):")
                for format, filepath in result['saved_files']['raw'].items():
                    print(f"   {format.upper()}: {filepath}")
            
            if result['saved_files'].get('cleaned'):
                print(f"\n📁 Cleaned data files:")
                for format, filepath in result['saved_files']['cleaned'].items():
                    print(f"   {format.upper()}: {filepath}")
        
        # Show sample items if verbose
        if args.verbose and result['items']:
            qty = result.get('metadata', {}).get('quantity_requested') or len(result['items'])
            show_n = min(qty, len(result['items']))
            print(f"\n📊 Sample items (first {show_n}):")
            for i, item in enumerate(result['items'][:show_n], 1):
                print(f"\n{i}. {item}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='AI Web Scraper - Scrape websites with natural language prompts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python scrape.py
  
  # Command line mode
  python scrape.py --prompt "scrape 10 articles" --url "https://news.ycombinator.com"
  
  # With Vision AI
  python scrape.py --prompt "scrape products" --url "https://example.com" --vision
  
  # Save as CSV
  python scrape.py --prompt "scrape data" --url "https://example.com" --format csv
  
  # Custom filename
  python scrape.py --prompt "scrape articles" --url "https://example.com" --filename my_data
        """
    )
    
    parser.add_argument(
        '--prompt', '-p',
        type=str,
        help='What to scrape (e.g., "scrape 10 tech articles")'
    )
    
    parser.add_argument(
        '--url', '-u',
        type=str,
        help='URL to scrape'
    )
    
    parser.add_argument(
        '--format', '-f',
        type=str,
        default='json',
        choices=['json', 'yaml', 'csv', 'excel', 'sqlite', 'all'],
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--vision',
        action='store_true',
        help='Enable Vision AI for selector generation'
    )
    
    parser.add_argument(
        '--filename',
        type=str,
        help='Custom output filename (without extension)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory (default: output)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, run interactive mode
    if not args.prompt or not args.url:
        interactive_mode()
    else:
        command_line_mode(args)


if __name__ == "__main__":
    main()
