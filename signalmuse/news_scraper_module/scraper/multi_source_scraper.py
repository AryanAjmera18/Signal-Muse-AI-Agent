#!/usr/bin/env python3
"""
Multi-Source RSS Scraper

Enhanced RSS scraper that can handle multiple financial news sources
with proper error handling, rate limiting, and source categorization.
"""

import requests
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
import hashlib

from signalmuse.utils.utils import get_logger, save_dataframe_to_csv, generate_timestamp_filename
from .feed_config import RSSFeed, feed_manager

logger = get_logger(__name__)

class MultiSourceScraper:
    """Enhanced RSS scraper for multiple financial news sources"""
    
    def __init__(self):
        self.feeds = feed_manager.get_enabled_feeds()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_feed(self, feed: RSSFeed) -> List[Dict]:
        """Fetch and parse a single RSS feed"""
        try:
            logger.info(f"Fetching {feed.name} from {feed.url}")
            
            response = self.session.get(feed.url, timeout=10)
            response.raise_for_status()
            
            # Parse RSS feed
            parsed = feedparser.parse(response.content)
            
            articles = []
            for entry in parsed.entries:
                # Extract article data
                article = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', ''),
                    'published': entry.get('published', ''),
                    'source': feed.name,
                    'category': feed.category,
                    'priority': feed.priority,
                    'guid': entry.get('id', ''),
                    'author': entry.get('author', ''),
                    'tags': entry.get('tags', [])
                }
                
                # Generate unique ID
                article['id'] = self._generate_article_id(article)
                
                articles.append(article)
            
            logger.info(f"Successfully fetched {len(articles)} articles from {feed.name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching {feed.name}: {str(e)}")
            return []
    
    def _generate_article_id(self, article: Dict) -> str:
        """Generate unique ID for article"""
        content = f"{article['title']}{article['link']}{article['published']}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def fetch_all_feeds(self, max_articles_per_feed: int = 50) -> pd.DataFrame:
        """Fetch all enabled feeds and return combined DataFrame"""
        all_articles = []
        
        for feed_id, feed in self.feeds.items():
            if not feed.enabled:
                continue
                
            articles = self.fetch_feed(feed)
            
            # Limit articles per feed
            if len(articles) > max_articles_per_feed:
                articles = articles[:max_articles_per_feed]
            
            all_articles.extend(articles)
            
            # Rate limiting
            time.sleep(feed.rate_limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_articles)
        
        if not df.empty:
            # Clean and process data
            df['published'] = pd.to_datetime(df['published'], errors='coerce')
            df['summary'] = df['summary'].str.strip()
            df['title'] = df['title'].str.strip()
            
            # Remove duplicates based on ID
            df = df.drop_duplicates(subset=['id'])
            
            # Sort by priority and publication date
            df = df.sort_values(['priority', 'published'], ascending=[True, False])
        
        return df
    
    def fetch_by_category(self, category: str, max_articles: int = 100) -> pd.DataFrame:
        """Fetch articles from a specific category"""
        category_feeds = {
            feed_id: feed for feed_id, feed in self.feeds.items()
            if feed.category == category and feed.enabled
        }
        
        all_articles = []
        for feed_id, feed in category_feeds.items():
            articles = self.fetch_feed(feed)
            all_articles.extend(articles)
            time.sleep(feed.rate_limit)
        
        df = pd.DataFrame(all_articles)
        
        if not df.empty:
            df['published'] = pd.to_datetime(df['published'], errors='coerce')
            df = df.drop_duplicates(subset=['id'])
            df = df.sort_values('published', ascending=False)
            df = df.head(max_articles)
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = None) -> str:
        """Save articles to CSV file"""
        if filename is None:
            filename = "raw_news.csv"
        
        from signalmuse.utils.utils import config
        filepath = config.data_dir / filename
        return save_dataframe_to_csv(df, str(filepath), logger)
