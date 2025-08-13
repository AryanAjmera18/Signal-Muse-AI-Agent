#!/usr/bin/env python3
"""
Utility functions for the ticker list generator module.
"""

import sys
import logging
from typing import Set, List, Any
from pathlib import Path

# Add project root to path for absolute imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from signalmuse.ticker_list_gen_module.config import VALID_TICKER_VALUES

# Set up logging
logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def is_valid_ticker(ticker: Any) -> bool:
    """
    Check if a ticker value is valid.
    
    Args:
        ticker: The ticker value to validate
        
    Returns:
        bool: True if ticker is valid, False otherwise
    """
    if ticker is None:
        return False
    
    ticker_str = str(ticker).strip()
    return ticker_str not in VALID_TICKER_VALUES and len(ticker_str) > 0

def clean_ticker_set(tickers: Set[str]) -> Set[str]:
    """
    Clean a set of tickers by removing invalid values.
    
    Args:
        tickers: Set of ticker strings
        
    Returns:
        Set[str]: Cleaned set of valid tickers
    """
    cleaned_tickers = set()
    for ticker in tickers:
        if is_valid_ticker(ticker):
            cleaned_tickers.add(str(ticker).strip().upper())
    
    logger.debug(f"Cleaned ticker set: {len(tickers)} -> {len(cleaned_tickers)} valid tickers")
    return cleaned_tickers

def log_ticker_comparison(csv_tickers: Set[str], earnings_tickers: Set[str], 
                         v1_earnings: Set[str], v1_impact: Set[str]) -> None:
    """
    Log ticker comparison results for debugging.
    
    Args:
        csv_tickers: Set of tickers from CSV
        earnings_tickers: Set of tickers from earnings data
        v1_earnings: Set of tickers that match earnings (before priority filtering)
        v1_impact: Set of tickers that don't match earnings (before priority filtering)
    """
    logger.debug(f"CSV unique tickers: {len(csv_tickers)}")
    logger.debug(f"Earnings tickers: {len(earnings_tickers)}")
    logger.debug(f"V1 earnings list: {len(v1_earnings)}")
    logger.debug(f"V1 impact list: {len(v1_impact)}")
    
    if v1_earnings:
        logger.debug(f"Earnings matches: {sorted(v1_earnings)}")
    if v1_impact:
        logger.debug(f"Impact candidates: {sorted(v1_impact)}")

def validate_data_paths() -> bool:
    """
    Validate that required data files exist.
    
    Returns:
        bool: True if all files exist, False otherwise
    """
    from signalmuse.ticker_list_gen_module.config import UPDATED_NEWS_CSV_PATH, EARNINGS_DATA_JSON_PATH
    
    csv_exists = UPDATED_NEWS_CSV_PATH.exists()
    json_exists = EARNINGS_DATA_JSON_PATH.exists()
    
    if not csv_exists:
        logger.error(f"CSV file not found: {UPDATED_NEWS_CSV_PATH}")
    if not json_exists:
        logger.error(f"JSON file not found: {EARNINGS_DATA_JSON_PATH}")
    
    return csv_exists and json_exists
