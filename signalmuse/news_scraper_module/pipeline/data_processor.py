"""
Data Processing Utilities

Contains utilities for processing and validating news data.
"""

import pandas as pd
from typing import Dict, List, Optional
from signalmuse.utils.utils import get_logger

logger = get_logger(__name__)

def validate_csv_format(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame has the correct CSV format.
    
    Expected columns: title,link,summary,published,source,category,priority,guid,author,tags,id
    """
    expected_columns = [
        'title', 'link', 'summary', 'published', 'source', 
        'category', 'priority', 'guid', 'author', 'tags', 'id'
    ]
    
    missing_columns = set(expected_columns) - set(df.columns)
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    
    logger.info(f"CSV format validation passed: {len(df)} articles")
    return True

def process_news_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process and clean news data.
    
    Args:
        df: Raw news DataFrame
        
    Returns:
        Processed DataFrame with cleaned data
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for processing")
        return df
    
    # Make a copy to avoid modifying original
    processed_df = df.copy()
    
    # Clean text fields
    if 'title' in processed_df.columns:
        processed_df['title'] = processed_df['title'].str.strip()
    
    if 'summary' in processed_df.columns:
        processed_df['summary'] = processed_df['summary'].str.strip()
    
    if 'author' in processed_df.columns:
        processed_df['author'] = processed_df['author'].fillna('')
    
    # Ensure tags is a list
    if 'tags' in processed_df.columns:
        processed_df['tags'] = processed_df['tags'].apply(
            lambda x: x if isinstance(x, list) else []
        )
    
    # Remove duplicates based on ID
    initial_count = len(processed_df)
    processed_df = processed_df.drop_duplicates(subset=['id'])
    final_count = len(processed_df)
    
    if initial_count != final_count:
        logger.debug(f"Removed {initial_count - final_count} duplicate articles")
    
    logger.debug(f"Processed {len(processed_df)} articles")
    return processed_df
