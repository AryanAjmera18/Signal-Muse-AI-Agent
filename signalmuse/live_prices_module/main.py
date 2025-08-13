#!/usr/bin/env python3
"""
Live Prices Module - Lean Implementation

Single-file module for fetching real-time market data and generating
deterministic markdown formatting for the live prices section.
"""

import yfinance as yf
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Optional
import logging

# Use centralized logging
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Market data structure for live prices"""
    # Futures data (percent changes)
    sp500_futures: float
    nasdaq_futures: float
    russell_futures: float
    
    # Current prices
    sp500_current: float
    nasdaq_current: float
    russell_current: float
    
    # Commodities and indicators
    crude_oil: float
    treasury_yield: float
    vix: float
    
    # Calculated sentiment
    sentiment: str


def fetch_market_data() -> MarketData:
    """
    Fetch market data using yfinance in a single batch call
    
    Returns:
        MarketData: Fetched market data with calculated sentiment
    """
    try:
        # Symbol mappings for all required data
        symbols = {
            'sp500_futures': 'ES=F',     # E-mini S&P 500 futures
            'nasdaq_futures': 'NQ=F',    # E-mini Nasdaq-100 futures  
            'russell_futures': 'RTY=F',  # E-mini Russell 2000 futures
            'sp500_current': '^GSPC',    # S&P 500 Index
            'nasdaq_current': '^IXIC',   # Nasdaq Composite
            'russell_current': '^RUT',   # Russell 2000
            'crude_oil': 'CL=F',         # WTI Crude Oil
            'treasury_yield': '^TNX',    # 10-Year Treasury Yield
            'vix': '^VIX'                # Volatility Index
        }
        
        # Download all data in one batch call
        tickers = list(symbols.values())
        data = yf.download(
            tickers=tickers,
            period='2d',  # Get 2 days to calculate change from previous close
            interval='1d',
            group_by='ticker',
            auto_adjust=True,
            progress=False
        )
        
        # Calculate percent changes for futures (previous close vs last close)
        def safe_get_change(symbol_key: str) -> float:
            """Safely calculate percentage change from previous close"""
            try:
                symbol = symbols[symbol_key]
                close_key = (symbol, 'Close')
                open_key = (symbol, 'Open')
                
                if close_key in data and len(data[close_key]) >= 2:
                    prev_close = data[close_key].iloc[-2]
                    current_close = data[close_key].iloc[-1]
                    pct_change = ((current_close - prev_close) / prev_close) * 100
                    return pct_change
                elif close_key in data and open_key in data and len(data[close_key]) >= 1:
                    # Fallback: use day's open vs close
                    current_open = data[open_key].iloc[-1]
                    current_close = data[close_key].iloc[-1]
                    pct_change = ((current_close - current_open) / current_open) * 100
                    return pct_change
                else:
                    logger.warning(f"No data available for {symbol_key} ({symbol})")
                    return 0.0
            except Exception as e:
                logger.warning(f"Could not calculate change for {symbol_key}: {e}")
                return 0.0
        
        def safe_get_price(symbol_key: str, default_value: float = 0.0) -> float:
            """Safely get current price"""
            try:
                symbol = symbols[symbol_key]
                close_key = (symbol, 'Close')
                
                if close_key in data and len(data[close_key]) > 0:
                    value = data[close_key].iloc[-1]
                    # Handle NaN values
                    if pd.isna(value):
                        logger.warning(f"NaN value for {symbol_key} ({symbol})")
                        return default_value
                    return float(value)
                else:
                    logger.warning(f"No data available for {symbol_key} ({symbol})")
                    return default_value
            except Exception as e:
                logger.warning(f"Could not fetch price for {symbol_key}: {e}")
                return default_value
        
        # Get futures percent changes
        sp500_futures = safe_get_change('sp500_futures')
        nasdaq_futures = safe_get_change('nasdaq_futures')
        russell_futures = safe_get_change('russell_futures')
        
        # Get current index levels
        sp500_current = safe_get_price('sp500_current', 0.0)
        nasdaq_current = safe_get_price('nasdaq_current', 0.0)
        russell_current = safe_get_price('russell_current', 0.0)
        
        # Get commodities and indicators
        crude_oil = safe_get_price('crude_oil', 0.0)
        treasury_yield = safe_get_price('treasury_yield', 0.0)  # Already in percent
        vix = safe_get_price('vix', 0.0)
        
        # Calculate sentiment based on average futures change
        avg_change = (sp500_futures + nasdaq_futures + russell_futures) / 3
        sentiment = calculate_sentiment(avg_change)
        
        return MarketData(
            sp500_futures=sp500_futures,
            nasdaq_futures=nasdaq_futures,
            russell_futures=russell_futures,
            sp500_current=sp500_current,
            nasdaq_current=nasdaq_current,
            russell_current=russell_current,
            crude_oil=crude_oil,
            treasury_yield=treasury_yield,
            vix=vix,
            sentiment=sentiment
        )
        
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        # Return default values on failure
        return MarketData(
            sp500_futures=0.0,
            nasdaq_futures=0.0,
            russell_futures=0.0,
            sp500_current=0.0,
            nasdaq_current=0.0,
            russell_current=0.0,
            crude_oil=0.0,
            treasury_yield=0.0,
            vix=0.0,
            sentiment="Data Unavailable"
        )


def calculate_sentiment(avg_change: float) -> str:
    """
    Calculate sentiment based on average percent change
    
    Args:
        avg_change: Average percent change across major indices
        
    Returns:
        str: Sentiment classification
    """
    if avg_change > 1.0:
        return "Bullish"
    elif avg_change > 0.3:
        return "Cautiously Optimistic"
    elif avg_change > -0.3:
        return "Neutral"
    elif avg_change > -1.0:
        return "Cautiously Pessimistic"
    else:
        return "Bearish"


def format_live_prices_section(market_data: MarketData) -> str:
    """
    Format market data into exact markdown structure as specified
    
    Args:
        market_data: Market data to format
        
    Returns:
        str: Formatted markdown content
    """
    return f"""## Market Futures Overview

### Pre-Market Sentiment: {market_data.sentiment}

S&P 500 futures: {market_data.sp500_futures:+.2f}%
Nasdaq futures: {market_data.nasdaq_futures:+.2f}%
Russell 2000 futures: {market_data.russell_futures:+.2f}%
Crude Oil (WTI): ${market_data.crude_oil:.2f}
10Y Treasury Yield: {market_data.treasury_yield:.2f}%
VIX: {market_data.vix:.1f}


## Current Market Data

#### Current Index Levels:

S&P 500: {market_data.sp500_current:.2f}
Nasdaq Composite: {market_data.nasdaq_current:.2f}
Russell 2000: {market_data.russell_current:.2f}

---
"""


def run_live_prices_module() -> str:
    """
    Main function to fetch and format live prices data
    
    Returns:
        str: Formatted markdown content for live prices section
    """
    try:
        logger.info("Fetching live market data...")
        
        # Fetch market data
        market_data = fetch_market_data()
        
        # Format into markdown
        formatted_content = format_live_prices_section(market_data)
        
        logger.info(f"Live prices module completed successfully. Sentiment: {market_data.sentiment}")
        return formatted_content
        
    except Exception as e:
        logger.error(f"Live prices module failed: {e}")
        # Return a fallback message
        return """## Market Futures Overview

### Pre-Market Sentiment: Data Unavailable

S&P 500 futures: 0.00%
Nasdaq futures: 0.00%
Russell 2000 futures: 0.00%
Crude Oil (WTI): $0.00
10Y Treasury Yield: 0.00%
VIX: 0.0


## Current Market Data

#### Current Index Levels:

S&P 500: 0.00
Nasdaq Composite: 0.00
Russell 2000: 0.00

---
"""


if __name__ == "__main__":
    """Test the live prices module"""
    print("🔍 Live Prices Module Test")
    print("=" * 50)
    
    try:
        content = run_live_prices_module()
        print("✅ Live prices module test successful!")
        print("\n📰 Generated Content:")
        print(content)
        
    except Exception as e:
        print(f"❌ Live prices module test failed: {e}")
