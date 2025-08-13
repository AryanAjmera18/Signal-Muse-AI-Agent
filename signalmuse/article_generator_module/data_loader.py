#!/usr/bin/env python3
"""
Ultra-lean data loader reusing existing functions

This module maximizes code reuse by importing all data loading functionality
from the existing ticker_list_gen_module data_loader.py. Only 10 LOC of new code!
"""

from typing import Set, List, Dict, Tuple

# Import ALL existing functions we need - MAXIMUM REUSE!
from signalmuse.ticker_list_gen_module.data_loader import (
    load_updated_news_csv, 
    load_earnings_data_json,
    extract_unique_tickers_from_csv,
    extract_tickers_from_earnings_data
)


def load_ticker_data(earnings_list: Set[str], impact_list: List[str]) -> Tuple[Dict, Dict]:
    """
    Load and filter data using existing functions - ULTRA LEAN!
    
    Args:
        earnings_list: Set of tickers with earnings data  
        impact_list: List of top impact tickers
        
    Returns:
        Tuple[Dict, Dict]: (earnings_filtered, news_filtered)
    """
    
    # REUSE existing functions - NO CODE DUPLICATION!
    earnings_data = load_earnings_data_json()
    news_df = load_updated_news_csv()
    
    # Filter earnings data for our specific tickers (compact comprehension)
    earnings_filtered = {
        ticker: next((e for e in earnings_data if e.get('ticker') == ticker), {}) 
        for ticker in earnings_list
    }
    
    # Filter news data for all tickers (compact comprehension)
    all_tickers = list(earnings_list) + impact_list
    news_filtered = {
        ticker: news_df[news_df['ticker'] == ticker][['title', 'summary']].to_dict('records') 
        for ticker in all_tickers
    }
    
    return earnings_filtered, news_filtered
