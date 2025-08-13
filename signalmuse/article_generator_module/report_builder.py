#!/usr/bin/env python3
"""
Appending functions for report building

Implements the appending pattern similar to report_generator.py for 
progressive content building with memory efficiency and progress saving.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict
from signalmuse.utils.utils import config, generate_timestamp_filename
from signalmuse.ticker_list_gen_module.data_loader import load_updated_news_csv

# Track which sections have been added to prevent duplicates
_sections_added = set()

def create_report() -> str:
    """
    Create initial report file with UnBound X header format
    
    Returns:
        str: Path to the created report file
    """
    filename = generate_timestamp_filename("market_report", "md")
    report_path = config.output_dir / filename
    
    # Reset section tracking for new report
    global _sections_added
    _sections_added = set()
    
    # Get current date for header
    current_date = datetime.now()
    date_str = current_date.strftime('%B %d, %Y')
    timestamp_str = current_date.strftime('%Y-%m-%d %H:%M:%S')
    
    # Initialize report with UnBound X header
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# UnBound X Morning Market Briefing\n")
        f.write(f"📅 Date: {date_str}\n\n")
        f.write(f"Generated: {timestamp_str}\n")
        f.write(f"Top Articles with Individual AI Analysis\n\n")
        f.write("---\n\n")
    
    return str(report_path)


def append_to_report(report_path: str, content: str, section_type: str):
    """
    Append content to report with proper formatting
    
    Args:
        report_path: Path to the report file
        content: Content to append  
        section_type: Type of section ('earnings' or 'impact')
    """
    global _sections_added
    
    with open(report_path, 'a', encoding='utf-8') as f:
        # Add section headers only once per section type
        if section_type == 'earnings' and 'earnings' not in _sections_added:
            f.write("## Earnings Section\n\n")
            _sections_added.add('earnings')
        elif section_type == 'impact' and 'impact' not in _sections_added:
            f.write("## Market Impact Section\n\n")
            _sections_added.add('impact')
        
        # Append content with proper spacing
        f.write(content + "\n\n")
        f.write("---\n\n")  # Section separator


def extract_and_format_news_sources(ticker: str) -> str:
    """
    For a given ticker:
    1. Load updated_news.csv
    2. Filter all news with that ticker
    3. Extract ONLY source and link
    4. Format as simple markdown links
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        str: Formatted news sources section or empty string if no sources
    """
    try:
        # Load CSV directly
        news_df = load_updated_news_csv()
        
        # Filter news for this specific ticker
        ticker_news = news_df[news_df['ticker'] == ticker]
        
        if ticker_news.empty:
            return ""
        
        # Extract unique source-link pairs
        sources_links = set()
        for _, row in ticker_news.iterrows():
            source = row.get('source', 'Unknown')
            link = row.get('link', '')
            if source and link:
                sources_links.add((source, link))
        
        # Format as simple markdown links
        sources_content = f"\n\n**News Sources for {ticker}:**\n"
        
        for source, link in sorted(sources_links):
            sources_content += f"- [{source}]({link})\n"
        
        return sources_content
        
    except Exception as e:
        # Return empty string if any error occurs
        return ""


def insert_live_prices_section(report_path: str, live_prices_content: str):
    """
    Insert live prices section at the beginning of the report (after header)
    
    Args:
        report_path: Path to the report file
        live_prices_content: Live prices markdown content to insert
    """
    try:
        # Read existing content
        with open(report_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Split at the first "---" to insert live prices after header
        parts = existing_content.split("---", 1)
        if len(parts) == 2:
            header = parts[0]
            rest = parts[1]
            
            # Write back with live prices inserted
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(header)
                f.write(live_prices_content)  # Live prices section
                f.write("---")
                f.write(rest)
        else:
            # Fallback: append to end if structure is unexpected
            with open(report_path, 'a', encoding='utf-8') as f:
                f.write(live_prices_content)
                
    except Exception as e:
        # If insertion fails, append to end as fallback
        with open(report_path, 'a', encoding='utf-8') as f:
            f.write(live_prices_content)


def append_footer(report_path: str):
    """
    Append compliance footer to the report
    
    Args:
        report_path: Path to the report file
    """
    footer = """

## Compliance Disclosure

*This briefing is provided for informational purposes only and does not constitute investment advice, recommendations, or offers to buy or sell securities. All data sourced from public markets and third-party providers. UnBound X users should conduct their own research and consult with qualified professionals before making investment decisions.*

************************
"""
    
    with open(report_path, 'a', encoding='utf-8') as f:
        f.write(footer)
