"""
News Report Generator using Groq API
- Reads CSV file with news data
- Uses Groq API to generate human-like reports for each news item
- Appends reports to a markdown file
- NEW: Generates Morning Briefing reports in standardized format
"""

import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import instructor
from groq import Groq
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
# Look for .env file in the project root (2 levels up from this file)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

class NewsReport(BaseModel):
    """Structured model for news report generation"""
    headline: str
    summary: str
    sentiment_analysis: str
    key_points: List[str]
    market_implications: str

class MorningBriefing(BaseModel):
    """Structured model for Morning Briefing generation"""
    futures_snapshot: str
    premarket_standouts: List[str]
    todays_focus: str
    overnight_drivers: str
    risk_factors: List[str]
    key_levels: str

def setup_groq_client():
    """Initialize Groq client with API key from environment"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not found. Please set it in your .env file")
    
    # Initialize Groq client with instructor for structured outputs
    client = instructor.from_provider("groq/llama3-8b-8192")
    return client

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

def generate_morning_briefing(client, news_data: List[Dict], ticker: str) -> str:
    """Generate a Morning Briefing report in the standardized format"""
    
    # Prepare news summary for the AI
    news_summary = ""
    for i, item in enumerate(news_data[:10]):  # Top 10 most recent articles
        news_summary += f"{i+1}. {item['title']} - Sentiment: {item['sentiment']} ({item['confidence']})\n"
    
    prompt = f"""
    You are a professional financial analyst creating a Morning Market Briefing for {ticker}.
    
    Based on the following recent news articles, create a standardized Morning Briefing following this exact format:
    
    NEWS DATA:
    {news_summary}
    
    Create a Morning Briefing with these sections (max 2000 characters total):
    
    1. FUTURES SNAPSHOT - Brief market futures status
    2. PREMARKET STANDOUTS - Top 3-5 stock movers with brief reasons
    3. TODAY'S FOCUS - Key events (earnings, economic data, Fed speakers)
    4. OVERNIGHT DRIVERS - International markets and commodities
    5. RISK FACTORS - Top 1-2 market risks
    6. KEY LEVELS - Support/resistance levels
    
    Be concise, professional, and focus on actionable insights for traders.
    """
    
    try:
        # Generate structured briefing using Groq
        briefing = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert financial analyst creating concise, professional morning briefings for traders."},
                {"role": "user", "content": prompt}
            ],
            response_model=MorningBriefing,
            max_tokens=800,
            temperature=0.3
        )
        
        # Format the briefing into the exact template structure
        current_date = datetime.now().strftime("%B %d, %Y")
        current_time = datetime.now().strftime("%I:%M %p ET")
        
        markdown_briefing = f"""# SignalMuse: Morning Briefing Development Plan

## Morning Market Brief - {current_date}
Generated at {current_time} | Market Opens: 9:30 AM ET

### FUTURES SNAPSHOT
{briefing.futures_snapshot}

### PREMARKET STANDOUTS
"""
        for standout in briefing.premarket_standouts:
            markdown_briefing += f"• {standout}\n"
        
        markdown_briefing += f"""
### TODAY'S FOCUS
{briefing.todays_focus}

### OVERNIGHT DRIVERS
{briefing.overnight_drivers}

### RISK FACTORS
"""
        for risk in briefing.risk_factors:
            markdown_briefing += f"• {risk}\n"
        
        markdown_briefing += f"""
### KEY LEVELS
{briefing.key_levels}

---
*Generated by SignalMuse AI - Professional Market Intelligence*
"""
        
        return markdown_briefing
        
    except Exception as e:
        print(f"❌ Error generating morning briefing: {e}")
        
        # Fallback simple briefing
        fallback_briefing = f"""# SignalMuse: Morning Briefing Development Plan

## Morning Market Brief - {current_date}
Generated at {current_time} | Market Opens: 9:30 AM ET

### FUTURES SNAPSHOT
• Market data unavailable - check live sources

### PREMARKET STANDOUTS
• {ticker} - Recent news sentiment analysis available
• Check live premarket data for current movers

### TODAY'S FOCUS
• Monitor {ticker} news flow
• Check economic calendar for key releases

### OVERNIGHT DRIVERS
• International markets: Check Asian/European session
• Commodities: Monitor oil, gold, Bitcoin levels

### RISK FACTORS
• Market volatility due to news sentiment
• Monitor {ticker} specific developments

### KEY LEVELS
• Support/Resistance: Check technical analysis
• VIX: Monitor fear gauge levels

---
*Generated by SignalMuse AI - Professional Market Intelligence*
"""
        return fallback_briefing

def process_csv_to_report(csv_file_path: str, output_file_path: Optional[str] = None) -> str:
    """
    Process a CSV file of news items and generate a comprehensive markdown report
    
    Args:
        csv_file_path: Path to the CSV file containing news data
        output_file_path: Optional path for output markdown file. If None, generates based on input filename
    
    Returns:
        Path to the generated markdown report file
    """
    
    # Validate input file
    if not Path(csv_file_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    # Set up output path
    if output_file_path is None:
        input_path = Path(csv_file_path)
        output_file_path = input_path.parent / f"{input_path.stem}_report.md"
    
    # Create output directory if it doesn't exist
    Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize Groq client
    print("🔧 Setting up Groq API client...")
    client = setup_groq_client()
    
    # Read CSV data
    print(f"📖 Reading news data from: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    if df.empty:
        raise ValueError(f"CSV file is empty: {csv_file_path}")
    
    print(f"Found {len(df)} news items to process")
    
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

def process_csv_to_morning_briefing(csv_file_path: str, ticker: str, output_file_path: Optional[str] = None) -> str:
    """
    Process a CSV file of news items and generate a Morning Briefing report
    
    Args:
        csv_file_path: Path to the CSV file containing news data
        ticker: Stock ticker symbol
        output_file_path: Optional path for output markdown file. If None, generates based on input filename
    
    Returns:
        Path to the generated Morning Briefing markdown file
    """
    
    # Validate input file
    if not Path(csv_file_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    # Set up output path
    if output_file_path is None:
        input_path = Path(csv_file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = input_path.parent / f"{ticker.lower()}_morning_briefing_{timestamp}.md"
    
    # Create output directory if it doesn't exist
    Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize Groq client
    print("🔧 Setting up Groq API client...")
    client = setup_groq_client()
    
    # Read CSV data
    print(f"📖 Reading news data from: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    if df.empty:
        raise ValueError(f"CSV file is empty: {csv_file_path}")
    
    print(f"Found {len(df)} news items to process for Morning Briefing")
    
    # Convert DataFrame to list of dictionaries
    news_data = df.to_dict('records')
    
    # Generate Morning Briefing
    print("🤖 Generating Morning Briefing using Groq AI...")
    briefing_content = generate_morning_briefing(client, news_data, ticker)
    
    # Write the briefing to file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(briefing_content)
    
    print(f"🎉 Morning Briefing generation complete!")
    print(f"📄 Briefing saved to: {output_file_path}")
    
    return str(output_file_path)









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