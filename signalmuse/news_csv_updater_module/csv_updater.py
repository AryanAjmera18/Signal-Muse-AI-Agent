#!/usr/bin/env python3
"""
CSV Updater

Handles CSV file operations including loading, updating, and saving.
Reuses utility functions from existing codebase.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional

from ..utils.utils import get_logger, config, validate_csv_file, save_dataframe_to_csv

logger = get_logger(__name__)

class CSVUpdater:
    """Handles CSV file operations for news classification updates"""
    
    def __init__(self):
        self.data_dir = config.data_dir
        self.raw_csv_path = self.data_dir / "raw_news.csv"
        self.updated_csv_path = self.data_dir / "updated_news.csv"
    
    def load_raw_csv(self) -> Optional[pd.DataFrame]:
        """
        Load raw_news.csv from data/real/ directory
        
        Returns:
            DataFrame or None if failed
        """
        try:
            # Reuse existing validation function
            df = validate_csv_file(str(self.raw_csv_path))
            logger.info(f"Loaded raw CSV with {len(df)} articles")
            
            # Verify required columns exist
            required_columns = ['title', 'summary', 'id']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return None
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load raw CSV: {e}")
            return None
    
    def add_new_columns_if_needed(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add 'label' and 'ticker' columns if they don't exist
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with new columns added
        """
        df_copy = df.copy()
        
        # Add label column if not exists
        if 'label' not in df_copy.columns:
            df_copy['label'] = None  # Will be filled during processing
            logger.info("Added 'label' column to DataFrame")
        
        # Add ticker column if not exists
        if 'ticker' not in df_copy.columns:
            df_copy['ticker'] = None  # Will be filled during processing
            logger.info("Added 'ticker' column to DataFrame")
        
        return df_copy
    
    def update_row_with_classification(self, df: pd.DataFrame, news_id: int, label: int, ticker: str) -> bool:
        """
        Update specific row with classification results
        
        Args:
            df: DataFrame to update
            news_id: News article ID
            label: Classification label (0 or 1)
            ticker: Company ticker symbol
            
        Returns:
            True if update successful
        """
        try:
            # Find row with matching news_id
            mask = df['id'] == news_id
            matching_rows = df[mask]
            
            if len(matching_rows) == 0:
                logger.warning(f"No row found with news_id: {news_id}")
                return False
            
            if len(matching_rows) > 1:
                logger.warning(f"Multiple rows found with news_id: {news_id}, updating first match")
            
            # Update the row
            df.loc[mask, 'label'] = label
            df.loc[mask, 'ticker'] = ticker
            
            logger.debug(f"Updated news_id {news_id}: label={label}, ticker={ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating row for news_id {news_id}: {e}")
            return False
    
    def handle_llm_response(self, df: pd.DataFrame, response_data: List[Dict]) -> int:
        """
        Process LLM response and update DataFrame with all classifications
        
        Args:
            df: DataFrame to update
            response_data: List of classification results from LLM
            
        Returns:
            Number of successfully updated rows
        """
        if not response_data:
            logger.warning("No response data to process")
            return 0
        
        updated_count = 0
        
        for classification in response_data:
            news_id = classification['news_id']
            label = classification['label']
            ticker = classification['ticker']
            
            if self.update_row_with_classification(df, news_id, label, ticker):
                updated_count += 1
        
        logger.info(f"Successfully updated {updated_count} out of {len(response_data)} articles")
        return updated_count
    
    def save_updated_csv(self, df: pd.DataFrame) -> bool:
        """
        Save updated DataFrame as updated_news.csv
        
        Args:
            df: Updated DataFrame
            
        Returns:
            True if save successful
        """
        try:
            # Use existing utility function for consistent saving
            output_path = save_dataframe_to_csv(df, str(self.updated_csv_path), logger)
            
            if output_path:
                logger.info(f"Successfully saved updated CSV to: {output_path}")
                return True
            else:
                logger.error("Failed to save updated CSV")
                return False
                
        except Exception as e:
            logger.error(f"Error saving updated CSV: {e}")
            return False
    
    def create_backup(self, df: pd.DataFrame) -> bool:
        """
        Create backup of original data before processing
        
        Args:
            df: Original DataFrame
            
        Returns:
            True if backup successful
        """
        try:
            backup_path = self.data_dir / f"raw_news_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
            save_dataframe_to_csv(df, str(backup_path), logger)
            logger.info(f"Created backup at: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def get_processing_stats(self, df: pd.DataFrame) -> Dict:
        """
        Get statistics about the processing results
        
        Args:
            df: Processed DataFrame
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'total_articles': len(df),
            'articles_with_label': len(df[df['label'].notna()]),
            'articles_with_ticker': len(df[(df['ticker'].notna()) & (df['ticker'] != 'N/A')]),
            'earning_release_count': len(df[df['label'] == 0]),
            'high_impact_count': len(df[df['label'] == 1]),
            'processing_completion': len(df[df['label'].notna()]) / len(df) * 100
        }
        
        return stats
