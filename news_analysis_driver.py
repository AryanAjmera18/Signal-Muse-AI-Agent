#!/usr/bin/env python3
"""
News Analysis Driver Script

This script provides a complete workflow:
1. Asks user for a stock ticker symbol
2. Runs yahoo_scraper.py to fetch and analyze news
3. Generates a human-like report using the report generator

Usage: uv run python news_analysis_driver.py
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file in the root directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check if GROQ_API_KEY is set
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found!")
        print("\n📋 Setup Instructions:")
        print("1. Get your API key from: https://console.groq.com/keys")
        print("2. Set it in your environment:")
        print("   PowerShell: $env:GROQ_API_KEY='your_key_here'")
        print("   CMD: set GROQ_API_KEY=your_key_here")
        return False
    
    # Check if required files exist
    required_files = [
        "signalmuse/scrapers/yahoo_scraper.py",
        "signalmuse/outputs/report_generator.py"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Required file not found: {file}")
            return False
    
    print("✅ All dependencies are ready!")
    return True

def get_user_input():
    """Get stock ticker from user with validation"""
    print("\n" + "="*50)
    print("📈 Stock News Analysis")
    print("="*50)
    
    while True:
        ticker = input("\n🎯 Enter stock ticker symbol (e.g., AAPL, GOOGL, TSLA): ").strip().upper()
        
        if not ticker:
            print("❌ Please enter a valid ticker symbol")
            continue
        
        if len(ticker) > 10:
            print("❌ Ticker symbol seems too long. Please check and try again.")
            continue
        
        # Confirm with user
        confirm = input(f"\n✅ You entered: {ticker}. Proceed? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            return ticker
        elif confirm in ['n', 'no']:
            continue
        else:
            print("Please enter 'y' for yes or 'n' for no.")

def run_yahoo_scraper(ticker):
    """Run the Yahoo scraper to fetch news data"""
    print(f"\n🔄 Step 1: Fetching news for {ticker}...")
    
    # Set up output path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_output = f"signalmuse/data/real/{ticker.lower()}_news_{timestamp}.csv"
    
    try:
        # Import and run the yahoo scraper
        sys.path.append(str(Path(__file__).parent))
        from signalmuse.scrapers.yahoo_scraper import get_yahoo_news_sentiment
        
        print(f"📡 Scraping Yahoo Finance news for {ticker}...")
        results = get_yahoo_news_sentiment(ticker, save_path=csv_output)
        
        if not results:
            print(f"❌ No news found for {ticker}. Please try a different ticker.")
            return None
        
        print(f"✅ Successfully scraped {len(results)} articles")
        print(f"📁 Data saved to: {csv_output}")
        
        return csv_output
        
    except Exception as e:
        print(f"❌ Error running Yahoo scraper: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_report(csv_file, ticker):
    """Generate the human-like report using Groq API"""
    print(f"\n🔄 Step 2: Generating AI-powered report...")
    
    # Set up output path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_output = f"signalmuse/outputs/{ticker.lower()}_analysis_report_{timestamp}.md"
    
    try:
        from signalmuse.outputs.report_generator import process_csv_to_report
        
        print(f"🤖 Using Groq AI to generate human-like analysis...")
        result_path = process_csv_to_report(csv_file, report_output)
        
        print(f"✅ Report generation complete!")
        print(f"📄 Report saved to: {result_path}")
        
        return result_path
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main driver function"""
    print("🚀 News Analysis Driver - Stock Market Intelligence")
    print("This tool will fetch news and generate AI-powered analysis reports")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please fix the setup issues above and try again.")
        return 1
    
    try:
        # Get user input
        ticker = get_user_input()
        
        # Step 1: Run Yahoo scraper
        csv_file = run_yahoo_scraper(ticker)
        if not csv_file:
            print(f"\n❌ Failed to fetch news for {ticker}")
            return 1
        
        # Step 2: Generate report
        report_file = generate_report(csv_file, ticker)
        if not report_file:
            print(f"\n❌ Failed to generate report")
            return 1
        
        # Success summary
        print("\n" + "="*60)
        print("🎉 ANALYSIS COMPLETE!")
        print("="*60)
        print(f"📊 Ticker analyzed: {ticker}")
        print(f"📁 Raw data: {csv_file}")
        print(f"📄 AI Report: {report_file}")
        print("\n💡 Next steps:")
        print(f"   - Open {report_file} to read the analysis")
        print(f"   - Share the report with your team")
        print(f"   - Use insights for investment decisions")
        print("="*60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n👋 Analysis cancelled by user. Goodbye!")
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main()) 