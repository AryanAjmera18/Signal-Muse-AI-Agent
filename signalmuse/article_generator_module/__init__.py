#!/usr/bin/env python3
"""
Article Generator Module

Ultra-lean standalone module for generating newspaper-style reports
by processing earnings data and news articles using Groq LLM.

Features:
- Reuses existing data loader functions for maximum efficiency
- Appending pattern for progress saving and memory efficiency
- Batch processing: 2 earnings tickers + 1 impact ticker per LLM call
- ~75 total LOC with maximum code reuse
"""

from .main import ArticleGenerator, main
from .data_loader import load_ticker_data
from .report_builder import create_report, append_to_report, append_footer
from .prompt_templates import EARNINGS_PROMPT, IMPACT_PROMPT

__all__ = [
    'ArticleGenerator',
    'main',
    'load_ticker_data',
    'create_report',
    'append_to_report',
    'append_footer',
    'EARNINGS_PROMPT',
    'IMPACT_PROMPT'
]

__version__ = "1.0.0"
__author__ = "SignalMuse AI Agent"
