#!/usr/bin/env python3
"""
Query engine for SQL-like operations on ticker data.
"""

import sys
import logging
import pandas as pd
from typing import Set, List, Tuple
from pathlib import Path

# Add project root to path for absolute imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from signalmuse.ticker_list_gen_module.config import TOP_IMPACT_TICKERS_LIMIT, TOP_EARNINGS_TICKERS_LIMIT

logger = logging.getLogger(__name__)

def get_unique_tickers_from_csv(csv_data: pd.DataFrame) -> Set[str]:
    """
    SQL-like operation: "SELECT DISTINCT ticker FROM csv_data"
    
    Args:
        csv_data: DataFrame containing news data
        
    Returns:
        Set[str]: Set of unique ticker symbols
    """
    try:
        if 'ticker' not in csv_data.columns:
            raise ValueError("CSV data does not contain 'ticker' column")
        
        # Get unique tickers, excluding null values
        unique_tickers = set(csv_data['ticker'].dropna().unique())
        
        logger.debug(f"Found {len(unique_tickers)} unique tickers in CSV data")
        
        return unique_tickers
        
    except Exception as e:
        logger.error(f"Error in get_unique_tickers_from_csv: {str(e)}")
        raise

def filter_news_by_tickers(csv_data: pd.DataFrame, ticker_list: Set[str]) -> pd.DataFrame:
    """
    SQL-like operation: "SELECT * FROM csv_data WHERE ticker IN ticker_list"
    
    Args:
        csv_data: DataFrame containing news data
        ticker_list: Set of ticker symbols to filter by
        
    Returns:
        pd.DataFrame: Filtered DataFrame containing only articles for specified tickers
    """
    try:
        if 'ticker' not in csv_data.columns:
            raise ValueError("CSV data does not contain 'ticker' column")
        
        # Convert ticker_list to uppercase for case-insensitive matching
        ticker_list_upper = {ticker.upper() for ticker in ticker_list}
        
        # Filter DataFrame
        filtered_data = csv_data[
            csv_data['ticker'].str.upper().isin(ticker_list_upper)
        ].copy()
        
        logger.debug(f"Filtered news data: {len(csv_data)} -> {len(filtered_data)} articles for {len(ticker_list)} tickers")
        
        return filtered_data
        
    except Exception as e:
        logger.error(f"Error in filter_news_by_tickers: {str(e)}")
        raise

def sort_by_priority_and_select_top(filtered_data: pd.DataFrame, limit: int = None, limit_type: str = "impact") -> List[str]:
    """
    SQL-like operation: "SELECT ticker FROM filtered_data ORDER BY priority DESC LIMIT limit"
    
    Args:
        filtered_data: DataFrame containing filtered news data
        limit: Maximum number of unique tickers to return (default from config)
        limit_type: Type of limit to apply ("earnings" or "impact")
        
    Returns:
        List[str]: List of top tickers sorted by priority
    """
    try:
        if limit is None:
            if limit_type == "earnings":
                limit = TOP_EARNINGS_TICKERS_LIMIT
            else:
                limit = TOP_IMPACT_TICKERS_LIMIT
        
        if filtered_data.empty:
            logger.warning("No data to sort - returning empty list")
            return []
        
        # Check if priority column exists
        if 'priority' not in filtered_data.columns:
            logger.warning(f"Priority column not found - returning first {limit} unique tickers")
            unique_tickers = filtered_data['ticker'].dropna().unique()[:limit]
            return list(unique_tickers)
        
        # Sort by priority (descending) and get unique tickers
        sorted_data = filtered_data.sort_values('priority', ascending=False)
        
        # Get unique tickers in order of appearance (maintaining priority order)
        seen_tickers = set()
        top_tickers = []
        
        for ticker in sorted_data['ticker']:
            if ticker and ticker not in seen_tickers and len(top_tickers) < limit:
                seen_tickers.add(ticker)
                top_tickers.append(ticker)
        
        logger.debug(f"Selected top {len(top_tickers)} unique tickers by priority for {limit_type}")
        
        return top_tickers
        
    except Exception as e:
        logger.error(f"Error in sort_by_priority_and_select_top: {str(e)}")
        raise

def get_top_earnings_tickers(v1_earnings_list: Set[str], csv_data: pd.DataFrame) -> List[str]:
    """
    Get top earnings tickers from v1_earnings_list based on priority.
    
    Args:
        v1_earnings_list: Set of tickers that match earnings data
        csv_data: DataFrame containing news data
        
    Returns:
        List[str]: Top 5 unique earnings tickers sorted by priority
    """
    try:
        if not v1_earnings_list:
            logger.debug("V1 earnings list is empty - returning empty list")
            return []
        
        # Filter news data for tickers in v1_earnings_list
        filtered_data = filter_news_by_tickers(csv_data, v1_earnings_list)
        
        if filtered_data.empty:
            logger.warning(f"No news articles found for tickers in v1_earnings_list: {v1_earnings_list}")
            return []
        
        # Sort by priority and select top tickers
        top_tickers = sort_by_priority_and_select_top(filtered_data, limit_type="earnings")
        
        logger.info(f"Generated final earnings list with {len(top_tickers)} tickers")
        
        return top_tickers
        
    except Exception as e:
        logger.error(f"Error in get_top_earnings_tickers: {str(e)}")
        raise

def get_top_impact_tickers(v1_impact_list: Set[str], csv_data: pd.DataFrame) -> List[str]:
    """
    Get top impact tickers from v1_impact_list based on priority.
    
    Args:
        v1_impact_list: Set of tickers that don't match earnings data
        csv_data: DataFrame containing news data
        
    Returns:
        List[str]: Top 5 unique tickers sorted by priority
    """
    try:
        if not v1_impact_list:
            logger.debug("V1 impact list is empty - returning empty list")
            return []
        
        # Filter news data for tickers in v1_impact_list
        filtered_data = filter_news_by_tickers(csv_data, v1_impact_list)
        
        if filtered_data.empty:
            logger.warning(f"No news articles found for tickers in v1_impact_list: {v1_impact_list}")
            return []
        
        # Sort by priority and select top tickers
        top_tickers = sort_by_priority_and_select_top(filtered_data, limit_type="impact")
        
        logger.info(f"Generated final impact list with {len(top_tickers)} tickers")
        
        return top_tickers
        
    except Exception as e:
        logger.error(f"Error in get_top_impact_tickers: {str(e)}")
        raise

def compare_ticker_sets(csv_tickers: Set[str], earnings_tickers: Set[str]) -> Tuple[Set[str], Set[str]]:
    """
    Compare two sets of tickers and return matches and non-matches.
    
    Args:
        csv_tickers: Set of tickers from CSV data
        earnings_tickers: Set of tickers from earnings data
        
    Returns:
        Tuple[Set[str], Set[str]]: (matches, non-matches)
    """
    try:
        # Convert to uppercase for case-insensitive comparison
        csv_upper = {ticker.upper() for ticker in csv_tickers}
        earnings_upper = {ticker.upper() for ticker in earnings_tickers}
        
        # Find matches (intersection)
        matches = csv_upper.intersection(earnings_upper)
        
        # Find non-matches (difference)
        non_matches = csv_upper.difference(earnings_upper)
        
        logger.debug(f"Ticker comparison: {len(matches)} matches, {len(non_matches)} non-matches")
        
        return matches, non_matches
        
    except Exception as e:
        logger.error(f"Error in compare_ticker_sets: {str(e)}")
        raise
