#!/usr/bin/env python3
"""
News CSV Updater - Main Orchestrator

Main module for processing raw news CSV with Groq LLM classification.
Follows the existing codebase patterns and integrates with the modular structure.
"""

import sys
import pandas as pd
from typing import Optional
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


from signalmuse.utils.utils import get_logger, config
from signalmuse.news_csv_updater_module.groq_client import GroqClientManager
from signalmuse.news_csv_updater_module.chunk_processor import ChunkProcessor
from signalmuse.news_csv_updater_module.csv_updater import CSVUpdater

logger = get_logger(__name__)

class NewsCSVUpdater:
    """
    Main orchestrator for news CSV updating process
    
    Processes raw_news.csv through Groq LLM for classification and ticker extraction,
    then saves the results as updated_news.csv.
    """
    
    def __init__(self, chunk_size: int = 10, rate_limit_delay: float = 5.0):
        """
        Initialize the news CSV updater
        
        Args:
            chunk_size: Number of articles to process per LLM call
            rate_limit_delay: Delay between API calls in seconds
        """
        self.chunk_size = chunk_size
        self.rate_limit_delay = rate_limit_delay
        
        # Initialize components
        self.groq_manager = GroqClientManager(rate_limit_delay)
        self.chunk_processor = ChunkProcessor(self.groq_manager)
        self.csv_updater = CSVUpdater()
        
        logger.info(f"NewsCSVUpdater initialized with chunk_size={chunk_size}, rate_limit={rate_limit_delay}s")
    
    def process_news_csv(self) -> bool:
        """
        Main processing function that orchestrates the entire workflow
        
        Returns:
            True if processing completed successfully
        """
        logger.info("Starting news CSV processing...")
        
        # Step 1: Load raw CSV
        df = self.csv_updater.load_raw_csv()
        if df is None:
            logger.error("Failed to load raw CSV file")
            return False
        
        # Step 2: Create backup
        if not self.csv_updater.create_backup(df):
            logger.warning("Failed to create backup, continuing anyway...")
        
        # Step 3: Add new columns if needed
        df = self.csv_updater.add_new_columns_if_needed(df)
        
        # Step 4: Check Groq client availability
        if not self.groq_manager.is_available():
            logger.error("Groq client not available. Please check your API key configuration.")
            return False
        
        # Step 5: Create chunks
        chunks = self.chunk_processor.create_chunks(df, self.chunk_size)
        total_chunks = len(chunks)
        
        logger.info(f"Processing {total_chunks} chunks with {self.rate_limit_delay}s delays...")
        
        # Step 6: Process each chunk through LLM
        total_processed = 0
        total_errors = 0
        
        for chunk_idx, chunk_df in enumerate(chunks, 1):
            logger.info(f"Processing chunk {chunk_idx}/{total_chunks} ({len(chunk_df)} articles)")
            
            try:
                # Extract article fields
                articles = self.chunk_processor.extract_article_fields(chunk_df)
                
                # Process through LLM
                classification_results = self.chunk_processor.process_chunk_with_llm(articles)
                
                if classification_results:
                    # Update CSV with results
                    updated_count = self.csv_updater.handle_llm_response(df, classification_results)
                    total_processed += updated_count
                    
                    if updated_count < len(articles):
                        total_errors += (len(articles) - updated_count)
                        logger.warning(f"Chunk {chunk_idx}: Updated {updated_count}/{len(articles)} articles")
                    else:
                        logger.info(f"Chunk {chunk_idx}: Successfully updated all {updated_count} articles")
                else:
                    logger.error(f"Chunk {chunk_idx}: Failed to get LLM response")
                    total_errors += len(articles)
                
            except Exception as e:
                logger.error(f"Error processing chunk {chunk_idx}: {e}")
                total_errors += len(chunk_df)
                continue
        
        # Step 7: Save updated CSV
        if total_processed > 0:
            if self.csv_updater.save_updated_csv(df):
                logger.info("Successfully saved updated CSV file")
                
                # Log final statistics
                stats = self.csv_updater.get_processing_stats(df)
                self._log_final_stats(stats, total_processed, total_errors)
                
                return True
            else:
                logger.error("Failed to save updated CSV file")
                return False
        else:
            logger.error("No articles were successfully processed")
            return False
    
    def _log_final_stats(self, stats: dict, total_processed: int, total_errors: int):
        """Log final processing statistics"""
        logger.info("=" * 50)
        logger.info("PROCESSING COMPLETE - FINAL STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total articles: {stats['total_articles']}")
        logger.info(f"Successfully processed: {total_processed}")
        logger.info(f"Errors encountered: {total_errors}")
        logger.info(f"Processing completion: {stats['processing_completion']:.1f}%")
        logger.info(f"None articles (label 0): {stats['none_count']}")
        logger.info(f"Earnings articles (label 1): {stats['earnings_count']}")
        logger.info(f"Impact articles (label 2): {stats['impact_count']}")
        logger.info(f"Both articles (label 3): {stats['both_count']}")
        logger.info(f"Articles with valid tickers (excluding N/A): {stats['articles_with_ticker']}")
        logger.info("=" * 50)

def main():
    """Entry point for standalone execution"""
    try:
        # Check if running in correct environment
        if not config.has_groq_api:
            logger.error("GROQ_API_KEY not found in environment. Please set it in your .env file.")
            return False
        
        # Initialize and run updater
        updater = NewsCSVUpdater()
        success = updater.process_news_csv()
        
        if success:
            logger.info("News CSV updating completed successfully!")
            return True
        else:
            logger.error("News CSV updating failed!")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return False

if __name__ == "__main__":
    main()
