"""
Data storage and export module
Saves scraped data to various formats (JSON, CSV, Excel, SQLite)
"""

import json
import csv
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from logger import setup_logger

logger = setup_logger(__name__)


class DataStorage:
    """
    Handles saving scraped data to various formats
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize data storage
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"DataStorage initialized (output_dir={output_dir})")
    
    def save(
        self,
        data: List[Dict],
        filename: str,
        format: str = "json",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save data to file
        
        Args:
            data: List of items to save
            filename: Base filename (without extension)
            format: Output format (json, yaml, csv, excel, sqlite)
            metadata: Optional metadata to include
        
        Returns:
            Path to saved file
        """
        if not data:
            logger.warning("No data to save")
            return ""
        
        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{filename}_{timestamp}"
        
        # Save based on format
        if format == "json":
            return self.save_json(data, base_filename, metadata)
        elif format == "yaml":
            return self.save_yaml(data, base_filename, metadata)
        elif format == "csv":
            return self.save_csv(data, base_filename)
        elif format == "excel":
            return self.save_excel(data, base_filename)
        elif format == "sqlite":
            return self.save_sqlite(data, base_filename, metadata)
        else:
            logger.error(f"Unknown format: {format}")
            return ""
    
    def save_json(
        self,
        data: List[Dict],
        filename: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Save data as JSON"""
        filepath = self.output_dir / f"{filename}.json"
        
        output = {
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "count": len(data),
            "items": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(data)} items to JSON: {filepath}")
        return str(filepath)
    
    def save_yaml(
        self,
        data: List[Dict],
        filename: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Save data as YAML"""
        try:
            import yaml
        except ImportError:
            logger.error("PyYAML not installed. Install with: pip install pyyaml")
            return ""
        
        filepath = self.output_dir / f"{filename}.yaml"
        
        output = {
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "count": len(data),
            "items": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        logger.info(f"💾 Saved {len(data)} items to YAML: {filepath}")
        return str(filepath)
    
    def save_csv(self, data: List[Dict], filename: str) -> str:
        """Save data as CSV"""
        filepath = self.output_dir / f"{filename}.csv"
        
        if not data:
            return ""
        
        # Get all unique fields
        fields = set()
        for item in data:
            fields.update(item.keys())
        fields = sorted(fields)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"💾 Saved {len(data)} items to CSV: {filepath}")
        return str(filepath)
    
    def save_excel(self, data: List[Dict], filename: str) -> str:
        """Save data as Excel (requires openpyxl)"""
        try:
            import openpyxl
            from openpyxl import Workbook
        except ImportError:
            logger.error("openpyxl not installed. Install with: pip install openpyxl")
            return ""
        
        filepath = self.output_dir / f"{filename}.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Scraped Data"
        
        if not data:
            return ""
        
        # Get all unique fields
        fields = set()
        for item in data:
            fields.update(item.keys())
        fields = sorted(fields)
        
        # Write header
        ws.append(fields)
        
        # Write data
        for item in data:
            row = [item.get(field, '') for field in fields]
            ws.append(row)
        
        wb.save(filepath)
        logger.info(f"💾 Saved {len(data)} items to Excel: {filepath}")
        return str(filepath)
    
    def save_sqlite(
        self,
        data: List[Dict],
        filename: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Save data to SQLite database"""
        filepath = self.output_dir / f"{filename}.db"
        
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        # Create table
        if data:
            fields = set()
            for item in data:
                fields.update(item.keys())
            fields = sorted(fields)
            
            # Create table with dynamic columns
            columns = ', '.join([f'"{field}" TEXT' for field in fields])
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS scraped_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {columns},
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert data
            placeholders = ', '.join(['?' for _ in fields])
            field_names = ', '.join([f'"{f}"' for f in fields])
            for item in data:
                values = [item.get(field, '') for field in fields]
                cursor.execute(
                    f'INSERT INTO scraped_data ({field_names}) VALUES ({placeholders})',
                    values
                )
            
            # Save metadata
            if metadata:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                for key, value in metadata.items():
                    cursor.execute(
                        'INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
                        (key, str(value))
                    )
        
        conn.commit()
        conn.close()
        
        logger.info(f"💾 Saved {len(data)} items to SQLite: {filepath}")
        return str(filepath)
    
    def save_all_formats(
        self,
        data: List[Dict],
        filename: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Save data in all available formats
        
        Returns:
            Dictionary mapping format to filepath
        """
        logger.info(f"💾 Saving data in all formats...")
        
        results = {
            'json': self.save_json(data, filename, metadata),
            'csv': self.save_csv(data, filename),
        }
        
        # Try YAML (optional dependency)
        try:
            results['yaml'] = self.save_yaml(data, filename, metadata)
        except Exception as e:
            logger.warning(f"YAML export failed: {e}")
        
        # Try Excel (optional dependency)
        try:
            results['excel'] = self.save_excel(data, filename)
        except Exception as e:
            logger.warning(f"Excel export failed: {e}")
        
        # SQLite (optional - only if user wants it)
        # results['sqlite'] = self.save_sqlite(data, filename, metadata)
        
        logger.info(f"✅ Saved data in {len(results)} formats")
        return results
