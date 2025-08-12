#!/usr/bin/env python3
"""
Enhanced Morning Briefing Generator

Generates comprehensive morning market briefings in the UnBound X format
with futures data and strategic insights.
"""

import pandas as pd
import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from pydantic import BaseModel
import instructor
from groq import Groq
import yfinance as yf

from signalmuse.utils.utils import get_logger, config, save_dataframe_to_csv, generate_timestamp_filename

logger = get_logger(__name__)

# YFinance fallback removed - not used in main pipeline

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

class TickerExtraction(BaseModel):
    """Pydantic model for ticker extraction response"""
    ticker: str
    company_name: str
    confidence: float

@dataclass
class MarketData:
    """Market data structure"""
    sp500_futures: float
    nasdaq_futures: float
    russell_futures: float
    crude_oil: float
    treasury_yield: float
    vix: float
    sentiment: str = "Neutral"
    # Current market data
    sp500_current: float = 0.0
    nasdaq_current: float = 0.0
    russell_current: float = 0.0

class EnhancedBriefingGenerator:
    """Enhanced morning briefing generator with UnBound X format"""
    
    def __init__(self):
        self.fmp_api_key = config.fmp_api_key
        self.groq_api_key = config.groq_api_key
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.groq_client = self._setup_groq_client() if self.groq_api_key else None
        
    def _setup_groq_client(self):
        """Initialize Groq client for intelligent ticker extraction"""
        # Use centralized Groq client from news_csv_updater_module
        from signalmuse.news_csv_updater_module.groq_client import GroqClientManager
        groq_manager = GroqClientManager()
        return groq_manager.get_client() if groq_manager.is_available() else None
        
    def _extract_ticker_from_headline(self, title: str, summary: str = "") -> Tuple[str, str]:
        """Extract company ticker and name from headline using centralized ticker extraction"""
        
        # Use centralized ticker extraction from news_csv_updater_module
        try:
            from signalmuse.news_csv_updater_module.chunk_processor import ChunkProcessor
            from signalmuse.news_csv_updater_module.groq_client import GroqClientManager
            
            groq_manager = GroqClientManager()
            if not groq_manager.is_available():
                return "N/A", "N/A"
            
            chunk_processor = ChunkProcessor(groq_manager)
            
            # Create a single article for processing
            article = {
                'id': 1,
                'title': title,
                'summary': summary
            }
            
            # Process through LLM for ticker extraction
            results = chunk_processor.process_chunk_with_llm([article])
            
            if results and len(results) > 0:
                result = results[0]
                ticker = result.get('ticker', 'N/A')
                # Map ticker to company name using COMMON_TICKERS
                company_name = COMMON_TICKERS.get(ticker, ticker) if ticker != 'N/A' else 'N/A'
                return ticker, company_name
            else:
                return "N/A", "N/A"
                
        except Exception as e:
            logger.warning(f"Centralized ticker extraction failed: {e}, using fallback")
            return self._extract_ticker_fallback(title, summary)
    
    def _extract_ticker_fallback(self, title: str, summary: str = "") -> Tuple[str, str]:
        """Simple regex-based fallback ticker extraction"""
        text = f"{title} {summary}".upper()
        
        # Look for exact ticker matches first
        for ticker, company_name in COMMON_TICKERS.items():
            ticker_pattern = r'\b' + re.escape(ticker) + r'\b'
            if re.search(ticker_pattern, text):
                return ticker, company_name
        
        # Look for common company names
        for ticker, company_name in COMMON_TICKERS.items():
            if company_name.upper() in text:
                return ticker, company_name
        
        # Look for "stock" patterns
        stock_pattern = r'\b([A-Z]{2,5})\s+(?:stock|shares?)\b'
        match = re.search(stock_pattern, text)
        if match and match.group(1) in COMMON_TICKERS:
            ticker = match.group(1)
            return ticker, COMMON_TICKERS[ticker]
        
        return "N/A", "N/A"
    
    def fetch_market_futures(self) -> MarketData:
        """Fetch market futures and current data using Yahoo Finance"""
        
        try:
            # Fetch futures data
            futures_data = self._fetch_futures_data()
            
            # Fetch current market data  
            current_data = self._fetch_current_market_data()
            
            # Combine both datasets
            return MarketData(
                sp500_futures=futures_data.sp500_futures,
                nasdaq_futures=futures_data.nasdaq_futures,
                russell_futures=futures_data.russell_futures,
                crude_oil=futures_data.crude_oil,
                treasury_yield=futures_data.treasury_yield,
                vix=futures_data.vix,
                sentiment=futures_data.sentiment,
                sp500_current=current_data.sp500_futures,  # Using futures field as current
                nasdaq_current=current_data.nasdaq_futures,  # Using futures field as current
                russell_current=current_data.russell_futures  # Using futures field as current
            )
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            # Return all zeros for debugging
            return MarketData(
                sp500_futures=0.0,
                nasdaq_futures=0.0,
                russell_futures=0.0,
                crude_oil=0.0,
                treasury_yield=0.0,
                vix=0.0,
                sentiment="ERROR - CHECK LOGS",
                sp500_current=0.0,
                nasdaq_current=0.0,
                russell_current=0.0
            )

    def _fetch_current_market_data(self) -> MarketData:
        """Fetch market futures data from Yahoo Finance using yfinance"""

        try:
            # Symbol mappings
            symbols = {
                'sp500': '^GSPC',           # S&P 500 Index
                'nasdaq': '^IXIC',          # Nasdaq Composite
                'russell': '^RUT',          # Russell 2000
                'vix': '^VIX',              # CBOE Volatility Index
                'crude_oil': 'CL=F',        # WTI Crude Oil Futures
                'treasury_10y': '^TNX'      # 10-Year Treasury Yield
            }
            
            # Initialize default values
            sp500_current = 0.0
            nasdaq_current = 0.0
            russell_current = 0.0
            crude_oil_price = 0.0
            treasury_yield = 0.0
            vix_price = 0.0
            
            # Download data for all symbols at once (more efficient)
            tickers = list(symbols.values())
            data = yf.download(
                tickers=tickers,
                period='2d',  # Get 2 days to calculate change from previous close
                interval='1d',
                group_by='ticker',
                auto_adjust=True,
                progress=False
            )
            def safe_get_price(symbol_key, default_value):
                """Safely get current price"""
                try:
                    symbol = symbols[symbol_key]
                    return float(data[symbol]['Close'].iloc[-1])
                except Exception as e:
                    logger.warning(f"Could not fetch price for {symbol_key}: {e}")
                    return default_value
            
            # Calculate percentage changes (futures-like behavior)
            sp500_current = safe_get_price('sp500', 0.0)
            nasdaq_current = safe_get_price('nasdaq', 0.0)  
            russell_current = safe_get_price('russell', 0.0)
            
            # Get current prices
            crude_oil_price = safe_get_price('crude_oil', 0.0)
            vix_price = safe_get_price('vix', 0.0)
            
            # Treasury yield (^TNX gives yield in percent, no division needed)
            try:
                treasury_yield = safe_get_price('treasury_10y', 0.0)
            except Exception as e:
                logger.warning(f"Could not fetch Treasury yield: {e}")
                treasury_yield = 0.0
            
            return MarketData(
                sp500_futures=sp500_current,
                nasdaq_futures=nasdaq_current,
                russell_futures=russell_current,
                crude_oil=crude_oil_price,
                treasury_yield=treasury_yield,
                vix=vix_price
            )
            
        except Exception as e:
            logger.error(f"Error fetching market futures data: {e}")
            # Return reasonable defaults instead of failing (same as original)
            return MarketData(
                sp500_futures=0.0,
                nasdaq_futures=0.0,
                russell_futures=0.0,
                crude_oil=0.0,
                treasury_yield=0.0,
                vix=0.0,
                sentiment="BAD THING HAPPENED - DEBUG COMMENT"
            )

    def _fetch_futures_data(self) -> MarketData:
        """Fetch market futures data from Yahoo Finance using yfinance"""

        try:
            # Symbol mappings
            symbols = {
                'sp500': 'ES=F',     # E-mini S&P 500 futures
                'nasdaq': 'NQ=F',    # E-mini Nasdaq-100 futures  
                'russell': 'RTY=F',  # E-mini Russell 2000 futures
                'crude_oil': 'CL=F', # WTI Crude (already correct)
                'treasury_10y': '^TNX',
                'vix': '^VIX'
            }

            
            # Initialize default values
            sp500_change = 0.0
            nasdaq_change = 0.0
            russell_change = 0.0
            crude_oil_price = 0.0
            treasury_yield = 0.0
            vix_price = 0.0
            
            # Download data for all symbols at once (more efficient)
            tickers = list(symbols.values())
            data = yf.download(
                tickers=tickers,
                period='2d',  # Get 2 days to calculate change from previous close
                interval='1d',
                group_by='ticker',
                auto_adjust=True,
                progress=False
            )
            
            def safe_get_change(symbol_key):
                """Safely calculate percentage change from previous close"""
                try:
                    symbol = symbols[symbol_key]
                    if len(data[symbol]) >= 2:
                        prev_close = data[symbol]['Close'].iloc[-2]
                        current_close = data[symbol]['Close'].iloc[-1]
                        pct_change = ((current_close - prev_close) / prev_close) * 100
                        return pct_change
                    else:
                        # Fallback: use day's open vs close
                        current_open = data[symbol]['Open'].iloc[-1]
                        current_close = data[symbol]['Close'].iloc[-1]
                        pct_change = ((current_close - current_open) / current_open) * 100
                        return pct_change
                except Exception as e:
                    logger.warning(f"Could not calculate change for {symbol_key}: {e}")
                    return 0.0
            
            def safe_get_price(symbol_key, default_value):
                """Safely get current price"""
                try:
                    symbol = symbols[symbol_key]
                    return float(data[symbol]['Close'].iloc[-1])
                except Exception as e:
                    logger.warning(f"Could not fetch price for {symbol_key}: {e}")
                    return default_value
            
            # Calculate percentage changes (futures-like behavior)
            sp500_change = safe_get_change('sp500')
            nasdaq_change = safe_get_change('nasdaq')  
            russell_change = safe_get_change('russell')
            
            # Get current prices
            crude_oil_price = safe_get_price('crude_oil', 0.0)
            vix_price = safe_get_price('vix', 0.0)
            
            # Treasury yield (^TNX gives yield in percent, no division needed)
            try:
                treasury_yield = safe_get_price('treasury_10y', 0.0)
            except Exception as e:
                logger.warning(f"Could not fetch Treasury yield: {e}")
                treasury_yield = 0.0
            
            # Calculate market sentiment (same logic as original)
            avg_change = (sp500_change + nasdaq_change + russell_change) / 3
            if avg_change > 1.0:
                sentiment = "Bullish"
            elif avg_change > 0.3:
                sentiment = "Cautiously Optimistic" 
            elif avg_change > -0.3:
                sentiment = "Neutral"
            elif avg_change > -1.0:
                sentiment = "Cautiously Pessimistic"
            else:
                sentiment = "Bearish"
            
            return MarketData(
                sp500_futures=sp500_change,
                nasdaq_futures=nasdaq_change,
                russell_futures=russell_change,
                crude_oil=crude_oil_price,
                treasury_yield=treasury_yield,
                vix=vix_price,
                sentiment=sentiment
            )
            
        except Exception as e:
            logger.error(f"Error fetching market futures data: {e}")
            # Return zero defaults for debugging
            return MarketData(
                sp500_futures=0.0,
                nasdaq_futures=0.0,
                russell_futures=0.0,
                crude_oil=0.0,
                treasury_yield=0.0,
                vix=0.0,
                sentiment="ERROR - FUTURES DATA FAILED"
            )
    
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
                        'link': row.get('link', ''),
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
                    'link': row.get('link', ''),
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
            
            # Analyze news
            key_headlines, market_context = self.analyze_news_sentiment(news_df)
            
            # Generate briefing
            briefing = self._format_briefing(
                market_data=market_data,
                key_headlines=key_headlines,
                market_context=market_context,
                ticker=ticker
            )
            
            return briefing
            
        except Exception as e:
            logger.error(f"Error generating briefing: {e}")
            return f"Error generating briefing: {str(e)}"
    
    def _format_briefing(self, market_data: MarketData, key_headlines: List[Dict], 
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

## Current Market Data

**Current Index Levels:**

- **S&P 500:** {market_data.sp500_current:.2f}
- **Nasdaq Composite:** {market_data.nasdaq_current:.2f}
- **Russell 2000:** {market_data.russell_current:.2f}

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
**📰 [Read Full Article]({headline['link']})**

---
"""
        
        # Calendar sections will be added by external calendar module when integrated
        
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

## Source Articles

This briefing is based on the following articles:

"""
        
        # Add numbered citations for all articles used
        for i, headline in enumerate(key_headlines, 1):
            briefing += f"{i}. **{headline['title']}** - {headline['source']} | [Read Article]({headline['link']})\n"
        
        briefing += f"""

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
            filename = generate_timestamp_filename("unbound_briefing", "md")
        
        filepath = config.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(briefing)
        
        logger.info(f"Briefing saved to: {filepath}")
        return str(filepath)
    
    # Legacy function removed - now using _fetch_futures_data and _fetch_current_market_data

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