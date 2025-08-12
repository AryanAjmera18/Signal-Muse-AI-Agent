#!/usr/bin/env python3
"""
News Scraper Module - Standalone Entry Point

This module can be run independently to scrape news from multiple RSS sources.
It maintains the same logic as the original multi_source_scraper but in a modular structure.
"""

import argparse
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from signalmuse.news_scraper_module.scraper.multi_source_scraper import MultiSourceScraper
from signalmuse.news_scraper_module.pipeline.data_processor import validate_csv_format, process_news_data
from signalmuse.utils.utils import get_logger

logger = get_logger(__name__)

def run_news_scraper(
    max_articles_per_feed: int = 20,
    category: str = None,
    output_filename: str = None,
    validate_output: bool = True
) -> str:
    """
    Run the news scraper and return the path to the generated CSV file.
    
    Args:
        max_articles_per_feed: Maximum articles to fetch per RSS feed
        category: Specific category to fetch (optional)
        output_filename: Custom filename for output (optional)
        validate_output: Whether to validate the output format
        
    Returns:
        Path to the generated CSV file
    """
    try:
        logger.info("🚀 Starting News Scraper Module")
        logger.info("=" * 50)
        
        # Initialize scraper
        scraper = MultiSourceScraper()
        
        # Fetch news data
        if category:
            logger.info(f"📡 Fetching news for category: {category}")
            df = scraper.fetch_by_category(category, max_articles=max_articles_per_feed * 5)
        else:
            logger.info(f"📡 Fetching all feeds (max {max_articles_per_feed} articles per feed)")
            df = scraper.fetch_all_feeds(max_articles_per_feed=max_articles_per_feed)
        
        if df.empty:
            logger.error("❌ No articles fetched")
            return None
        
        # Process and validate data
        logger.info("🔧 Processing news data...")
        df = process_news_data(df)
        
        if validate_output:
            if not validate_csv_format(df):
                logger.error("❌ CSV format validation failed")
                return None
        
        # Save to CSV
        logger.info("💾 Saving to CSV...")
        filepath = scraper.save_to_csv(df, output_filename)
        
        # Print summary
        logger.info("✅ News scraping completed successfully!")
        logger.info(f"📊 Summary:")
        logger.info(f"   - Total articles: {len(df)}")
        logger.info(f"   - Sources: {df['source'].nunique()}")
        logger.info(f"   - Categories: {df['category'].nunique()}")
        logger.info(f"   - Output file: {filepath}")
        
        # Show category breakdown
        logger.info(f"📈 Articles by category:")
        category_counts = df['category'].value_counts()
        for category_name, count in category_counts.items():
            logger.info(f"   - {category_name}: {count} articles")
        
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Error in news scraper: {str(e)}")
        return None

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(
        description="Standalone News Scraper - Fetch financial news from multiple RSS sources"
    )
    parser.add_argument(
        "--max-articles", 
        type=int, 
        default=20,
        help="Maximum articles per feed (default: 20)"
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=['general_financial', 'investing_markets', 'economy_policy', 'cryptocurrency', 'fintech'],
        help="Specific category to fetch"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Custom output filename"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip output validation"
    )
    
    args = parser.parse_args()
    
    # Run the scraper
    filepath = run_news_scraper(
        max_articles_per_feed=args.max_articles,
        category=args.category,
        output_filename=args.output,
        validate_output=not args.no_validate
    )
    
    if filepath:
        print(f"\n🎉 News scraping completed! Output saved to: {filepath}")
        sys.exit(0)
    else:
        print("\n❌ News scraping failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
