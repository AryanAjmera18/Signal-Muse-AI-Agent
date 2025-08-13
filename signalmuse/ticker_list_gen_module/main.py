#!/usr/bin/env python3
"""
Main orchestrator for the ticker list generator module.
"""

import sys
import logging
from typing import Set, List, Tuple, Dict, Any
from pathlib import Path

# Add project root to path for absolute imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from signalmuse.ticker_list_gen_module.utils import setup_logging, validate_data_paths
from signalmuse.ticker_list_gen_module.ticker_processor import process_ticker_data, get_processing_summary
from signalmuse.ticker_list_gen_module.config import LOG_LEVEL

# Set up logging
setup_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

def generate_ticker_lists() -> Tuple[List[str], List[str]]:
    """
    Main function to generate ticker lists from news and earnings data.
    
    This function orchestrates the entire process:
    1. Loads updated_news.csv and earnings_data.json
    2. Extracts unique tickers from CSV
    3. Compares CSV tickers with earnings tickers
    4. Generates final_earnings_list (top 5 by priority) and final_impact_list (top 5 by priority)
    
    Returns:
        Tuple[List[str], List[str]]: (final_earnings_list, final_impact_list)
        
    Raises:
        FileNotFoundError: If required data files are missing
        ValueError: If data processing fails
        Exception: For other processing errors
    """
    try:
        logger.info("Starting ticker list generation process")
        
        # Validate data paths
        if not validate_data_paths():
            raise FileNotFoundError("Required data files not found")
        
        # Process ticker data
        final_earnings_list, final_impact_list = process_ticker_data()
        
        # Generate summary
        summary = get_processing_summary(final_earnings_list, final_impact_list)
        
        logger.info("Ticker list generation completed successfully")
        logger.info(f"Generated {len(final_earnings_list)} earnings tickers and {len(final_impact_list)} impact tickers")
        
        return final_earnings_list, final_impact_list
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_ticker_lists: {str(e)}")
        raise

def generate_ticker_lists_with_summary() -> Dict[str, Any]:
    """
    Generate ticker lists and return with detailed summary.
    
    Returns:
        Dict[str, Any]: Dictionary containing ticker lists and processing summary
        
    Raises:
        Exception: If processing fails
    """
    try:
        logger.info("Starting ticker list generation with summary")
        
        # Generate ticker lists
        final_earnings_list, final_impact_list = generate_ticker_lists()
        
        # Get processing summary
        summary = get_processing_summary(final_earnings_list, final_impact_list)
        
        # Create result dictionary
        result = {
            'success': True,
            'final_earnings_list': final_earnings_list,
            'final_impact_list': final_impact_list,
            'summary': summary,
            'timestamp': logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))
        }
        
        logger.info("Ticker list generation with summary completed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_ticker_lists_with_summary: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'final_earnings_list': [],
            'final_impact_list': [],
            'summary': {},
            'timestamp': logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))
        }

def main():
    """
    Main entry point for standalone execution.
    """
    try:
        logger.info("Ticker List Generator Module - Standalone Execution")
        
        # Generate ticker lists
        final_earnings_list, final_impact_list = generate_ticker_lists()
        
        # Print results
        print("\n" + "="*50)
        print("TICKER LIST GENERATION RESULTS")
        print("="*50)
        print(f"Earnings Tickers ({len(final_earnings_list)}):")
        for ticker in final_earnings_list:
            print(f"  - {ticker}")
        
        print(f"\nImpact Tickers ({len(final_impact_list)}):")
        for ticker in final_impact_list:
            print(f"  - {ticker}")
        
        print("\n" + "="*50)
        print("Processing completed successfully!")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        print(f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
