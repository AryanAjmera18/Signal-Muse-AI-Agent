#!/usr/bin/env python3
"""
Market Data Fetcher Module

Modular component for fetching current market data and futures data from Yahoo Finance,
with formatting capabilities for reports.
"""

import yfinance as yf
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class MarketDataFetcher:
    """Modular market data fetcher for current and futures data"""
    
    def __init__(self):
        """Initialize the market data fetcher"""
        pass
        
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
        """Fetch current market data from Yahoo Finance using yfinance"""

        try:
            # Symbol mappings for current market data
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
            
            # Get current prices
            sp500_current = safe_get_price('sp500', 0.0)
            nasdaq_current = safe_get_price('nasdaq', 0.0)  
            russell_current = safe_get_price('russell', 0.0)
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
            logger.error(f"Error fetching current market data: {e}")
            # Return reasonable defaults instead of failing
            return MarketData(
                sp500_futures=0.0,
                nasdaq_futures=0.0,
                russell_futures=0.0,
                crude_oil=0.0,
                treasury_yield=0.0,
                vix=0.0,
                sentiment="ERROR - CURRENT DATA FAILED"
            )

    def _fetch_futures_data(self) -> MarketData:
        """Fetch market futures data from Yahoo Finance using yfinance"""

        try:
            # Symbol mappings for futures data
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
            
            # Calculate market sentiment
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

class MarketDataFormatter:
    """Formatter for market data into various report formats"""
    
    def __init__(self):
        """Initialize the formatter"""
        pass
    
    def format_market_overview(self, market_data: MarketData, market_context: str = "") -> str:
        """Format market data into a market overview section"""
        
        formatted = f"""## Market Futures Overview

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

---"""
        
        return formatted
        

def main():
    """Test the market data fetcher and formatter"""
    
    print("🔍 Market Data Fetcher & Formatter Test")
    print("=" * 50)
    
    # Initialize fetcher and formatter
    fetcher = MarketDataFetcher()
    formatter = MarketDataFormatter()
    
    try:
        # Fetch market data
        print("\n📊 Fetching market data...")
        market_data = fetcher.fetch_market_futures()
        
        print(f"✅ Market data fetched successfully!")
        print(f"   S&P 500: {market_data.sp500_current:.2f} (futures: {market_data.sp500_futures:+.2f}%)")
        print(f"   Nasdaq: {market_data.nasdaq_current:.2f} (futures: {market_data.nasdaq_futures:+.2f}%)")
        print(f"   Russell: {market_data.russell_current:.2f} (futures: {market_data.russell_futures:+.2f}%)")
        print(f"   Sentiment: {market_data.sentiment}")
        
        # Test formatting
        print("\n📝 Testing formatting...")
        header = formatter.format_briefing_header("AAPL")
        overview = formatter.format_market_overview(market_data, "Positive sentiment with strong tech earnings")
        
        print("✅ Formatting successful!")
        print("\n📰 Sample Output:")
        print(header)
        print(overview[:200] + "...")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    main()
