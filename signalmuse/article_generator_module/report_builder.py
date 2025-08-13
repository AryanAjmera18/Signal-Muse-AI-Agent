#!/usr/bin/env python3
"""
Appending functions for report building

Implements the appending pattern similar to report_generator.py for 
progressive content building with memory efficiency and progress saving.
"""

from datetime import datetime
from pathlib import Path
from signalmuse.utils.utils import config, generate_timestamp_filename

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
        f.write(f"Top 7 Articles with Individual AI Analysis\n\n")
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


def append_footer(report_path: str):
    """
    Append compliance footer to the report
    
    Args:
        report_path: Path to the report file
    """
    footer = """
************************

## Compliance Disclosure

*This briefing is provided for informational purposes only and does not constitute investment advice, recommendations, or offers to buy or sell securities. All data sourced from public markets and third-party providers. UnBound X users should conduct their own research and consult with qualified professionals before making investment decisions.*

************************
"""
    
    with open(report_path, 'a', encoding='utf-8') as f:
        f.write(footer)
