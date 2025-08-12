"""
News Report Generator using Groq API
- Reads CSV file with news data
- Uses Groq API to generate human-like reports for each news item
- Appends reports to a markdown file
- NEW: Generates Morning Briefing reports in standardized format
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import instructor
from groq import Groq
from pydantic import BaseModel
from datetime import datetime

from signalmuse.utils.utils import get_logger, config, validate_csv_file, ensure_directory

logger = get_logger(__name__)

class NewsReport(BaseModel):
    """Structured model for news report generation"""
    headline: str
    summary: str
    sentiment_analysis: str
    key_points: List[str]
    market_implications: str

# Remove MorningBriefing - it's redundant with enhanced_briefing_generator
# This file should focus on detailed news reports only

def setup_groq_client():
    """Initialize Groq client with API key from environment"""
    # Use centralized Groq client from news_csv_updater_module
    from signalmuse.news_csv_updater_module.groq_client import GroqClientManager
    groq_manager = GroqClientManager()
    if not groq_manager.is_available():
        raise ValueError("GROQ_API_KEY environment variable not found. Please set it in your .env file")
    return groq_manager.get_client()

def generate_report_for_news_item(client, news_item: Dict) -> str:
    """Generate a human-like report for a single news item using Groq API"""
    
    prompt = f"""
    You are a financial news analyst writing a comprehensive report. 
    
    Based on the following news item, create a detailed, human-readable report:
    
    Title: {news_item['title']}
    Publisher: {news_item['publisher']}
    Published: {news_item['published']}
    Summary: {news_item['summary']}
    Sentiment: {news_item['sentiment']} (Confidence: {news_item['confidence']})
    Link: {news_item['link']}
    
    Create a professional financial news report that includes:
    1. A compelling headline
    2. A detailed summary in paragraph form
    3. Sentiment analysis explanation
    4. Key takeaways (3-5 bullet points)
    5. Potential market implications
    
    Write in a professional, engaging tone suitable for financial professionals.
    """
    
    try:
        # Generate structured report using Groq
        report = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert financial news analyst who writes clear, insightful reports."},
                {"role": "user", "content": prompt}
            ],
            response_model=NewsReport,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Format the structured report into markdown
        markdown_report = f"""
## {report.headline}

**Published:** {news_item['published']} | **Source:** {news_item['publisher']}
**Original Link:** [Read Full Article]({news_item['link']})

### Summary
{report.summary}

### Sentiment Analysis
{report.sentiment_analysis}

### Key Points
"""
        for point in report.key_points:
            markdown_report += f"- {point}\n"
        
        markdown_report += f"""
### Market Implications
{report.market_implications}

---

"""
        
        return markdown_report
        
    except Exception as e:
        print(f"❌ Error generating report for: {news_item['title'][:50]}...")
        print(f"Error: {e}")
        
        # Fallback simple report if API fails
        fallback_report = f"""
## {news_item['title']}

**Published:** {news_item['published']} | **Source:** {news_item['publisher']}
**Original Link:** [Read Full Article]({news_item['link']})

### Summary
{news_item['summary']}

### Sentiment
**{news_item['sentiment']}** (Confidence: {news_item['confidence']})

---

"""
        return fallback_report

# Morning briefing functionality moved to enhanced_briefing_generator.py
# This file now focuses only on detailed news report generation

def process_csv_to_report(csv_file_path: str, output_file_path: Optional[str] = None) -> str:
    """
    Process a CSV file of news items and generate a comprehensive markdown report
    
    Args:
        csv_file_path: Path to the CSV file containing news data
        output_file_path: Optional path for output markdown file. If None, generates based on input filename
    
    Returns:
        Path to the generated markdown report file
    """
    
    # Validate and load CSV
    df = validate_csv_file(csv_file_path)
    
    # Set up output path
    if output_file_path is None:
        input_path = Path(csv_file_path)
        output_file_path = config.output_dir / f"{input_path.stem}_report.md"
    
    ensure_directory(Path(output_file_path).parent)
    
    # Initialize Groq client
    logger.info("Setting up Groq API client...")
    client = setup_groq_client()
    
    logger.info(f"Processing {len(df)} news items")
    
    # Initialize the markdown report file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(f"# Financial News Analysis Report\n\n")
        f.write(f"**Generated from:** {csv_file_path}\n")
        f.write(f"**Total Articles:** {len(df)}\n")
        f.write(f"**Generated on:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
    




    # APPENDING LOGIC -----> Process each news item and append to markdown file
    successful_reports = 0
    for index, row in df.iterrows():
        print(f"🔄 Processing article {index + 1}/{len(df)}: {row['title'][:50]}...")
        
        # Generate report for this news item
        report_content = generate_report_for_news_item(client, row.to_dict())
        
        # Append to markdown file
        with open(output_file_path, 'a', encoding='utf-8') as f:
            f.write(report_content)
        
        successful_reports += 1
        print(f"✅ Report generated and appended ({successful_reports}/{len(df)})")
    
    
    
    
    
    
    # Add summary footer
    with open(output_file_path, 'a', encoding='utf-8') as f:
        f.write(f"\n---\n\n")
        f.write(f"**Report Summary:**\n")
        f.write(f"- Total articles processed: {len(df)}\n")
        f.write(f"- Successful reports generated: {successful_reports}\n")
        f.write(f"- Report generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"🎉 Report generation complete!")
    print(f"📄 Report saved to: {output_file_path}")
    
    return str(output_file_path)

# Morning briefing functionality moved to enhanced_briefing_generator.py
# Use EnhancedBriefingGenerator.generate_briefing() instead









def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate human-like news reports from CSV data using Groq API")
    parser.add_argument("csv_file", help="Path to the CSV file containing news data")
    parser.add_argument("-o", "--output", help="Output markdown file path (optional)")
    
    args = parser.parse_args()
    
    try:
        output_path = process_csv_to_report(args.csv_file, args.output)
        print(f"\n✅ Success! Report generated: {output_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 