#!/usr/bin/env python3
"""
Comprehensive Driver for SignalMuse AI Agent Pipeline

This driver orchestrates the entire SignalMuse pipeline by running all modules
in the correct sequence to generate comprehensive market reports.

Pipeline Order:
1. earnings_calendar - Scrape earnings data
2. news_scraper - Scrape news articles
3. news_csv_updater - Process and update news CSV
4. ticker_list_gen - Generate ticker lists
5. article_generator - Generate final reports
"""

import sys
import time
from pathlib import Path
from typing import Set, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from signalmuse.utils.utils import get_logger, config

logger = get_logger(__name__)


def run_earnings_calendar():
    """Step 1: Run earnings calendar module"""
    logger.info("🔄 Step 1: Running earnings calendar module...")
    try:
        # Run Scrapy spider using subprocess
        import subprocess
        import os
        
        spider_path = os.path.join(project_root, "signalmuse", "earnings_calendar_module", "scrapy_crawler", "earnings.py")
        result = subprocess.run(
            ["scrapy", "runspider", spider_path],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            logger.info("✅ Earnings calendar module completed successfully")
            return True
        else:
            logger.error(f"❌ Earnings calendar module failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Earnings calendar module failed: {e}")
        return False


def run_news_scraper():
    """Step 2: Run news scraper module"""
    logger.info("🔄 Step 2: Running news scraper module...")
    try:
        # Import and run news scraper function directly (not main)
        from signalmuse.news_scraper_module.main import run_news_scraper
        filepath = run_news_scraper(
            max_articles_per_feed=20,
            category=None,
            output_filename=None,
            validate_output=True
        )
        if filepath:
            logger.info("✅ News scraper module completed successfully")
            return True
        else:
            logger.error("❌ News scraper module returned None")
            return False
    except Exception as e:
        logger.error(f"❌ News scraper module failed: {e}")
        return False


def run_news_csv_updater():
    """Step 3: Run news CSV updater module"""
    logger.info("🔄 Step 3: Running news CSV updater module...")
    logger.info("   ⏱️  This step may take 2-3 minutes due to rate limiting...")
    try:
        # Import and run news CSV updater function directly
        from signalmuse.news_csv_updater_module.main import NewsCSVUpdater
        updater = NewsCSVUpdater()
        success = updater.process_news_csv()
        if success:
            logger.info("✅ News CSV updater module completed successfully")
            return True
        else:
            logger.error("❌ News CSV updater module failed")
            return False
    except Exception as e:
        logger.error(f"❌ News CSV updater module failed: {e}")
        return False


def run_ticker_list_gen():
    """Step 4: Run ticker list generator module"""
    logger.info("🔄 Step 4: Running ticker list generator module...")
    try:
        # Import and run ticker list generator
        from signalmuse.ticker_list_gen_module.main import generate_ticker_lists
        earnings_list, impact_list = generate_ticker_lists()
        logger.info(f"✅ Ticker list generator completed successfully")
        logger.info(f"   - Earnings tickers: {len(earnings_list)}")
        logger.info(f"   - Impact tickers: {len(impact_list)}")
        return earnings_list, impact_list
    except Exception as e:
        logger.error(f"❌ Ticker list generator failed: {e}")
        return set(), []


def run_article_generator(earnings_list: Set[str], impact_list: List[str]):
    """Step 5: Run article generator module"""
    logger.info("🔄 Step 5: Running article generator module...")
    try:
        # Import and run article generator
        from signalmuse.article_generator_module import ArticleGenerator
        
        generator = ArticleGenerator()
        report_path = generator.generate_articles(earnings_list, impact_list)
        
        logger.info(f"✅ Article generator completed successfully")
        logger.info(f"   - Report generated: {report_path}")
        return report_path
    except Exception as e:
        logger.error(f"❌ Article generator failed: {e}")
        return None


def main():
    """Main driver function that orchestrates the entire pipeline"""
    logger.info("Starting SignalMuse AI Agent Pipeline")
    
    start_time = time.time()
    
    # Step 1: Earnings Calendar
    if not run_earnings_calendar():
        logger.error("❌ Pipeline failed at Step 1. Stopping execution.")
        return False
    
    # Step 2: News Scraper
    if not run_news_scraper():
        logger.error("❌ Pipeline failed at Step 2. Stopping execution.")
        return False
    
    # Step 3: News CSV Updater
    if not run_news_csv_updater():
        logger.error("❌ Pipeline failed at Step 3. Stopping execution.")
        return False
    
    # Step 4: Ticker List Generator
    earnings_list, impact_list = run_ticker_list_gen()
    if not earnings_list and not impact_list:
        logger.error("❌ Pipeline failed at Step 4. Stopping execution.")
        return False
    
    # Step 5: Article Generator
    report_path = run_article_generator(earnings_list, impact_list)
    if not report_path:
        logger.error("❌ Pipeline failed at Step 5.")
        return False
    
    # Pipeline completed successfully
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("SignalMuse pipeline completed successfully")
    logger.info(f"Total execution time: {duration:.2f} seconds")
    logger.info(f"Final report: {report_path}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
