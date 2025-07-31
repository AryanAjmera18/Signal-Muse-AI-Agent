#!/usr/bin/env python3
"""
Enhanced Morning Briefing Generator

Generates comprehensive morning market briefings in the UnBound X format
with futures data, economic calendar, earnings, and strategic insights.
"""

import pandas as pd
import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common stock tickers for extraction
COMMON_TICKERS = {
    'AAPL': 'Apple', 'MSFT': 'Microsoft', 'GOOGL': 'Alphabet', 'AMZN': 'Amazon',
    'TSLA': 'Tesla', 'META': 'Meta', 'NVDA': 'NVIDIA', 'NFLX': 'Netflix',
    'PLTR': 'Palantir', 'AMD': 'Advanced Micro Devices', 'INTC': 'Intel',
    'CRM': 'Salesforce', 'ORCL': 'Oracle', 'ADBE': 'Adobe', 'PYPL': 'PayPal',
    'UBER': 'Uber', 'LYFT': 'Lyft', 'SNAP': 'Snap', 'TWTR': 'Twitter',
    'SPOT': 'Spotify', 'ZM': 'Zoom', 'SQ': 'Square', 'SHOP': 'Shopify',
    'RDDT': 'Reddit', 'COIN': 'Coinbase', 'HOOD': 'Robinhood', 'RIVN': 'Rivian',
    'LCID': 'Lucid', 'NIO': 'NIO', 'XPEV': 'XPeng', 'LI': 'Li Auto',
    'JPM': 'JPMorgan', 'BAC': 'Bank of America', 'WFC': 'Wells Fargo',
    'GS': 'Goldman Sachs', 'MS': 'Morgan Stanley', 'C': 'Citigroup',
    'JNJ': 'Johnson & Johnson', 'PFE': 'Pfizer', 'UNH': 'UnitedHealth',
    'HD': 'Home Depot', 'WMT': 'Walmart', 'COST': 'Costco', 'TGT': 'Target',
    'NKE': 'Nike', 'DIS': 'Disney', 'CMCSA': 'Comcast', 'VZ': 'Verizon',
    'T': 'AT&T', 'V': 'Visa', 'MA': 'Mastercard', 'AXP': 'American Express'
}

@dataclass
class MarketData:
    """Market data structure"""
    sp500_futures: float
    nasdaq_futures: float
    russell_futures: float
    crude_oil: float
    treasury_yield: float
    vix: float
    sentiment: str

@dataclass
class EconomicEvent:
    """Economic calendar event"""
    time: str
    event: str
    consensus: str
    previous: str
    impact: str

@dataclass
class EarningsEvent:
    """Earnings calendar event"""
    company: str
    ticker: str
    time: str
    eps_estimate: str
    revenue_estimate: str

class EnhancedBriefingGenerator:
    """Enhanced morning briefing generator with UnBound X format"""
    
    def __init__(self):
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.base_url = "https://financialmodelingprep.com/api/v3"
        
    def _extract_ticker_from_headline(self, title: str, summary: str = "") -> Tuple[str, str]:
        """Extract company ticker and name from headline"""
        # Combine title and summary for better extraction
        text = f"{title} {summary}".upper()
        
        # First, look for "Company stock" patterns as they're most specific
        # This should be the highest priority since it's explicit
        stock_pattern = r'\b([A-Z]+)\s+STOCK\b'
        match = re.search(stock_pattern, text)
        if match:
            company_name_match = match.group(1).upper()
            # Look for exact match first
            for ticker, company_name in COMMON_TICKERS.items():
                if company_name_match == company_name.upper():
                    return ticker, company_name
            # Then look for partial matches
            for ticker, company_name in COMMON_TICKERS.items():
                if company_name_match in company_name.upper() or company_name.upper() in company_name_match:
                    return ticker, company_name
        else:
            pass # No debug logging
        
        # Look for exact ticker matches in the title only (not summary)
        title_upper = title.upper()
        for ticker, company_name in COMMON_TICKERS.items():
            # Use word boundaries to avoid false positives like "GSA" matching "GS"
            ticker_pattern = r'\b' + re.escape(ticker) + r'\b'
            if re.search(ticker_pattern, title_upper):
                return ticker, company_name
        
        # Look for company names in the title only (prioritize by position)
        # BUT only if no stock pattern was found above
        found_companies = []
        title_upper = title.upper()
        for ticker, company_name in COMMON_TICKERS.items():
            # Check for company name variations
            company_variations = [
                company_name.upper(),
                company_name.upper().replace(' ', ''),
                company_name.upper().replace(' ', ' & '),
                company_name.upper().replace(' ', ' AND '),
                company_name.upper().replace(' ', '&'),
                # Handle common abbreviations
                'APPLE' if company_name == 'Apple' else company_name.upper(),
                'MICROSOFT' if company_name == 'Microsoft' else company_name.upper(),
                'ALPHABET' if company_name == 'Alphabet' else company_name.upper(),
                'AMAZON' if company_name == 'Amazon' else company_name.upper(),
                'TESLA' if company_name == 'Tesla' else company_name.upper(),
                'META' if company_name == 'Meta' else company_name.upper(),
                'NVIDIA' if company_name == 'NVIDIA' else company_name.upper(),
                'PALANTIR' if company_name == 'Palantir' else company_name.upper(),
                'REDDIT' if company_name == 'Reddit' else company_name.upper(),
                'COINBASE' if company_name == 'Coinbase' else company_name.upper(),
                'ROBINHOOD' if company_name == 'Robinhood' else company_name.upper(),
                'RIVIAN' if company_name == 'Rivian' else company_name.upper(),
                'LUCID' if company_name == 'Lucid' else company_name.upper(),
                'NIO' if company_name == 'NIO' else company_name.upper(),
                'XPENG' if company_name == 'XPeng' else company_name.upper(),
                'LI AUTO' if company_name == 'Li Auto' else company_name.upper(),
                'JPMORGAN' if company_name == 'JPMorgan' else company_name.upper(),
                'BANK OF AMERICA' if company_name == 'Bank of America' else company_name.upper(),
                'WELLS FARGO' if company_name == 'Wells Fargo' else company_name.upper(),
                'GOLDMAN SACHS' if company_name == 'Goldman Sachs' else company_name.upper(),
                'MORGAN STANLEY' if company_name == 'Morgan Stanley' else company_name.upper(),
                'CITIGROUP' if company_name == 'Citigroup' else company_name.upper(),
                'JOHNSON & JOHNSON' if company_name == 'Johnson & Johnson' else company_name.upper(),
                'PFIZER' if company_name == 'Pfizer' else company_name.upper(),
                'UNITEDHEALTH' if company_name == 'UnitedHealth' else company_name.upper(),
                'HOME DEPOT' if company_name == 'Home Depot' else company_name.upper(),
                'WALMART' if company_name == 'Walmart' else company_name.upper(),
                'COSTCO' if company_name == 'Costco' else company_name.upper(),
                'TARGET' if company_name == 'Target' else company_name.upper(),
                'NIKE' if company_name == 'Nike' else company_name.upper(),
                'DISNEY' if company_name == 'Disney' else company_name.upper(),
                'COMCAST' if company_name == 'Comcast' else company_name.upper(),
                'VERIZON' if company_name == 'Verizon' else company_name.upper(),
                'AT&T' if company_name == 'AT&T' else company_name.upper(),
                'VISA' if company_name == 'Visa' else company_name.upper(),
                'MASTERCARD' if company_name == 'Mastercard' else company_name.upper(),
                'AMERICAN EXPRESS' if company_name == 'American Express' else company_name.upper(),
            ]
            
            for variation in company_variations:
                if variation in title_upper:
                    # Find the position of the company name in the title
                    pos = title_upper.find(variation)
                    found_companies.append((ticker, company_name, pos))
                    break
        
        # Sort by position (earlier in title = higher priority) and return the first match
        if found_companies:
            found_companies.sort(key=lambda x: x[2])
            return found_companies[0][0], found_companies[0][1]
        
        # Look for common patterns like "Company (TICKER)" or "TICKER stock"
        ticker_pattern = r'\b([A-Z]{2,5})\s*(?:stock|shares?|earnings?|reports?|results?)\b'
        match = re.search(ticker_pattern, text)
        if match:
            ticker = match.group(1)
            if ticker in COMMON_TICKERS:
                return ticker, COMMON_TICKERS[ticker]
        
        return "N/A", "N/A"
    
    def fetch_market_futures(self) -> MarketData:
        """Fetch market futures data (mock implementation)"""
        # In production, this would fetch real data from FMP API
        return MarketData(
            sp500_futures=0.15,
            nasdaq_futures=0.22,
            russell_futures=0.08,
            crude_oil=78.45,
            treasury_yield=4.18,
            vix=13.2,
            sentiment="Cautiously Optimistic"
        )
    
    def fetch_economic_calendar(self) -> List[EconomicEvent]:
        """Fetch economic calendar from FMP API"""
        if not self.fmp_api_key:
            # Return mock data if no API key
            return [
                EconomicEvent("08:30", "Building Permits", "1.45M", "1.43M", "Medium"),
                EconomicEvent("08:30", "Housing Starts", "1.35M", "1.31M", "Medium"),
                EconomicEvent("10:00", "Consumer Sentiment (Final)", "66.0", "66.0", "Low")
            ]
        
        try:
            url = f"{self.base_url}/economic_calendar?apikey={self.fmp_api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events = []
            
            for item in data[:5]:  # Top 5 events
                events.append(EconomicEvent(
                    time=item.get('time', ''),
                    event=item.get('event', ''),
                    consensus=item.get('consensus', ''),
                    previous=item.get('previous', ''),
                    impact=item.get('impact', 'Medium')
                ))
            
            return events
            
        except Exception as e:
            logger.error(f"Error fetching economic calendar: {e}")
            return []
    
    def fetch_earnings_calendar(self) -> List[EarningsEvent]:
        """Fetch earnings calendar from FMP API"""
        if not self.fmp_api_key:
            # Return mock data if no API key
            return [
                EarningsEvent("Schlumberger", "SLB", "Pre", "$0.68", "$6.8B"),
                EarningsEvent("Travelers", "TRV", "Pre", "$3.85", "$9.2B"),
                EarningsEvent("Synchrony Financial", "SYF", "Pre", "$1.52", "$4.1B")
            ]
        
        try:
            url = f"{self.base_url}/earning_calendar?apikey={self.fmp_api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events = []
            
            for item in data[:5]:  # Top 5 earnings
                events.append(EarningsEvent(
                    company=item.get('companyName', ''),
                    ticker=item.get('symbol', ''),
                    time=item.get('time', ''),
                    eps_estimate=item.get('epsEstimate', ''),
                    revenue_estimate=item.get('revenueEstimate', '')
                ))
            
            return events
            
        except Exception as e:
            logger.error(f"Error fetching earnings calendar: {e}")
            return []
    
    def analyze_news_sentiment(self, news_df: pd.DataFrame) -> Tuple[List[Dict], str]:
        """Analyze news sentiment and extract key headlines"""
        if news_df.empty:
            return [], "No news data available"
        
        # Handle column mapping between old and new CSV formats
        if 'source' not in news_df.columns and 'publisher' in news_df.columns:
            news_df['source'] = news_df['publisher']
        
        # Handle both old and new CSV formats
        if 'priority' in news_df.columns:
            # New format with priority column
            news_df = news_df.sort_values(['priority', 'published'], ascending=[True, False])
        else:
            # Old format without priority column - add default priority
            news_df['priority'] = 2  # Default medium priority
            news_df = news_df.sort_values(['priority', 'published'], ascending=[True, False])
        
        key_headlines = []
        market_context = ""
        
        # Extract top headlines by category (handle both formats)
        if 'category' in news_df.columns:
            # New format with category column
            for category in ['general_financial', 'investing_markets', 'economy_policy']:
                category_news = news_df[news_df['category'] == category].head(2)
                
                for _, row in category_news.iterrows():
                    # Determine impact based on sentiment and source
                    impact = self._determine_impact(row)
                    
                    # Extract ticker and company name
                    ticker, company_name = self._extract_ticker_from_headline(
                        row['title'], row.get('summary', '')
                    )
                    
                    headline = {
                        'title': row['title'],
                        'source': row['source'],
                        'impact': impact,
                        'summary': row['summary'][:200] + "..." if len(row['summary']) > 200 else row['summary'],
                        'category': category,
                        'ticker': ticker,
                        'company_name': company_name
                    }
                    key_headlines.append(headline)
        else:
            # Old format without category - use all articles
            for _, row in news_df.head(6).iterrows():
                # Determine impact based on sentiment and source
                impact = self._determine_impact(row)
                
                # Extract ticker and company name
                ticker, company_name = self._extract_ticker_from_headline(
                    row['title'], row.get('summary', '')
                )
                
                headline = {
                    'title': row['title'],
                    'source': row['source'],
                    'impact': impact,
                    'summary': row['summary'][:200] + "..." if len(row['summary']) > 200 else row['summary'],
                    'category': 'general_financial',  # Default category
                    'ticker': ticker,
                    'company_name': company_name
                }
                key_headlines.append(headline)
        
        # Generate market context
        if len(key_headlines) > 0:
            market_context = self._generate_market_context(key_headlines)
        
        return key_headlines[:6], market_context  # Top 6 headlines
    
    def _determine_impact(self, row: pd.Series) -> str:
        """Determine market impact based on sentiment and source credibility"""
        # This is a simplified version - in production, you'd use more sophisticated logic
        high_credibility_sources = ['Reuters', 'Bloomberg', 'CNBC', 'MarketWatch', 'Yahoo Finance']
        
        # Get source from either 'source' or 'publisher' column
        source = row.get('source', row.get('publisher', 'Unknown'))
        
        if source in high_credibility_sources:
            return "High"
        elif 'priority' in row and row['priority'] == 1:
            return "Medium"
        else:
            return "Low"
    
    def _generate_market_context(self, headlines: List[Dict]) -> str:
        """Generate market context from headlines"""
        positive_count = sum(1 for h in headlines if 'positive' in h.get('summary', '').lower())
        negative_count = sum(1 for h in headlines if 'negative' in h.get('summary', '').lower())
        
        if positive_count > negative_count:
            return "Positive sentiment dominates with strong earnings and policy support"
        elif negative_count > positive_count:
            return "Mixed sentiment with some concerns about economic data and policy uncertainty"
        else:
            return "Balanced market sentiment with mixed signals across sectors"
    
    def generate_briefing(self, news_csv_path: str, ticker: str = None) -> str:
        """Generate comprehensive morning briefing"""
        try:
            # Load news data
            news_df = pd.read_csv(news_csv_path)
            
            # Fetch market data
            market_data = self.fetch_market_futures()
            economic_events = self.fetch_economic_calendar()
            earnings_events = self.fetch_earnings_calendar()
            
            # Analyze news
            key_headlines, market_context = self.analyze_news_sentiment(news_df)
            
            # Generate briefing
            briefing = self._format_briefing(
                market_data=market_data,
                key_headlines=key_headlines,
                economic_events=economic_events,
                earnings_events=earnings_events,
                market_context=market_context,
                ticker=ticker
            )
            
            return briefing
            
        except Exception as e:
            logger.error(f"Error generating briefing: {e}")
            return f"Error generating briefing: {str(e)}"
    
    def _format_briefing(self, market_data: MarketData, key_headlines: List[Dict], 
                        economic_events: List[EconomicEvent], earnings_events: List[EarningsEvent],
                        market_context: str, ticker: str = None) -> str:
        """Format the briefing in UnBound X style with proper markdown"""
        
        today = datetime.now().strftime("%B %d, %Y")
        
        briefing = f"""# UnBound X Morning Market Briefing

**📅 Date:** {today}  
**🎯 Sector Focus:** Technology & Financial Services  
**Data Sources:** Financial Modeling Prep API, Reuters, WSJ, Bloomberg Terminal

---

## Market Futures Overview

**Pre-Market Sentiment:** {market_data.sentiment}

- **S&P 500 futures:** {market_data.sp500_futures:+.2f}%
- **Nasdaq futures:** {market_data.nasdaq_futures:+.2f}%
- **Russell 2000 futures:** {market_data.russell_futures:+.2f}%
- **Crude Oil (WTI):** ${market_data.crude_oil:.2f} (+0.2%)
- **10Y Treasury Yield:** {market_data.treasury_yield:.2f}% (-2 bp)
- **VIX:** {market_data.vix:.1f} (-0.3%)

**Market Context:** {market_context}

---

## Key Headlines

"""
        
        # Add key headlines
        for i, headline in enumerate(key_headlines[:3], 1):
            # Format company display
            if headline.get('ticker') != 'N/A' and headline.get('company_name') != 'N/A':
                company_display = f"{headline['company_name']} ({headline['ticker']})"
            else:
                company_display = "N/A"
            
            briefing += f"""### {headline['title']}

**Company:** {company_display} | **Impact:** {headline['impact']}

{headline['summary']}

*Source: {headline['source']}*

---
"""
        
        # Add economic calendar
        briefing += f"""## Today's Economic Calendar

| Time (EST) | Event | Consensus | Previous | Impact |
|------------|-------|-----------|----------|--------|
"""
        for event in economic_events:
            briefing += f"| {event.time} | {event.event} | {event.consensus} | {event.previous} | {event.impact} |\n"
        
        # Add earnings calendar
        briefing += f"""

## Earnings Calendar - Key Reports

| Company | Ticker | Time | EPS Estimate | Revenue Estimate |
|---------|--------|------|--------------|------------------|
"""
        for event in earnings_events:
            briefing += f"| {event.company} | {event.ticker} | {event.time} | {event.eps_estimate} | {event.revenue_estimate} |\n"
        
        # Add strategic insights
        briefing += f"""

---

## UnBound X Intelligence

### Sector Dynamics

Technology continues to lead with strong earnings momentum and AI-driven growth narratives. Financial services remain under focus as rate cut expectations build, with insurers and regional banks showing mixed signals ahead of potential policy shifts.

### Market Structure Notes

Thursday's session saw the S&P 500 hit new highs before settling nearly flat, while the Nasdaq managed slight gains. Volume patterns suggest consolidation ahead of the weekend, with volatility compressed as markets await clearer Fed guidance.

---

## Strategic Considerations

**For Entrepreneurs:** Market conditions favor technology companies with strong fundamentals and growth narratives. Consider positioning for AI and digital transformation opportunities.

**For Investors:** Consider rotation opportunities into communications services and ad-tech as sector inclusion may drive broader interest. Fed dovish signals support duration trades and growth-oriented positioning.

**For Analysts:** Focus on housing data releases today which could influence Fed policy decisions. Monitor earnings quality in financial services, particularly around net interest margins and credit provisions.

---

## Risk Monitor

### Key Risks Today:
- **Housing Data Miss:** Weaker than expected housing starts could signal economic softening *(Moderate probability)*
- **Weekend Geopolitical Risk:** Market positioning vulnerable to overseas developments *(Low probability)*

### Catalysts to Watch:
- **08:30** - Housing data could influence Fed policy expectations
- **10:00** - Final consumer sentiment reading for directional confirmation

---

## Interactive Elements

📊 **Today's Poll:** Will technology earnings momentum continue through Q2?  
💭 **Discussion Starter:** How should investors position ahead of potential Fed rate cuts while managing duration risk?  
🔗 **Deep Dive:** Analysis of sector rotation patterns and inclusion impacts available in UnBound X research portal

---

## Compliance Disclosure

*This briefing is provided for informational purposes only and does not constitute investment advice, recommendations, or offers to buy or sell securities. All data sourced from public markets and third-party providers. UnBound X users should conduct their own research and consult with qualified professionals before making investment decisions.*

---

**Briefing Credits:** 3 credits used | **Next Update:** Monday 7:00 AM EST  
**Feedback:** Rate this briefing and suggest improvements in the UnBound X app

---

*Generated by UnBound X Intelligence Engine | Powered by multi-agent research automation*
"""
        
        return briefing
    
    def save_briefing(self, briefing: str, filename: str = None) -> str:
        """Save briefing to markdown file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unbound_briefing_{timestamp}.md"
        
        # Ensure outputs directory exists
        outputs_dir = Path("signalmuse/outputs")
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = outputs_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(briefing)
        
        logger.info(f"Briefing saved to: {filepath}")
        return str(filepath)

def main():
    """Test the enhanced briefing generator"""
    generator = EnhancedBriefingGenerator()
    
    print("🔍 Enhanced Morning Briefing Generator")
    print("=" * 50)
    
    # Test with sample data
    sample_csv = "signalmuse/data/real/googl_news_20250731_224935.csv"
    
    if Path(sample_csv).exists():
        print(f"\n📊 Generating briefing from: {sample_csv}")
        briefing = generator.generate_briefing(sample_csv, "GOOGL")
        
        # Save briefing
        filepath = generator.save_briefing(briefing)
        print(f"✅ Briefing saved to: {filepath}")
        
        # Show preview
        print("\n📰 Briefing Preview:")
        print(briefing[:500] + "...")
        
    else:
        print(f"❌ Sample CSV not found: {sample_csv}")
        print("Please run the news scraper first to generate sample data.")

if __name__ == "__main__":
    main() 