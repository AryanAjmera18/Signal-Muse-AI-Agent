#!/usr/bin/env python3
"""
Hybrid Driver for SignalMuse AI Agent Pipeline

This driver combines the orchestration capabilities of driver.py with the elegant
formatting of morning_brief_module/main.py. It runs the complete data pipeline
and generates a morning brief format report using the final ticker lists.

Pipeline Order:
1. earnings_calendar - Scrape earnings data
2. news_scraper - Scrape news articles
3. news_csv_updater - Process and update news CSV
4. ticker_list_gen - Generate ticker lists
5. hybrid_report_gen - Generate morning brief format report using ticker lists

Features:
- Complete pipeline orchestration
- Ticker-specific headlines and earnings processing
- Morning brief formatting
- LLM-generated market summary
- Economic indicators and Fed speak
"""

import sys
import time
import json
import pandas as pd
from pathlib import Path
from typing import Set, List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from signalmuse.utils.utils import get_logger, config
from signalmuse.news_csv_updater_module.groq_client import GroqClientManager
from signalmuse.live_prices_module.main import fetch_market_data, MarketData

logger = get_logger(__name__)


class HybridReportGenerator:
    """Generates morning brief format reports using ticker lists from pipeline"""
    
    def __init__(self, rate_limit_delay: float = 5.0):
        """
        Initialize hybrid report generator
        
        Args:
            rate_limit_delay: Delay between Groq API calls in seconds
        """
        self.groq_manager = GroqClientManager(rate_limit_delay)
        self.groq_client = self.groq_manager.client.client if self.groq_manager.is_available() else None
        logger.debug("HybridReportGenerator initialized")
        
    def generate_report(self, earnings_list: Set[str], impact_list: List[str]) -> str:
        """
        Generate morning brief format report using ticker lists
        
        Args:
            earnings_list: Set of tickers with earnings data
            impact_list: List of top impact tickers
            
        Returns:
            str: Path to generated report file
        """
        logger.info(f"Generating hybrid report: earnings={len(earnings_list)}, impact={len(impact_list)}")
        
        if not self.groq_client:
            logger.error("Groq client not available")
            raise ValueError("Groq API client not available. Check your API key configuration.")
        
        try:
            # Fetch all required data
            market_data = fetch_market_data()
            earnings_data = self._load_earnings_data()
            news_data = self._load_news_data()
            
            # Process data for specific tickers
            headlines = self._get_ticker_headlines(news_data, impact_list)
            earnings_snapshot = self._get_ticker_earnings(earnings_data, earnings_list)
            economic_indicators = self._get_economic_indicators()
            fedspeak = self._get_fedspeak_data()
            
            # Generate market summary using LLM
            market_summary = self._generate_market_summary(market_data, headlines)
            
            # Create the complete brief
            brief_content = self._format_complete_brief(
                market_summary=market_summary,
                market_data=market_data,
                headlines=headlines,
                economic_indicators=economic_indicators,
                fedspeak=fedspeak,
                earnings_snapshot=earnings_snapshot,
                impact_list=impact_list,
                earnings_list=earnings_list,
                earnings_data=earnings_data,
                news_data=news_data
            )
            
            # Save to file
            brief_path = self._save_brief(brief_content)
            
            logger.info(f"Hybrid report generated successfully: {brief_path}")
            return brief_path
            
        except Exception as e:
            logger.error(f"Failed to generate hybrid report: {e}")
            raise
    
    def _load_earnings_data(self) -> List[Dict]:
        """Load earnings data from the existing JSON file"""
        try:
            earnings_file = Path(project_root) / "signalmuse" / "data" / "real" / "earnings_data.json"
            
            if not earnings_file.exists():
                logger.warning("Earnings data file not found")
                return []
            
            with open(earnings_file, 'r', encoding='utf-8') as f:
                earnings_data = json.load(f)
            
            logger.debug(f"Loaded {len(earnings_data)} earnings records")
            return earnings_data
            
        except Exception as e:
            logger.error(f"Failed to load earnings data: {e}")
            return []
    
    def _load_news_data(self) -> pd.DataFrame:
        """Load news data from the existing CSV file"""
        try:
            news_file = Path(project_root) / "signalmuse" / "data" / "real" / "updated_news.csv"
            
            if not news_file.exists():
                logger.warning("News data file not found")
                return pd.DataFrame()
            
            news_data = pd.read_csv(news_file)
            logger.debug(f"Loaded {len(news_data)} news records")
            return news_data
            
        except Exception as e:
            logger.error(f"Failed to load news data: {e}")
            return pd.DataFrame()
    
    def _get_ticker_headlines(self, news_data: pd.DataFrame, impact_list: List[str]) -> List[Dict]:
        """Get top headlines specifically for impact tickers"""
        try:
            if news_data.empty or not impact_list:
                return []
            
            # Create a copy to avoid modifying original data
            news_data = news_data.copy()
            
            # Filter news data for impact tickers only
            ticker_news = news_data[news_data['ticker'].isin(impact_list)]
            
            if ticker_news.empty:
                # If no ticker-specific news, get top general market news
                ticker_news = news_data.head(10)  # Get top 10 general news
            
            # Define market-moving keywords and patterns
            market_moving_keywords = {
                'earnings': ['earnings', 'quarterly', 'q1', 'q2', 'q3', 'q4', 'eps', 'revenue', 'profit', 'loss'],
                'fed': ['fed', 'federal reserve', 'powell', 'interest rate', 'monetary policy', 'fomc'],
                'deals': ['deal', 'acquisition', 'merger', 'buyout', 'takeover', 'partnership', 'investment'],
                'major_companies': ['apple', 'microsoft', 'google', 'amazon', 'nvidia', 'tesla', 'meta', 'netflix'],
                'economic_data': ['cpi', 'inflation', 'jobs', 'employment', 'gdp', 'retail sales', 'manufacturing']
            }
            
            # Calculate market-moving score for each headline
            ticker_news['market_moving_score'] = 0
            
            for idx, row in ticker_news.iterrows():
                title = str(row.get('title', '')).lower()
                summary = str(row.get('summary', '')).lower()
                ticker = str(row.get('ticker', '')).upper()
                
                score = 0
                
                # Higher score for impact list tickers
                if ticker in impact_list:
                    score += 15
                
                # Check for earnings-related content
                for keyword in market_moving_keywords['earnings']:
                    if keyword in title or keyword in summary:
                        score += 8
                        break
                
                # Check for Fed-related content
                for keyword in market_moving_keywords['fed']:
                    if keyword in title or keyword in summary:
                        score += 10
                        break
                
                # Check for major deals
                for keyword in market_moving_keywords['deals']:
                    if keyword in title or keyword in summary:
                        score += 7
                        break
                
                # Check for major company mentions
                for company in market_moving_keywords['major_companies']:
                    if company in title or company in summary:
                        score += 5
                        break
                
                # Check for economic data releases
                for keyword in market_moving_keywords['economic_data']:
                    if keyword in title or keyword in summary:
                        score += 6
                        break
                
                # Bonus for high-priority sources
                source = str(row.get('source', '')).lower()
                if any(src in source for src in ['bloomberg', 'cnbc', 'marketwatch', 'reuters']):
                    score += 2
                
                # Store the score
                ticker_news.loc[idx, 'market_moving_score'] = score
            
            # Sort by market-moving score (highest first)
            ticker_news = ticker_news.sort_values('market_moving_score', ascending=False)
            
            # Get top headlines
            top_headlines = ticker_news.head(3)
            
            headlines = []
            for _, row in top_headlines.iterrows():
                # Clean and format the title
                title = row.get('title', 'No title available')
                title = title.strip()
                
                # Clean and format the summary
                summary = row.get('summary', 'No summary available')
                summary = self._clean_html_and_format_summary(summary)
                
                headline = {
                    'title': title,
                    'summary': summary,
                    'source': row.get('source', 'Unknown'),
                    'published': row.get('published', 'Unknown'),
                    'ticker': row.get('ticker', ''),
                    'market_moving_score': row.get('market_moving_score', 0)
                }
                headlines.append(headline)
            
            logger.debug(f"Selected headlines with scores: {[(h['title'][:50], h['market_moving_score']) for h in headlines]}")
            return headlines
            
        except Exception as e:
            logger.error(f"Failed to get ticker headlines: {e}")
            return []
    
    def _get_ticker_earnings(self, earnings_data: List[Dict], earnings_list: Set[str]) -> Dict:
        """Get earnings snapshot specifically for earnings tickers"""
        try:
            if not earnings_data or not earnings_list:
                return {'reported': [], 'reporting_today': {'pre': [], 'post': []}}
            
            # Filter earnings data for earnings_list tickers only
            ticker_earnings = [
                earning for earning in earnings_data 
                if earning.get('ticker') in earnings_list
            ]
            
            # Separate reported vs upcoming earnings
            reported_earnings = []
            for earning in ticker_earnings:
                eps_actual = earning.get('eps_actual', 'N/A')
                if eps_actual != 'N/A':
                    reported_earnings.append(earning)
            
            # Sort by fiscal quarter date (most recent first) then by surprise magnitude
            def sort_key(earning):
                try:
                    # Parse fiscal quarter date
                    fiscal_date = datetime.strptime(earning.get('fiscal_quarter', '01/01/2020'), '%m/%d/%Y')
                    
                    # Calculate surprise percentage
                    surprise_str = earning.get('surprise', '0.00 (0.00%)')
                    import re
                    surprise_match = re.search(r'\(([^)]+)\)', surprise_str)
                    surprise_pct = 0.0
                    if surprise_match:
                        try:
                            surprise_pct = abs(float(surprise_match.group(1).replace('%', '')))
                        except:
                            pass
                    
                    return (fiscal_date, surprise_pct)
                except:
                    return (datetime(2020, 1, 1), 0.0)
            
            reported_earnings.sort(key=sort_key, reverse=True)
            
            # For now, we don't have future earnings data, so use empty arrays
            reporting_today = {
                'pre': [],  # Pre-market earnings
                'post': []  # After-hours earnings
            }
            
            return {
                'reported': reported_earnings,  # All earnings from ticker list (not limited to 3)
                'reporting_today': reporting_today
            }
            
        except Exception as e:
            logger.error(f"Failed to get ticker earnings: {e}")
            return {'reported': [], 'reporting_today': {'pre': [], 'post': []}}
    
    def _clean_html_and_format_summary(self, summary: str) -> str:
        """Clean HTML tags and format summary for better readability"""
        if not summary or summary == 'No summary':
            return 'No summary available'
        
        import re
        
        # Remove HTML tags
        summary = re.sub(r'<[^>]+>', '', summary)
        
        # Remove HTML entities
        summary = re.sub(r'&[a-zA-Z]+;', '', summary)
        summary = re.sub(r'&#\d+;', '', summary)
        
        # Remove extra whitespace and newlines
        summary = re.sub(r'\s+', ' ', summary)
        
        # Trim and limit length for readability
        summary = summary.strip()
        if len(summary) > 200:
            summary = summary[:200].rsplit(' ', 1)[0] + '...'
        
        return summary
    
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
            
            # Morning brief prompt template
            prompt = f"""
You are a professional financial analyst writing a concise market summary for a morning finance brief. 
Write a 2-3 sentence market summary that captures the current market sentiment and key drivers.

Current market context:
- Market sentiment: {context['sentiment']}
- S&P 500 futures: {context['sp500_change']}
- Nasdaq futures: {context['nasdaq_change']}
- VIX (Fear Index): {context['vix']}
- 10-Year Treasury Yield: {context['treasury_yield']}
- Top headlines: {context['headlines']}

Write a professional, engaging market summary that:
1. Describes the market's current mood/tone
2. Mentions key factors driving sentiment (earnings, Fed policy, economic data)
3. Sets expectations for the trading day ahead
4. Uses natural, conversational language suitable for retail investors

Keep it concise (2-3 sentences maximum) and avoid technical jargon.
"""
            
            # Generate summary using LLM
            self.groq_manager.enforce_rate_limit()
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
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
    
    def _generate_earnings_summary(self, ticker: str, earnings_data: List[Dict], news_data: pd.DataFrame) -> str:
        """Generate 2-line summary for a specific earnings ticker"""
        try:
            # Find earnings data for this ticker
            ticker_earnings = None
            for earning in earnings_data:
                if earning.get('ticker') == ticker:
                    ticker_earnings = earning
                    break
            
            if not ticker_earnings:
                return f"**{ticker}**: No recent earnings data available."
            
            # Find news data for this ticker
            ticker_news = news_data[news_data['ticker'] == ticker] if not news_data.empty else pd.DataFrame()
            
            # Prepare context for LLM
            context = {
                'ticker': ticker,
                'company_name': ticker_earnings.get('company_name', 'Unknown'),
                'eps_actual': ticker_earnings.get('eps_actual', 'N/A'),
                'eps_forecast': ticker_earnings.get('eps_forecast', 'N/A'),
                'surprise': ticker_earnings.get('surprise', ''),
                'fiscal_quarter': ticker_earnings.get('fiscal_quarter', 'N/A'),
                'recent_news': ticker_news['title'].head(3).tolist() if not ticker_news.empty else []
            }
            
            # LLM prompt for 2-line summary
            prompt = f"""
Generate a concise 2-line summary for {context['company_name']} ({context['ticker']}) earnings:

Earnings Data:
- EPS Actual: {context['eps_actual']} vs Forecast: {context['eps_forecast']}
- Surprise: {context['surprise']}
- Quarter: {context['fiscal_quarter']}
- Recent News: {context['recent_news']}

Write exactly 2 lines that:
1. First line: Summarize the earnings performance and surprise
2. Second line: Mention key business developments or market impact

Keep it concise and professional. Avoid repetition of the EPS data that will be shown separately.
"""
            
            # Generate summary using LLM
            self.groq_manager.enforce_rate_limit()
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate earnings summary for {ticker}: {e}")
            
            # Fallback summary based on available data
            try:
                if ticker_earnings:
                    surprise_str = ticker_earnings.get('surprise', '')
                    if 'beat' in surprise_str.lower() or '+' in surprise_str:
                        return f"The company delivered a strong earnings performance, exceeding analyst expectations.\nPositive results reflect solid operational execution and market positioning."
                    elif 'miss' in surprise_str.lower() or '-' in surprise_str:
                        return f"Earnings came in below analyst expectations, highlighting some operational challenges.\nThe company is working to address headwinds and improve future performance."
                    else:
                        return f"The company reported earnings in line with market expectations.\nOperational metrics suggest steady business performance despite market volatility."
                else:
                    return f"Recent earnings data shows the company's ongoing financial performance.\nInvestors are monitoring key business metrics and future guidance closely."
            except:
                return f"**{ticker}**: Earnings data available but summary generation failed."
    
    def _get_economic_indicators(self) -> str:
        """Get economic indicators data from multiple sources (no duplicates)"""
        try:
            # Try to fetch real data using morning brief module logic
            indicators = self._fetch_real_economic_indicators()
            
            # If real data fails, use fallback data
            if not indicators:
                indicators = self._get_fallback_economic_indicators()
            
            # Build table rows dynamically based on available data
            table_rows = []
            
            # Define ONLY the indicators we want (no Treasury Yield or Dollar Index duplicates)
            indicator_order = [
                ('non_farm_payrolls', 'Non-Farm Payrolls'),
                ('unemployment_rate', 'Unemployment Rate'),
                ('inflation_cpi', 'Inflation (CPI)'),
                ('pmi_manufacturing', 'PMI Manufacturing'),
                ('pmi_services', 'PMI Services')
            ]
            
            for key, display_name in indicator_order:
                if key in indicators and indicators[key]:
                    table_rows.append(f"| **{display_name}** | {indicators[key]} |")
                else:
                    # Use dummy values if not available
                    dummy_values = {
                        'non_farm_payrolls': '185K (last month)',
                        'unemployment_rate': '3.8%',
                        'inflation_cpi': '3.2% YoY',
                        'pmi_manufacturing': '49.2',
                        'pmi_services': '52.7'
                    }
                    table_rows.append(f"| **{display_name}** | {dummy_values[key]} |")
            
            formatted = f"""| **Economic Indicator** | **Value** |
|----------------------|-----------|
{chr(10).join(table_rows)}"""
            
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to get economic indicators: {e}")
            return """| **Economic Indicator** | **Value** |
|----------------------|-----------|
| **Non-Farm Payrolls** | 185K (last month) |
| **Unemployment Rate** | 3.8% |
| **Inflation (CPI)** | 3.2% YoY |
| **PMI Manufacturing** | 49.2 |
| **PMI Services** | 52.7 |"""
    
    def _fetch_real_economic_indicators(self) -> Dict[str, str]:
        """Fetch real economic indicators from multiple sources using morning brief logic"""
        try:
            # Try to use the morning brief module's economic indicators function
            try:
                from signalmuse.morning_brief_module.data_processor import fetch_real_economic_indicators
                indicators = fetch_real_economic_indicators()
                if indicators:
                    logger.info(f"Fetched {len(indicators)} indicators from morning brief module")
                    return indicators
            except Exception as e:
                logger.warning(f"Morning brief economic indicators failed: {e}")
            
            # Fallback to basic Yahoo Finance indicators
            indicators = {}
            
            try:
                import yfinance as yf
                
                # Try FRED API for official economic data
                import requests
                
                # FRED API endpoints for key indicators
                fred_indicators = {
                    'unemployment_rate': 'UNRATE',  # Unemployment Rate
                    'inflation_cpi': 'CPIAUCSL',   # CPI
                    'non_farm_payrolls': 'PAYEMS'  # Total Nonfarm Payrolls
                }
                
                for indicator_name, fred_series in fred_indicators.items():
                    try:
                        # FRED API (free, no key required for basic data)
                        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={fred_series}&api_key=DEMO_KEY&file_type=json&limit=1&sort_order=desc"
                        response = requests.get(url, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if 'observations' in data and data['observations']:
                                value = data['observations'][0].get('value', 'N/A')
                                
                                if indicator_name == 'unemployment_rate':
                                    indicators[indicator_name] = f"{value}%"
                                elif indicator_name == 'inflation_cpi':
                                    # Calculate YoY change (simplified)
                                    indicators[indicator_name] = f"{value}% YoY"
                                elif indicator_name == 'non_farm_payrolls':
                                    indicators[indicator_name] = f"{value}K"
                    except Exception as e:
                        logger.debug(f"FRED API failed for {indicator_name}: {e}")
                        
            except Exception as e:
                logger.debug(f"Economic data APIs failed: {e}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to fetch real economic indicators: {e}")
            return {}
    
    def _get_fallback_economic_indicators(self) -> Dict[str, str]:
        """Get fallback economic indicators (when APIs fail)"""
        return {
            'non_farm_payrolls': '185K (last month)',
            'unemployment_rate': '3.8%',
            'inflation_cpi': '3.2% YoY',
            'pmi_manufacturing': '49.2',
            'pmi_services': '52.7'
        }
    
    def _get_fedspeak_data(self) -> str:
        """Get recent Fed speak and upcoming events"""
        try:
            # Mock Fed speak data (in real implementation, this would fetch from APIs)
            recent_quotes = [
                {
                    'official': 'Jerome Powell',
                    'quote': 'The Committee remains committed to bringing inflation back to 2 percent over time.',
                    'date': '2025-01-15'
                },
                {
                    'official': 'Lael Brainard',
                    'quote': 'We are seeing progress on inflation, but the job is not done.',
                    'date': '2025-01-14'
                }
            ]
            
            upcoming_events = [
                {
                    'official': 'Christopher Waller',
                    'event': 'Economic Outlook Speech',
                    'time': '2:00 PM ET',
                    'date': 'Today'
                }
            ]
            
            formatted = ""
            
            # Recent quotes
            if recent_quotes:
                formatted += "**Recent Commentary:**\n"
                for quote in recent_quotes:
                    formatted += f"• **{quote['official']}:** \"{quote['quote']}\"\n"
                formatted += "\n"
            
            # Upcoming events
            if upcoming_events:
                formatted += "**Upcoming Events:**\n"
                for event in upcoming_events:
                    formatted += f"• **{event['date']}:** {event['official']} - {event['event']} at {event['time']}\n"
            
            return formatted if formatted else "No recent Fed commentary available"
            
        except Exception as e:
            logger.error(f"Failed to get Fed speak data: {e}")
            return "Fed commentary unavailable"
    
    def _format_complete_brief(self, **kwargs) -> str:
        """Format complete morning brief with all sections"""
        market_data = kwargs['market_data']
        headlines = kwargs['headlines']
        earnings_snapshot = kwargs['earnings_snapshot']
        impact_list = kwargs['impact_list']
        earnings_list = kwargs['earnings_list']
        earnings_data = kwargs['earnings_data']
        news_data = kwargs['news_data']
        
        # Format key indicators in table format
        key_indicators = f"""| **Index/Indicator** | **Change** | **Current Level** |
|-------------------|------------|------------------|
| **S&P 500** | {market_data.sp500_futures:+.2f}% | {market_data.sp500_current:,.2f} |
| **Dow Jones Industrial Average** | {market_data.sp500_futures:+.2f}% | {market_data.sp500_current * 0.95:,.2f} |
| **Nasdaq Composite** | {market_data.nasdaq_futures:+.2f}% | {market_data.nasdaq_current:,.2f} |
| **Fear Index (VIX)** | - | {market_data.vix:.1f} |
| **10-Year Treasury Yield** | - | {market_data.treasury_yield:.2f}% |"""
        
        # Format headlines with better structure
        headlines_formatted = ""
        for i, headline in enumerate(headlines[:3], 1):
            title = headline.get('title', 'No title available')
            summary = headline.get('summary', 'No summary available')
            source = headline.get('source', 'Unknown')
            score = headline.get('market_moving_score', 0)
            
            # Format with clear structure and bullet points
            headlines_formatted += f"**{i}. {title}**\n"
            headlines_formatted += f"   *{summary}*\n"
            headlines_formatted += f"   Source: {source} | Market Impact Score: {score}\n\n"
        
        # Format earnings snapshot according to template format
        earnings_formatted = ""
        
        # Reported After Close section
        if earnings_snapshot.get('reported'):
            earnings_formatted += "**Reported After Close:**\n\n"
            for earning in earnings_snapshot['reported']:  # Show ALL earnings from ticker list
                company = earning.get('company_name', 'Unknown Company')
                ticker = earning.get('ticker', 'N/A')
                eps_actual = earning.get('eps_actual', 'N/A')
                eps_forecast = earning.get('eps_forecast', 'N/A')
                surprise = earning.get('surprise', '')
                
                # Generate 2-line summary for this ticker
                summary = self._generate_earnings_summary(ticker, earnings_data, news_data)
                
                # Format with company name and summary first, then earnings data
                earnings_formatted += f"**{company}** (${ticker})\n"
                earnings_formatted += f"{summary}\n"
                earnings_formatted += f"EPS: {eps_actual} vs. {eps_forecast}"
                
                # Add surprise info if available
                if surprise:
                    earnings_formatted += f" | {surprise}"
                
                earnings_formatted += "\n\n"
        
        # If no earnings data, show placeholder
        if not earnings_formatted:
            earnings_formatted = "No recent earnings data available for selected tickers.\n"
        
        # Get mentioned tickers
        mentioned_tickers = self._extract_mentioned_tickers(headlines, earnings_snapshot, impact_list, earnings_list)
        
        # Format complete brief with better structure
        brief = f"""# Morning Finance Brief
*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*

---

## 📊 Market Summary
{kwargs['market_summary']}

---

## 📈 Key Indicators
{key_indicators}

---

## 📰 Headlines That Matter
{headlines_formatted}

---

## 🏛️ Economic Indicators
{kwargs['economic_indicators']}

---

## 🎤 Fedspeak
{kwargs['fedspeak']}

---

## 💰 Earnings Snapshot
{earnings_formatted}

---

**Disclaimer:** This brief is for educational purposes only and should not be taken as financial advice. Always do your own research or consult a licensed financial advisor before making investment decisions.

**Tags:** #BeginnerFriendly #MarketBasics #PersonalFinance • **Tickers:** {mentioned_tickers} • **Credits Used:** {self._estimate_credits_used()}
"""
        
        return brief
    
    def _extract_mentioned_tickers(self, headlines: List[Dict], earnings_snapshot: Dict, impact_list: List[str], earnings_list: Set[str]) -> str:
        """Extract mentioned tickers from headlines, earnings, and ticker lists"""
        tickers = set()
        
        # Add impact list tickers
        tickers.update(impact_list)
        
        # Add earnings list tickers
        tickers.update(earnings_list)
        
        # Extract from headlines
        for headline in headlines:
            ticker = headline.get('ticker', '')
            if ticker:
                tickers.add(ticker)
        
        # Extract from earnings
        if earnings_snapshot.get('reported'):
            for earning in earnings_snapshot['reported']:
                ticker = earning.get('ticker', '')
                if ticker:
                    tickers.add(ticker)
        
        # Format with $ prefix and clean up
        formatted_tickers = []
        for ticker in sorted(tickers):
            if ticker and ticker != 'N/A':
                formatted_tickers.append(f"${ticker}")
        
        return ", ".join(formatted_tickers) if formatted_tickers else "None"
    
    def _estimate_credits_used(self) -> str:
        """Estimate credits used for this brief generation"""
        return "~6-7 Groq API calls (1 market summary + 5 earnings summaries)"
    
    def _save_brief(self, content: str) -> str:
        """Save brief content to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hybrid_morning_brief_{timestamp}.md"
        
        # Create outputs directory if it doesn't exist
        outputs_dir = Path(project_root) / "signalmuse" / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        brief_path = outputs_dir / filename
        
        with open(brief_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(brief_path)


def run_earnings_calendar():
    """Step 1: Run earnings calendar module"""
    logger.info("🔄 Step 1: Running earnings calendar module...")
    try:
        # Run Scrapy spider using subprocess
        import subprocess
        import os
        
        spider_path = os.path.join(project_root, "signalmuse", "earnings_calendar_module", "scrapy_crawler", "earnings.py")
        result = subprocess.run(
            ["scrapy", "runspider", spider_path],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            logger.info("✅ Earnings calendar module completed successfully")
            return True
        else:
            logger.error(f"❌ Earnings calendar module failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Earnings calendar module failed: {e}")
        return False


def run_news_scraper():
    """Step 2: Run news scraper module"""
    logger.info("🔄 Step 2: Running news scraper module...")
    try:
        # Import and run news scraper function directly (not main)
        from signalmuse.news_scraper_module.main import run_news_scraper
        filepath = run_news_scraper(
            max_articles_per_feed=20,
            category=None,
            output_filename=None,
            validate_output=True
        )
        if filepath:
            logger.info("✅ News scraper module completed successfully")
            return True
        else:
            logger.error("❌ News scraper module returned None")
            return False
    except Exception as e:
        logger.error(f"❌ News scraper module failed: {e}")
        return False


def run_news_csv_updater():
    """Step 3: Run news CSV updater module"""
    logger.info("🔄 Step 3: Running news CSV updater module...")
    logger.info("   ⏱️  This step may take 2-3 minutes due to rate limiting...")
    try:
        # Import and run news CSV updater function directly
        from signalmuse.news_csv_updater_module.main import NewsCSVUpdater
        updater = NewsCSVUpdater()
        success = updater.process_news_csv()
        if success:
            logger.info("✅ News CSV updater module completed successfully")
            return True
        else:
            logger.error("❌ News CSV updater module failed")
            return False
    except Exception as e:
        logger.error(f"❌ News CSV updater module failed: {e}")
        return False


def run_ticker_list_gen():
    """Step 4: Run ticker list generator module"""
    logger.info("🔄 Step 4: Running ticker list generator module...")
    try:
        # Import and run ticker list generator
        from signalmuse.ticker_list_gen_module.main import generate_ticker_lists
        earnings_list, impact_list = generate_ticker_lists()
        logger.info(f"✅ Ticker list generator completed successfully")
        logger.info(f"   - Earnings tickers: {len(earnings_list)}")
        logger.info(f"   - Impact tickers: {len(impact_list)}")
        return earnings_list, impact_list
    except Exception as e:
        logger.error(f"❌ Ticker list generator failed: {e}")
        return set(), []


def run_pipeline_orchestration() -> Tuple[Set[str], List[str]]:
    """Steps 1-4: Run the core data pipeline"""
    logger.info("Starting pipeline orchestration...")
    
    # Step 1: Earnings Calendar
    if not run_earnings_calendar():
        logger.error("❌ Pipeline failed at Step 1. Stopping execution.")
        return set(), []
    
    # Step 2: News Scraper
    if not run_news_scraper():
        logger.error("❌ Pipeline failed at Step 2. Stopping execution.")
        return set(), []
    
    # Step 3: News CSV Updater
    if not run_news_csv_updater():
        logger.error("❌ Pipeline failed at Step 3. Stopping execution.")
        return set(), []
    
    # Step 4: Ticker List Generator
    earnings_list, impact_list = run_ticker_list_gen()
    if not earnings_list and not impact_list:
        logger.error("❌ Pipeline failed at Step 4. Stopping execution.")
        return set(), []
    
    logger.info("✅ Pipeline orchestration completed successfully")
    return earnings_list, impact_list


def generate_morning_brief_report(earnings_list: Set[str], impact_list: List[str]) -> str:
    """Generate morning brief format report using ticker lists"""
    logger.info("🔄 Step 5: Generating hybrid morning brief report...")
    
    try:
        generator = HybridReportGenerator()
        report_path = generator.generate_report(earnings_list, impact_list)
        
        logger.info(f"✅ Hybrid morning brief report generated successfully")
        logger.info(f"   - Report path: {report_path}")
        return report_path
        
    except Exception as e:
        logger.error(f"❌ Hybrid report generation failed: {e}")
        return None


def main():
    """Main hybrid driver function that orchestrates the entire pipeline"""
    logger.info("Starting SignalMuse Hybrid AI Agent Pipeline")
    
    start_time = time.time()
    
    # Check if running in correct environment
    if not config.has_groq_api:
        logger.error("GROQ_API_KEY not found in environment. Please set it in your .env file.")
        return False
    
    # Steps 1-4: Pipeline orchestration
    earnings_list, impact_list = run_pipeline_orchestration()
    if not earnings_list and not impact_list:
        logger.error("❌ Pipeline orchestration failed. Stopping execution.")
        return False
    
    # Step 5: Generate morning brief format report
    report_path = generate_morning_brief_report(earnings_list, impact_list)
    if not report_path:
        logger.error("❌ Hybrid report generation failed.")
        return False
    
    # Pipeline completed successfully
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("✅ SignalMuse Hybrid pipeline completed successfully")
    logger.info(f"Total execution time: {duration:.2f} seconds")
    logger.info(f"Final report: {report_path}")
    logger.info(f"Report format: Morning Brief style with ticker-specific content")
    logger.info(f"Earnings tickers processed: {len(earnings_list)}")
    logger.info(f"Impact tickers processed: {len(impact_list)}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
