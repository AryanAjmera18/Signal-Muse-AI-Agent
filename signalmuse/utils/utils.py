#!/usr/bin/env python3
"""
Core Utilities
Common utilities for logging, environment, file operations, and configurations
"""

import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Global configuration
_env_loaded = False
_logger_configured = False

def setup_environment():
    """Setup environment variables once"""
    global _env_loaded
    if not _env_loaded:
        load_dotenv()
        _env_loaded = True

def setup_logging(level: str = "INFO", format_str: Optional[str] = None):
    """Setup logging configuration once"""
    global _logger_configured
    if not _logger_configured:
        if format_str is None:
            format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=format_str,
            force=True  # Override any existing config
        )
        _logger_configured = True

def get_logger(name: str) -> logging.Logger:
    """Get a logger with proper setup"""
    setup_logging()
    return logging.getLogger(name)

def ensure_directory(path: Path) -> Path:
    """Ensure directory exists and return path"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_dataframe_to_csv(df: pd.DataFrame, filepath: str, logger: Optional[logging.Logger] = None) -> str:
    """Common CSV saving functionality"""
    if df.empty:
        if logger:
            logger.warning("No data to save")
        return ""
    
    filepath_obj = Path(filepath)
    ensure_directory(filepath_obj.parent)
    
    df.to_csv(filepath_obj, index=False)
    
    if logger:
        logger.info(f"Saved {len(df)} records to {filepath}")
    
    return str(filepath_obj)

def generate_timestamp_filename(base_name: str, extension: str = "csv") -> str:
    """Generate timestamped filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"

def validate_csv_file(filepath: str) -> pd.DataFrame:
    """Validate and load CSV file"""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    if df.empty:
        raise ValueError(f"CSV file is empty: {filepath}")
    
    return df

class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        setup_environment()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY")
        
        # Directories
        self.data_dir = Path("signalmuse/data/real")
        self.output_dir = Path("signalmuse/outputs")
        
        # Ensure directories exist
        ensure_directory(self.data_dir)
        ensure_directory(self.output_dir)
    
    @property
    def has_groq_api(self) -> bool:
        return bool(self.groq_api_key)
    
    @property
    def has_fmp_api(self) -> bool:
        return bool(self.fmp_api_key)

# Global config instance
config = Config()