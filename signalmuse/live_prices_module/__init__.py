#!/usr/bin/env python3
"""
Live Prices Module

Lean single-file module for fetching real-time market data and generating
deterministic markdown formatting for the live prices section.
"""

from .main import run_live_prices_module, fetch_market_data, format_live_prices_section

__all__ = [
    'run_live_prices_module',
    'fetch_market_data', 
    'format_live_prices_section'
]

__version__ = "1.0.0"
__author__ = "SignalMuse AI Agent"
