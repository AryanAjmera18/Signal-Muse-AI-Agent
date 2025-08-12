"""
News Scraper Module

Standalone module for scraping financial news from multiple RSS sources.
Maintains the same logic as the original multi_source_scraper but in a modular structure.
"""

from .scraper.multi_source_scraper import MultiSourceScraper
from .main import run_news_scraper

__all__ = ['MultiSourceScraper', 'run_news_scraper']
