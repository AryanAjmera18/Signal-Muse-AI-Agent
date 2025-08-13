#!/usr/bin/env python3
"""
Core ticker processing logic for the ticker list generator module.
"""

import sys
import logging
import pandas as pd
from typing import Set, List, Tuple
from pathlib import Path

# Add project root to path for absolute imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from signalmuse.ticker_list_gen_module.data_loader import load_updated_news_csv, load_earnings_data_json
from signalmuse.ticker_list_gen_module.query_engine import (
    get_unique_tickers_from_csv,
    compare_ticker_sets,
    get_top_impact_tickers
)
from signalmuse.ticker_list_gen_module.utils import log_ticker_comparison

logger = logging.getLogger(__name__)

def compare_tickers(csv_tickers: Set[str], earnings_tickers: Set[str]) -> Tuple[Set[str], Set[str]]:
    """
    Compare CSV tickers against earnings tickers.
    
    Args:
        csv_tickers: Set of tickers from CSV data
        earnings_tickers: Set of tickers from earnings data
        
    Returns:
        Tuple[Set[str], Set[str]]: (final_earnings_list, v1_impact_list)
    """
    try:
        logger.info("Starting ticker comparison process")
        
        # Compare ticker sets
        final_earnings_list, v1_impact_list = compare_ticker_sets(csv_tickers, earnings_tickers)
        
        # Log comparison results
        log_ticker_comparison(csv_tickers, earnings_tickers, final_earnings_list, v1_impact_list)
        
        logger.info(f"Comparison complete: {len(final_earnings_list)} earnings matches, {len(v1_impact_list)} impact candidates")
        
        return final_earnings_list, v1_impact_list
        
    except Exception as e:
        logger.error(f"Error in compare_tickers: {str(e)}")
        raise

def generate_final_impact_list(v1_impact_list: Set[str], news_data: pd.DataFrame) -> List[str]:
    """
    Generate final impact list from v1_impact_list based on priority.
    
    Args:
        v1_impact_list: Set of tickers that don't match earnings data
        news_data: DataFrame containing news data
        
    Returns:
        List[str]: Top 5 unique tickers sorted by priority
    """
    try:
        logger.info(f"Generating final impact list from {len(v1_impact_list)} candidates")
        
        if not v1_impact_list:
            logger.info("V1 impact list is empty - returning empty final impact list")
            return []
        
        # Get top impact tickers based on priority
        final_impact_list = get_top_impact_tickers(v1_impact_list, news_data)
        
        logger.info(f"Final impact list generated with {len(final_impact_list)} tickers")
        
        return final_impact_list
        
    except Exception as e:
        logger.error(f"Error in generate_final_impact_list: {str(e)}")
        raise

def process_ticker_data() -> Tuple[Set[str], List[str]]:
    """
    Process ticker data to generate both earnings and impact lists.
    
    Returns:
        Tuple[Set[str], List[str]]: (final_earnings_list, final_impact_list)
    """
    try:
        logger.info("Starting ticker data processing")
        
        # Load data
        news_data = load_updated_news_csv()
        earnings_data = load_earnings_data_json()
        
        # Extract tickers
        csv_unique_tickers = get_unique_tickers_from_csv(news_data)
        
        # Extract earnings tickers
        earnings_tickers = set()
        for record in earnings_data:
            if isinstance(record, dict) and 'ticker' in record:
                ticker = record['ticker']
                if ticker:
                    earnings_tickers.add(str(ticker).strip().upper())
        
        logger.info(f"Data loaded: {len(csv_unique_tickers)} CSV tickers, {len(earnings_tickers)} earnings tickers")
        
        # Compare tickers
        final_earnings_list, v1_impact_list = compare_tickers(csv_unique_tickers, earnings_tickers)
        
        # Generate final impact list
        final_impact_list = generate_final_impact_list(v1_impact_list, news_data)
        
        logger.info("Ticker data processing completed successfully")
        
        return final_earnings_list, final_impact_list
        
    except Exception as e:
        logger.error(f"Error in process_ticker_data: {str(e)}")
        raise

def validate_ticker_lists(final_earnings_list: Set[str], final_impact_list: List[str]) -> bool:
    """
    Validate the generated ticker lists.
    
    Args:
        final_earnings_list: Set of tickers that match earnings data
        final_impact_list: List of top impact tickers
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Check for overlap between lists
        earnings_set = set(final_earnings_list)
        impact_set = set(final_impact_list)
        overlap = earnings_set.intersection(impact_set)
        
        if overlap:
            logger.warning(f"Found overlap between earnings and impact lists: {overlap}")
            return False
        
        # Check impact list length
        if len(final_impact_list) > 5:
            logger.warning(f"Impact list has more than 5 tickers: {len(final_impact_list)}")
            return False
        
        logger.info("Ticker list validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Error in validate_ticker_lists: {str(e)}")
        return False

def get_processing_summary(final_earnings_list: Set[str], final_impact_list: List[str]) -> dict:
    """
    Generate a summary of the processing results.
    
    Args:
        final_earnings_list: Set of tickers that match earnings data
        final_impact_list: List of top impact tickers
        
    Returns:
        dict: Summary of processing results
    """
    try:
        summary = {
            'earnings_tickers_count': len(final_earnings_list),
            'impact_tickers_count': len(final_impact_list),
            'earnings_tickers': sorted(list(final_earnings_list)),
            'impact_tickers': final_impact_list,
            'total_unique_tickers': len(final_earnings_list) + len(final_impact_list),
            'validation_passed': validate_ticker_lists(final_earnings_list, final_impact_list)
        }
        
        logger.info(f"Processing summary: {summary['earnings_tickers_count']} earnings, {summary['impact_tickers_count']} impact")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in get_processing_summary: {str(e)}")
        raise
