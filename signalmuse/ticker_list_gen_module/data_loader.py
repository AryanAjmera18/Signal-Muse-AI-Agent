#!/usr/bin/env python3
"""
Data loading functions for the ticker list generator module.
"""

import sys
import json
import logging
import pandas as pd
from typing import Set, Dict, List, Any
from pathlib import Path

# Add project root to path for absolute imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from signalmuse.ticker_list_gen_module.config import UPDATED_NEWS_CSV_PATH, EARNINGS_DATA_JSON_PATH
from signalmuse.ticker_list_gen_module.utils import clean_ticker_set, validate_data_paths

logger = logging.getLogger(__name__)

def load_updated_news_csv() -> pd.DataFrame:
    """
    Load the updated_news.csv file.
    
    Returns:
        pd.DataFrame: Loaded CSV data
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        pd.errors.EmptyDataError: If CSV file is empty
    """
    try:
        logger.info(f"Loading CSV data from: {UPDATED_NEWS_CSV_PATH}")
        
        if not UPDATED_NEWS_CSV_PATH.exists():
            raise FileNotFoundError(f"CSV file not found: {UPDATED_NEWS_CSV_PATH}")
        
        df = pd.read_csv(UPDATED_NEWS_CSV_PATH)
        
        if df.empty:
            raise pd.errors.EmptyDataError("CSV file is empty")
        
        logger.info(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        logger.debug(f"CSV columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        raise

def load_earnings_data_json() -> List[Dict[str, Any]]:
    """
    Load the earnings_data.json file.
    
    Returns:
        List[Dict[str, Any]]: Loaded JSON data
        
    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON file is invalid
    """
    try:
        logger.info(f"Loading JSON data from: {EARNINGS_DATA_JSON_PATH}")
        
        if not EARNINGS_DATA_JSON_PATH.exists():
            raise FileNotFoundError(f"JSON file not found: {EARNINGS_DATA_JSON_PATH}")
        
        with open(EARNINGS_DATA_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("JSON data should be a list of objects")
        
        logger.info(f"Successfully loaded JSON with {len(data)} earnings records")
        
        return data
        
    except Exception as e:
        logger.error(f"Error loading JSON file: {str(e)}")
        raise

def extract_unique_tickers_from_csv(csv_data: pd.DataFrame) -> Set[str]:
    """
    Extract unique tickers from CSV data.
    
    Args:
        csv_data: DataFrame containing news data
        
    Returns:
        Set[str]: Set of unique ticker symbols
    """
    try:
        if 'ticker' not in csv_data.columns:
            raise ValueError("CSV data does not contain 'ticker' column")
        
        # Extract ticker column and get unique values
        ticker_column = csv_data['ticker']
        unique_tickers = set(ticker_column.dropna().unique())
        
        # Clean the ticker set
        cleaned_tickers = clean_ticker_set(unique_tickers)
        
        logger.info(f"Extracted {len(cleaned_tickers)} unique valid tickers from CSV")
        
        return cleaned_tickers
        
    except Exception as e:
        logger.error(f"Error extracting tickers from CSV: {str(e)}")
        raise

def extract_tickers_from_earnings_data(earnings_data: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract ticker symbols from earnings data.
    
    Args:
        earnings_data: List of earnings data dictionaries
        
    Returns:
        Set[str]: Set of unique ticker symbols
    """
    try:
        tickers = set()
        
        for record in earnings_data:
            if isinstance(record, dict) and 'ticker' in record:
                ticker = record['ticker']
                if ticker:  # Check if ticker is not None/empty
                    tickers.add(str(ticker).strip().upper())
        
        # Clean the ticker set
        cleaned_tickers = clean_ticker_set(tickers)
        
        logger.info(f"Extracted {len(cleaned_tickers)} unique valid tickers from earnings data")
        
        return cleaned_tickers
        
    except Exception as e:
        logger.error(f"Error extracting tickers from earnings data: {str(e)}")
        raise

def get_csv_unique_tickers() -> Set[str]:
    """
    Load CSV data and extract unique tickers.
    
    Returns:
        Set[str]: Set of unique ticker symbols from CSV
    """
    csv_data = load_updated_news_csv()
    return extract_unique_tickers_from_csv(csv_data)

def get_earnings_tickers() -> Set[str]:
    """
    Load earnings data and extract tickers.
    
    Returns:
        Set[str]: Set of unique ticker symbols from earnings data
    """
    earnings_data = load_earnings_data_json()
    return extract_tickers_from_earnings_data(earnings_data)
