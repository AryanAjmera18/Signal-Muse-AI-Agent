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
from dataclasses import dataclass
from pathlib import Path
import hashlib

from signalmuse.utils.utils import get_logger, save_dataframe_to_csv, generate_timestamp_filename

logger = get_logger(__name__)

@dataclass
class RSSFeed:
    """RSS feed configuration"""
    name: str
    url: str
    category: str
    priority: int = 1  # 1=high, 2=medium, 3=low
    enabled: bool = True
    rate_limit: float = 1.0  # seconds between requests

class MultiSourceScraper:
    """Enhanced RSS scraper for multiple financial news sources"""
    
    def __init__(self):
        self.feeds = self._initialize_feeds()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _initialize_feeds(self) -> Dict[str, RSSFeed]:
        """Initialize RSS feed configurations - optimized based on testing"""
        return {
            # General Financial News - HIGH PRIORITY
            'marketwatch_top': RSSFeed(
                name='MarketWatch Top Stories',
                url='https://feeds.marketwatch.com/marketwatch/topstories/',
                category='general_financial',
                priority=1
            ),
            'cnbc_world': RSSFeed(
                name='CNBC World News',
                url='https://www.cnbc.com/id/100003114/device/rss/rss.html',
                category='general_financial',
                priority=1
            ),
            'yahoo_finance': RSSFeed(
                name='Yahoo Finance',
                url='https://feeds.finance.yahoo.com/rss/2.0/headline',
                category='general_financial',
                priority=1
            ),
            'bloomberg_markets': RSSFeed(
                name='Bloomberg Markets',
                url='https://feeds.bloomberg.com/markets/news.rss',
                category='general_financial',
                priority=1
            ),
            
            # Investing & Markets - VERIFIED WORKING
            'motley_fool': RSSFeed(
                name='The Motley Fool',
                url='https://www.fool.com/feeds/index.aspx?id=foolwatch&format=rss2',
                category='investing_markets',
                priority=1  # Upgraded to priority 1 due to high quality
            ),
            'thestreet': RSSFeed(
                name='TheStreet',
                url='https://www.thestreet.com/.rss/full/',
                category='investing_markets',
                priority=1  # Upgraded to priority 1 due to high volume and quality
            ),
            'seeking_alpha': RSSFeed(
                name='Seeking Alpha',
                url='https://seekingalpha.com/feed.xml',
                category='investing_markets',
                priority=1
            ),
            
            # Economy & Policy - VERIFIED WORKING
            'npr_economy': RSSFeed(
                name='NPR Economy',
                url='https://feeds.npr.org/1019/rss.xml',
                category='economy_policy',
                priority=1
            ),

            
            # Cryptocurrency - VERIFIED WORKING (Balanced to reduce crypto overweight)
            'coindesk': RSSFeed(
                name='CoinDesk',
                url='https://www.coindesk.com/arc/outboundfeeds/rss/',
                category='cryptocurrency',
                priority=1
            ),
            'cointelegraph': RSSFeed(
                name='Cointelegraph',
                url='https://cointelegraph.com/rss',
                category='cryptocurrency',
                priority=2,  # Reduced priority to balance crypto content
                enabled=True
            ),
            
            # Fintech - VERIFIED WORKING
            'techcrunch_fintech': RSSFeed(
                name='TechCrunch Fintech',
                url='https://techcrunch.com/tag/fintech/feed/',
                category='fintech',
                priority=2
            ),
            
            # REMOVED SOURCES (Failed during testing):
            # - Reuters Business: Network issues
            # - Kiplinger Investing: 404 error
            # - ZeroHedge: 404 error  
            # - Finextra: 0 articles returned
            # - Decrypt: Removed to balance crypto content (was producing 55 articles)
        }
    
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
            filename = generate_timestamp_filename("multi_source_news")
        
        from signalmuse.utils.utils import config
        filepath = config.data_dir / filename
        return save_dataframe_to_csv(df, str(filepath), logger)

def main():
    """Test the multi-source scraper"""
    scraper = MultiSourceScraper()
    
    print("🔍 Multi-Source RSS Scraper")
    print("=" * 50)
    
    # Fetch all feeds
    print("\n📡 Fetching all feeds...")
    df = scraper.fetch_all_feeds(max_articles_per_feed=20)
    
    if not df.empty:
        print(f"✅ Fetched {len(df)} articles from {df['source'].nunique()} sources")
        
        # Show summary by category
        print("\n📊 Articles by Category:")
        category_counts = df['category'].value_counts()
        for category, count in category_counts.items():
            print(f"  {category}: {count} articles")
        
        # Save to CSV
        filepath = scraper.save_to_csv(df)
        print(f"\n💾 Data saved to: {filepath}")
        
        # Show sample articles
        print("\n📰 Sample Articles:")
        for _, row in df.head(3).iterrows():
            print(f"  {row['source']}: {row['title'][:80]}...")
    
    else:
        print("❌ No articles fetched")

if __name__ == "__main__":
    main() 