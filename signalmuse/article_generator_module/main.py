#!/usr/bin/env python3
"""
Ultra-lean Article Generator - Main Orchestrator

Standalone module for generating comprehensive newspaper-style reports
by processing earnings data and news articles using Groq LLM.

Features:
- Reuses existing data loader functions
- Appending pattern for progress saving  
- Batch processing: 2 earnings + 1 impact per LLM call
- Ultra-lean implementation: ~40 LOC
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Set, List, Dict, Optional

# Add project root to path for absolute imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from signalmuse.utils.utils import get_logger, config
from signalmuse.news_csv_updater_module.groq_client import GroqClientManager
import pandas as pd
import yfinance as yf

# Handle imports for both script execution and module import
try:
    # Try relative imports first (for module import)
    from .data_loader import load_ticker_data
    from .report_builder import create_report, append_to_report, append_footer, extract_and_format_news_sources
    from .prompt_templates import EARNINGS_PROMPT, IMPACT_PROMPT
except ImportError:
    # Fallback to absolute imports (for script execution)
    from signalmuse.article_generator_module.data_loader import load_ticker_data
    from signalmuse.article_generator_module.report_builder import create_report, append_to_report, append_footer, extract_and_format_news_sources
    from signalmuse.article_generator_module.prompt_templates import EARNINGS_PROMPT, IMPACT_PROMPT

logger = get_logger(__name__)


@dataclass
class TickerQuote:
    price: float
    change_pct: Optional[float] = None


class ArticleGenerator:
    """Ultra-lean article generator with maximum code reuse"""
    
    def __init__(self, rate_limit_delay: float = 5.0):
        """
        Initialize article generator
        
        Args:
            rate_limit_delay: Delay between Groq API calls in seconds
        """
        self.groq_manager = GroqClientManager(rate_limit_delay)
        # Get the raw Groq client for simple text generation
        self.groq_client = self.groq_manager.client.client if self.groq_manager.is_available() else None
        logger.debug("ArticleGenerator initialized")
        self._ticker_quotes: Dict[str, TickerQuote] = {}
        
    def generate_articles(self, earnings_list: Set[str], impact_list: List[str]) -> str:
        """
        Generate complete report with appending pattern
        
        Args:
            earnings_list: Set of tickers with earnings data (process 2 at a time)
            impact_list: List of top impact tickers (process 1 at a time)
            
        Returns:
            str: Path to generated report file
        """
        logger.info(f"Generating report: earnings={len(earnings_list)}, impact={len(impact_list)}")
        
        if not self.groq_client:
            logger.error("Groq client not available")
            raise ValueError("Groq API client not available. Check your API key configuration.")
        
        # Load data using reused functions
        earnings_data, news_data = load_ticker_data(earnings_list, impact_list)
        
        # Prefetch live quotes for all tickers to minimize API calls
        try:
            all_tickers: List[str] = list(earnings_list) + list(impact_list)
            self._prefetch_live_quotes(all_tickers)
        except Exception as e:
            logger.warning(f"Prefetching live quotes failed: {e}")

        # Create report and append sections progressively
        report_path = create_report()
        logger.debug(f"Created report file: {report_path}")
        
        # Process earnings tickers (1 at a time for consistency)
        for ticker in earnings_list:
            content = self._generate_earnings_content(ticker, earnings_data, news_data)
            append_to_report(report_path, content, 'earnings')
            logger.debug(f"Processed earnings ticker: {ticker}")
        
        # Process impact tickers (1 at a time as specified)
        for ticker in impact_list:
            content = self._generate_impact_content(ticker, news_data)
            append_to_report(report_path, content, 'impact')
            logger.debug(f"Processed impact ticker: {ticker}")
        
        # Add compliance footer
        append_footer(report_path)
        logger.debug("Added compliance footer to report")
        
        logger.info(f"Report generation complete: {report_path}")
        return report_path
    
    def _generate_earnings_content(self, ticker: str, earnings_data: dict, news_data: dict) -> str:
        """Generate content for 1 earnings ticker with news sources appended"""
        ticker_data = {
            'ticker': ticker,
            'earnings': earnings_data.get(ticker, {}),
            'news': news_data.get(ticker, [])
        }
        
        # Generate LLM content (EXISTING CODE UNCHANGED)
        llm_content = self._call_groq(EARNINGS_PROMPT.format(**ticker_data))
        
        # Inject live price line after heading if available
        llm_content = self._inject_live_price(llm_content, ticker)
        
        # NEW: Extract and format news sources for this ticker
        sources_content = extract_and_format_news_sources(ticker)
        
        return llm_content + sources_content
    
    def _generate_impact_content(self, ticker: str, news_data: dict) -> str:
        """Generate content for 1 impact ticker with news sources appended"""
        ticker_data = {
            'ticker': ticker, 
            'news': news_data.get(ticker, [])
        }
        
        # Generate LLM content (EXISTING CODE UNCHANGED)
        llm_content = self._call_groq(IMPACT_PROMPT.format(**ticker_data))
        
        # Inject live price line after heading if available
        llm_content = self._inject_live_price(llm_content, ticker)
        
        # NEW: Extract and format news sources for this ticker
        sources_content = extract_and_format_news_sources(ticker)
        
        return llm_content + sources_content
    
    def _call_groq(self, prompt: str) -> str:
        """Single Groq call function with error handling"""
        try:
            # Enforce rate limiting
            self.groq_manager.enforce_rate_limit()
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",  # Use current model
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq call failed: {e}")
            return f"Error generating content: {e}"

    # -------------------
    # Live price utilities
    # -------------------

    def _prefetch_live_quotes(self, tickers: List[str]):
        """Batch-fetch live-ish quotes for given tickers using yfinance.
        Stores results in self._ticker_quotes.
        """
        if not tickers:
            return
        unique_tickers = sorted(set(tickers))

        # Map input tickers to yfinance symbols (e.g., BTC -> BTC-USD)
        symbol_map = self._build_symbol_map(unique_tickers)
        yf_symbols = sorted(set(symbol_map.values()))

        # Initialize with defaults
        for t in unique_tickers:
            self._ticker_quotes[t] = TickerQuote(price=0.0, change_pct=None)

        # Try intraday 1m prices for current price
        try:
            intraday_df = yf.download(
                tickers=yf_symbols,
                period='1d',
                interval='1m',
                group_by='ticker',
                auto_adjust=True,
                progress=False,
                threads=True
            )
            for t in unique_tickers:
                try:
                    symbol = symbol_map[t]
                    if isinstance(intraday_df.columns, pd.MultiIndex):
                        series = intraday_df[(symbol, 'Close')]
                    else:
                        # Single ticker case
                        series = intraday_df['Close']
                    last_val = series.dropna().iloc[-1]
                    if pd.notna(last_val):
                        self._ticker_quotes[t].price = float(last_val)
                except Exception:
                    # Keep default price if unavailable
                    pass
        except Exception as e:
            logger.debug(f"Intraday price fetch failed: {e}")

        # Fetch previous and last daily close for change %
        try:
            daily_df = yf.download(
                tickers=yf_symbols,
                period='2d',
                interval='1d',
                group_by='ticker',
                auto_adjust=True,
                progress=False,
                threads=True
            )
            for t in unique_tickers:
                try:
                    symbol = symbol_map[t]
                    if isinstance(daily_df.columns, pd.MultiIndex):
                        close_series = daily_df[(symbol, 'Close')]
                    else:
                        close_series = daily_df['Close']
                    close_series = close_series.dropna()
                    if len(close_series) >= 2:
                        prev_close = float(close_series.iloc[-2])
                        last_close = float(close_series.iloc[-1])
                        if prev_close != 0:
                            change_pct = ((last_close - prev_close) / prev_close) * 100.0
                            self._ticker_quotes[t].change_pct = change_pct
                        # Use last_close as price if intraday missing
                        if self._ticker_quotes[t].price == 0.0 and pd.notna(last_close):
                            self._ticker_quotes[t].price = float(last_close)
                    elif len(close_series) == 1:
                        # Only one day available
                        last_close = float(close_series.iloc[-1])
                        if self._ticker_quotes[t].price == 0.0 and pd.notna(last_close):
                            self._ticker_quotes[t].price = float(last_close)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Daily change fetch failed: {e}")

    def _format_live_price_md(self, ticker: str) -> Optional[str]:
        quote = self._ticker_quotes.get(ticker)
        if not quote or quote.price is None or quote.price == 0.0:
            return None
        if quote.change_pct is None:
            return f"**Live Price ({ticker})**: ${quote.price:.2f}"
        return f"**Live Price ({ticker})**: ${quote.price:.2f} ({quote.change_pct:+.2f}%)"

    def _inject_live_price(self, content: str, ticker: str) -> str:
        """Insert a one-line live price right after the section heading (### ...)."""
        price_line = self._format_live_price_md(ticker)
        if not price_line:
            return content
        lines = content.splitlines()
        inserted = False
        for idx, line in enumerate(lines):
            if line.strip().startswith("###"):
                # Insert after heading line
                insertion_index = idx + 1
                # Add a blank line before and after for readability
                lines.insert(insertion_index, "")
                lines.insert(insertion_index + 1, price_line)
                lines.insert(insertion_index + 2, "")
                inserted = True
                break
        if not inserted:
            # Prepend if heading not found (should not happen if prompt followed)
            return price_line + "\n\n" + content
        return "\n".join(lines)

    def _build_symbol_map(self, tickers: List[str]) -> Dict[str, str]:
        """Return a mapping from input tickers to yfinance symbols.
        Handles a small set of known crypto and special cases.
        """
        mapping: Dict[str, str] = {}
        for t in tickers:
            t_upper = t.upper().strip()
            if t_upper in {"BTC", "BTCUSD", "XBT"}:
                mapping[t] = "BTC-USD"
            elif t_upper in {"ETH", "ETHUSD"}:
                mapping[t] = "ETH-USD"
            elif t_upper in {"SOL", "SOLUSD"}:
                mapping[t] = "SOL-USD"
            else:
                # Default: use as-is (assumed listed equity/etf)
                mapping[t] = t
        return mapping


def main():
    """Entry point for standalone execution"""
    try:
        logger.debug("Article Generator Module Test")
        
        # Check if running in correct environment
        if not config.has_groq_api:
            logger.error("GROQ_API_KEY not found in environment. Please set it in your .env file.")
            return False
        
        # Example usage - in real implementation, these would come from ticker_list_gen_module
        earnings_list = {'AAPL', 'MSFT', 'GOOGL', 'NVDA'}
        impact_list = ['TSLA', 'META', 'AMZN']
        
        generator = ArticleGenerator()
        report_path = generator.generate_articles(earnings_list, impact_list)
        
        logger.info(f"Article generation complete: {report_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Article generation failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
