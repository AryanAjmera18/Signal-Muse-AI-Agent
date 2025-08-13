#!/usr/bin/env python3
"""
Configuration settings for the ticker list generator module.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "signalmuse" / "data" / "real"

# Data file paths
UPDATED_NEWS_CSV_PATH = DATA_DIR / "updated_news.csv"
EARNINGS_DATA_JSON_PATH = DATA_DIR / "earnings_data.json"

# Processing settings
TOP_EARNINGS_TICKERS_LIMIT = 5
TOP_IMPACT_TICKERS_LIMIT = 5
VALID_TICKER_VALUES = {'N/A', '', None}

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
