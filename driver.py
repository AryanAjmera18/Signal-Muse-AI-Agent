#!/usr/bin/env python3
"""
Simple Driver for Testing Article Generator Module

This driver runs the ticker_list_gen_module to get actual ticker lists
and then tests the article generator module with real data.
"""

import sys
from pathlib import Path
from typing import Set, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from signalmuse.utils.utils import get_logger, config
from signalmuse.ticker_list_gen_module.main import generate_ticker_lists
from signalmuse.article_generator_module import ArticleGenerator

logger = get_logger(__name__)


def get_ticker_lists() -> tuple[Set[str], List[str]]:
    """
    Get actual ticker lists from ticker_list_gen_module
    
    Returns:
        tuple[Set[str], List[str]]: (final_earnings_list, final_impact_list)
    """
    try:
        logger.info("=== Getting Ticker Lists ===")
        
        # Generate ticker lists using existing module
        final_earnings_list, final_impact_list = generate_ticker_lists()
        
        logger.info(f"✅ Generated {len(final_earnings_list)} earnings tickers")
        logger.info(f"✅ Generated {len(final_impact_list)} impact tickers")
        
        # Log the actual tickers for verification
        logger.info(f"Earnings tickers: {sorted(list(final_earnings_list))}")
        logger.info(f"Impact tickers: {final_impact_list}")
        
        return final_earnings_list, final_impact_list
        
    except Exception as e:
        logger.error(f"❌ Failed to get ticker lists: {e}")
        # Return fallback data for testing
        fallback_earnings = {'AAPL', 'MSFT', 'GOOGL', 'NVDA'}
        fallback_impact = ['TSLA', 'META', 'AMZN']
        logger.info(f"Using fallback data: {fallback_earnings}, {fallback_impact}")
        return fallback_earnings, fallback_impact


def test_article_generator(earnings_list: Set[str], impact_list: List[str]) -> bool:
    """
    Test the article generator module with real ticker lists
    
    Args:
        earnings_list: Set of earnings tickers
        impact_list: List of impact tickers
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("=== Testing Article Generator Module ===")
        
        # Check if Groq API is available
        if not config.has_groq_api:
            logger.error("GROQ_API_KEY not found in environment. Please set it in your .env file.")
            return False
        
        # Initialize article generator
        generator = ArticleGenerator()
        
        # Generate articles with real data
        report_path = generator.generate_articles(earnings_list, impact_list)
        
        logger.info(f"✅ Article generation successful!")
        logger.info(f"📄 Report saved to: {report_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Article generator test failed: {e}")
        return False


def main():
    """Main driver function"""
    try:
        logger.info("🚀 Starting Article Generator Module Test")
        logger.info("=" * 60)
        
        # Step 1: Get actual ticker lists
        earnings_list, impact_list = get_ticker_lists()
        
        # Step 2: Test article generator with real data
        success = test_article_generator(earnings_list, impact_list)
        
        if success:
            logger.info("🎉 All tests completed successfully!")
            return True
        else:
            logger.error("❌ Tests failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Driver failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
