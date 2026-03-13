"""
Debug Logger - Saves HTML and selectors for debugging
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse


class DebugLogger:
    """
    Logs HTML content and CSS selectors for debugging
    """
    
    def __init__(self, debug_dir: str = "debug"):
        """Initialize debug logger"""
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)
    
    def log_scrape_attempt(
        self,
        url: str,
        html: str,
        selectors: Optional[Dict] = None,
        items_found: int = 0,
        extraction_method: str = "unknown"
    ) -> str:
        """
        Log a scrape attempt with HTML and selectors
        
        Args:
            url: URL that was scraped
            html: HTML content retrieved
            selectors: CSS selectors used (if any)
            items_found: Number of items extracted
            extraction_method: Method used (dom_analyzer, heuristic, etc.)
        
        Returns:
            Path to saved debug file
        """
        # Generate filename
        domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_{timestamp}.json"
        filepath = self.debug_dir / filename
        
        # Prepare debug data
        debug_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'domain': urlparse(url).netloc,
            'html_length': len(html),
            'html_preview': html[:1000] + '...' if len(html) > 1000 else html,
            'html_full': html,  # Full HTML for debugging
            'selectors': selectors or {},
            'items_found': items_found,
            'extraction_method': extraction_method,
            'success': items_found > 0
        }
        
        # Save to JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def log_selector_test(
        self,
        url: str,
        selector: str,
        matches_found: int,
        sample_content: Optional[str] = None
    ):
        """
        Log a selector test result
        
        Args:
            url: URL being tested
            selector: CSS selector tested
            matches_found: Number of matches found
            sample_content: Sample of matched content
        """
        domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_selector_test_{timestamp}.json"
        filepath = self.debug_dir / filename
        
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'selector': selector,
            'matches_found': matches_found,
            'sample_content': sample_content,
            'success': matches_found > 0
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def get_latest_debug_file(self, domain: Optional[str] = None) -> Optional[Path]:
        """Get the most recent debug file, optionally filtered by domain"""
        files = list(self.debug_dir.glob('*.json'))
        
        if domain:
            domain_clean = domain.replace('www.', '').replace('.', '_')
            files = [f for f in files if domain_clean in f.name]
        
        if not files:
            return None
        
        return max(files, key=lambda f: f.stat().st_mtime)
    
    def list_debug_files(self, limit: int = 10) -> list:
        """List recent debug files"""
        files = sorted(
            self.debug_dir.glob('*.json'),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        return [str(f) for f in files[:limit]]


# Global debug logger instance
_debug_logger = None

def get_debug_logger() -> DebugLogger:
    """Get global debug logger instance"""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger()
    return _debug_logger
