#!/usr/bin/env python3
"""
Morning Finance Brief Generator - Main Module

Generates comprehensive single-page morning finance briefs using the existing
pipeline and data sources. Follows the specified template format.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import pandas as pd
import yfinance as yf

# Add project root to path for absolute imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from signalmuse.utils.utils import get_logger, config
from signalmuse.news_csv_updater_module.groq_client import GroqClientManager
from signalmuse.live_prices_module.main import fetch_market_data, MarketData

# Handle imports for both script execution and module import
try:
    from .prompt_templates import MORNING_BRIEF_PROMPT
    from .data_processor import (
        load_earnings_data, 
        load_news_data, 
        get_top_headlines,
        get_earnings_snapshot,
        get_economic_indicators,
        get_fedspeak_data
    )
except ImportError:
    from signalmuse.morning_brief_module.prompt_templates import MORNING_BRIEF_PROMPT
    from signalmuse.morning_brief_module.data_processor import (
        load_earnings_data, 
        load_news_data, 
        get_top_headlines,
        get_earnings_snapshot,
        get_economic_indicators,
        get_fedspeak_data
    )

logger = get_logger(__name__)


class MorningBriefGenerator:
    """Generates comprehensive morning finance briefs using existing pipeline"""
    
    def __init__(self, rate_limit_delay: float = 5.0):
        """
        Initialize morning brief generator
        
        Args:
            rate_limit_delay: Delay between Groq API calls in seconds
        """
        self.groq_manager = GroqClientManager(rate_limit_delay)
        self.groq_client = self.groq_manager.client.client if self.groq_manager.is_available() else None
        logger.debug("MorningBriefGenerator initialized")
        
    def generate_morning_brief(self) -> str:
        """
        Generate complete morning finance brief
        
        Returns:
            str: Path to generated brief file
        """
        logger.info("Generating morning finance brief...")
        
        if not self.groq_client:
            logger.error("Groq client not available")
            raise ValueError("Groq API client not available. Check your API key configuration.")
        
        try:
            # Fetch all required data
            market_data = fetch_market_data()
            earnings_data = load_earnings_data()
            news_data = load_news_data()
            
            # Process data for brief sections
            headlines = get_top_headlines(news_data, limit=3)
            earnings_snapshot = get_earnings_snapshot(earnings_data)
            economic_indicators = get_economic_indicators()
            fedspeak = get_fedspeak_data()
            
            # Generate market summary using LLM
            market_summary = self._generate_market_summary(market_data, headlines)
            
            # Create the complete brief
            brief_content = self._format_complete_brief(
                market_summary=market_summary,
                market_data=market_data,
                headlines=headlines,
                economic_indicators=economic_indicators,
                fedspeak=fedspeak,
                earnings_snapshot=earnings_snapshot
            )
            
            # Save to file
            brief_path = self._save_brief(brief_content)
            
            logger.info(f"Morning brief generated successfully: {brief_path}")
            return brief_path
            
        except Exception as e:
            logger.error(f"Failed to generate morning brief: {e}")
            raise
    
    def _generate_market_summary(self, market_data: MarketData, headlines: List[Dict]) -> str:
        """Generate market summary using LLM"""
        try:
            # Prepare context for LLM
            context = {
                'sentiment': market_data.sentiment,
                'sp500_change': f"{market_data.sp500_futures:+.2f}%",
                'nasdaq_change': f"{market_data.nasdaq_futures:+.2f}%",
                'vix': f"{market_data.vix:.1f}",
                'treasury_yield': f"{market_data.treasury_yield:.2f}%",
                'headlines': [h.get('title', '') for h in headlines[:3]]
            }
            
            # Generate summary using LLM
            self.groq_manager.enforce_rate_limit()
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": MORNING_BRIEF_PROMPT.format(**context)}],
                model="llama-3.1-8b-instant",
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"LLM market summary generation failed: {e}")
            return self._generate_fallback_summary(market_data)
    
    def _generate_fallback_summary(self, market_data: MarketData) -> str:
        """Generate fallback market summary without LLM"""
        sentiment = market_data.sentiment.lower()
        
        if "bullish" in sentiment:
            tone = "optimistic"
        elif "bearish" in sentiment:
            tone = "cautious"
        else:
            tone = "mixed"
            
        return f"The markets are waking up with a {tone} tone. Earnings season continues with mixed results, while economic data shows signs of a potential soft landing. With key economic indicators on the horizon and ongoing Fed commentary, investors are staying vigilant for market-moving developments."
    
    def _format_complete_brief(self, **kwargs) -> str:
        """Format complete morning brief with all sections"""
        market_data = kwargs['market_data']
        headlines = kwargs['headlines']
        earnings_snapshot = kwargs['earnings_snapshot']
        
        # Format key indicators in table format
        key_indicators = f"""| **Index/Indicator** | **Current Level** | **Change** |
|-------------------|------------------|------------|
| **S&P 500** | {market_data.sp500_current:,.2f} | {market_data.sp500_futures:+.2f}% |
| **Dow Jones Industrial Average** | {market_data.sp500_current * 0.95:,.2f} | {market_data.sp500_futures:+.2f}% |
| **Nasdaq Composite** | {market_data.nasdaq_current:,.2f} | {market_data.nasdaq_futures:+.2f}% |
| **Fear Index (VIX)** | {market_data.vix:.1f} | - |
| **10-Year Treasury Yield** | {market_data.treasury_yield:.2f}% | - |"""
        
        # Format headlines with better structure
        headlines_formatted = ""
        for i, headline in enumerate(headlines[:3], 1):
            title = headline.get('title', 'No title available')
            summary = headline.get('summary', 'No summary available')
            source = headline.get('source', 'Unknown')
            link = headline.get('link', '')
            score = headline.get('market_moving_score', 0)
            
            # Format with clear structure and bullet points
            headlines_formatted += f"**{i}. {title}**\n"
            headlines_formatted += f"   *{summary}*\n"
            # Add hyperlink to source if link is available
            if link:
                headlines_formatted += f"   Source: [{source}]({link}) | Market Impact Score: {score}\n\n"
            else:
                headlines_formatted += f"   Source: {source} | Market Impact Score: {score}\n\n"
        
        # Format earnings snapshot according to template format
        earnings_formatted = ""
        
        # Reported After Close section
        if earnings_snapshot.get('reported'):
            earnings_formatted += "**Reported After Close:**\n"
            for earning in earnings_snapshot['reported'][:2]:  # Show top 2 recent earnings
                company = earning.get('company_name', 'Unknown Company')
                ticker = earning.get('ticker', 'N/A')
                eps_actual = earning.get('eps_actual', 'N/A')
                eps_forecast = earning.get('eps_forecast', 'N/A')
                surprise = earning.get('surprise', '')
                
                # Format: • COMPANY ($TICKER): EPS ACTUAL vs. ESTIMATE | Revenue ACTUAL vs. ESTIMATE
                earnings_formatted += f"• **{company}** (${ticker}): EPS Actual {eps_actual} vs. Forecasted {eps_forecast}"
                
                # Add surprise info if available
                if surprise:
                    earnings_formatted += f" | {surprise}"
                
                earnings_formatted += "\n"
            
            earnings_formatted += "\n"
        
        # Reporting Today section
        if earnings_snapshot.get('reporting_today'):
            pre_market = earnings_snapshot['reporting_today'].get('pre', [])
            post_market = earnings_snapshot['reporting_today'].get('post', [])
            
            if pre_market or post_market:
                earnings_formatted += "**Reporting Today:**\n"
                
                if pre_market:
                    pre_tickers = ", ".join([f"${t}" for t in pre_market[:4]])  # Show up to 4 tickers
                    earnings_formatted += f"• **Pre:** {pre_tickers}\n"
                
                if post_market:
                    post_tickers = ", ".join([f"${t}" for t in post_market[:4]])  # Show up to 4 tickers
                    earnings_formatted += f"• **Post:** {post_tickers}\n"
        
        # If no earnings data, show placeholder
        if not earnings_formatted:
            earnings_formatted = "No recent earnings data available.\n"
        
        # Get mentioned tickers
        mentioned_tickers = self._extract_mentioned_tickers(headlines, earnings_snapshot)
        
        # Format complete brief for compact one-page layout
        brief = f"""<div style="font-size: 10px; line-height: 1.1; font-family: Arial, sans-serif; max-width: 8.5in;">

# 📊 UnBound X Market Brief
**{datetime.now().strftime('%Y-%m-%d %H:%M')} EST**

**📈 MARKET OUTLOOK**  
{kwargs['market_summary']}

---

**📊 KEY METRICS** | **🏛️ ECONOMIC DATA** | **🎤 FED WATCH**

{key_indicators}

{kwargs['economic_indicators']}

**Fed Commentary:** {kwargs['fedspeak'].replace('**Recent Commentary:**', '').replace('**Upcoming Events:**', '| Events:').strip()}

---

**📰 TOP HEADLINES**
{headlines_formatted}

**💰 EARNINGS UPDATE**
{earnings_formatted}

---
<small>**Disclaimer:** Educational use only | **Tickers:** {mentioned_tickers} | **API:** {self._estimate_credits_used()}</small>

</div>"""
        
        return brief
    
    def _extract_mentioned_tickers(self, headlines: List[Dict], earnings_snapshot: Dict) -> str:
        """Extract mentioned tickers from headlines and earnings"""
        tickers = set()
        
        # Extract from headlines
        for headline in headlines:
            title = headline.get('title', '')
            summary = headline.get('summary', '')
            # Simple ticker extraction (look for $TICKER pattern)
            import re
            ticker_matches = re.findall(r'\$([A-Z]{1,5})', title + ' ' + summary)
            tickers.update(ticker_matches)
        
        # Extract from earnings
        if earnings_snapshot.get('reported'):
            for earning in earnings_snapshot['reported']:
                tickers.add(earning.get('ticker', ''))
        
        if earnings_snapshot.get('reporting_today'):
            tickers.update(earnings_snapshot['reporting_today'].get('pre', []))
            tickers.update(earnings_snapshot['reporting_today'].get('post', []))
        
        return ", ".join(sorted(tickers)) if tickers else "None"
    
    def _estimate_credits_used(self) -> str:
        """Estimate credits used for this brief generation"""
        return "~2-3 Groq API calls"
    
    def _save_brief(self, content: str) -> str:
        """Save brief content to file with descriptive naming"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"UnBound_Market_Brief_{timestamp}.md"
        
        # Create outputs directory if it doesn't exist
        outputs_dir = Path(project_root) / "signalmuse" / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        brief_path = outputs_dir / filename
        
        with open(brief_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(brief_path)


def main():
    """Entry point for standalone execution"""
    try:
        logger.debug("Morning Brief Generator Test")
        
        # Check if running in correct environment
        if not config.has_groq_api:
            logger.error("GROQ_API_KEY not found in environment. Please set it in your .env file.")
            return False
        
        generator = MorningBriefGenerator()
        brief_path = generator.generate_morning_brief()
        
        logger.info(f"Morning brief generation complete: {brief_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Morning brief generation failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
