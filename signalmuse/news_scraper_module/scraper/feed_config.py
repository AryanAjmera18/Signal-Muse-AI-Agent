"""
RSS Feed Configuration

Contains RSS feed definitions and configurations for the news scraper.
Modular design allows easy addition/removal of feeds without code changes elsewhere.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class FeedCategory(Enum):
    """Enum for feed categories"""
    GENERAL_FINANCIAL = "general_financial"
    INVESTING_MARKETS = "investing_markets"
    ECONOMY_POLICY = "economy_policy"
    CRYPTOCURRENCY = "cryptocurrency"
    FINTECH = "fintech"

class FeedPriority(Enum):
    """Enum for feed priorities"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3

@dataclass
class RSSFeed:
    """RSS feed configuration"""
    name: str
    url: str
    category: str
    priority: int = 1  # 1=high, 2=medium, 3=low
    enabled: bool = True
    rate_limit: float = 1.0  # seconds between requests
    description: str = ""

class FeedManager:
    """Manages RSS feed configurations with easy add/remove functionality"""
    
    def __init__(self):
        self.feeds = {}
        self._initialize_default_feeds()
    
    def _initialize_default_feeds(self):
        """Initialize with default feed configurations"""
        default_feeds = {
            # General Financial News - HIGH PRIORITY
            'marketwatch_top': RSSFeed(
                name='MarketWatch Top Stories',
                url='https://feeds.marketwatch.com/marketwatch/topstories/',
                category=FeedCategory.GENERAL_FINANCIAL.value,
                priority=FeedPriority.HIGH.value,
                description='Top financial stories from MarketWatch'
            ),
            'cnbc_world': RSSFeed(
                name='CNBC World News',
                url='https://www.cnbc.com/id/100003114/device/rss/rss.html',
                category=FeedCategory.GENERAL_FINANCIAL.value,
                priority=FeedPriority.HIGH.value,
                description='World news from CNBC'
            ),
            'bloomberg_markets': RSSFeed(
                name='Bloomberg Markets',
                url='https://feeds.bloomberg.com/markets/news.rss',
                category=FeedCategory.GENERAL_FINANCIAL.value,
                priority=FeedPriority.HIGH.value,
                description='Market news from Bloomberg'
            ),
            
            # Investing & Markets - VERIFIED WORKING
            'motley_fool': RSSFeed(
                name='The Motley Fool',
                url='https://www.fool.com/feeds/index.aspx?id=foolwatch&format=rss2',
                category=FeedCategory.INVESTING_MARKETS.value,
                priority=FeedPriority.HIGH.value,
                description='Investment analysis from Motley Fool'
            ),
            'thestreet': RSSFeed(
                name='TheStreet',
                url='https://www.thestreet.com/.rss/full/',
                category=FeedCategory.INVESTING_MARKETS.value,
                priority=FeedPriority.HIGH.value,
                description='Full feed from TheStreet'
            ),
            'seeking_alpha': RSSFeed(
                name='Seeking Alpha',
                url='https://seekingalpha.com/feed.xml',
                category=FeedCategory.INVESTING_MARKETS.value,
                priority=FeedPriority.HIGH.value,
                description='Investment analysis from Seeking Alpha'
            ),
            
            # Economy & Policy - VERIFIED WORKING
            'npr_economy': RSSFeed(
                name='NPR Economy',
                url='https://feeds.npr.org/1019/rss.xml',
                category=FeedCategory.ECONOMY_POLICY.value,
                priority=FeedPriority.HIGH.value,
                description='Economic news from NPR'
            ),
            
            # Cryptocurrency - VERIFIED WORKING (Balanced to reduce crypto overweight)
            'coindesk': RSSFeed(
                name='CoinDesk',
                url='https://www.coindesk.com/arc/outboundfeeds/rss/',
                category=FeedCategory.CRYPTOCURRENCY.value,
                priority=FeedPriority.HIGH.value,
                description='Cryptocurrency news from CoinDesk'
            ),
            'cointelegraph': RSSFeed(
                name='Cointelegraph',
                url='https://cointelegraph.com/rss',
                category=FeedCategory.CRYPTOCURRENCY.value,
                priority=FeedPriority.MEDIUM.value,
                description='Cryptocurrency news from Cointelegraph'
            ),
            
            # Fintech - VERIFIED WORKING
            'techcrunch_fintech': RSSFeed(
                name='TechCrunch Fintech',
                url='https://techcrunch.com/tag/fintech/feed/',
                category=FeedCategory.FINTECH.value,
                priority=FeedPriority.MEDIUM.value,
                description='Fintech news from TechCrunch'
            ),
        }
        
        self.feeds.update(default_feeds)
    
    def add_feed(self, feed_id: str, feed: RSSFeed) -> bool:
        """
        Add a new RSS feed
        
        Args:
            feed_id: Unique identifier for the feed
            feed: RSSFeed configuration object
            
        Returns:
            bool: True if added successfully, False if feed_id already exists
        """
        if feed_id in self.feeds:
            return False
        
        self.feeds[feed_id] = feed
        return True
    
    def remove_feed(self, feed_id: str) -> bool:
        """
        Remove an RSS feed
        
        Args:
            feed_id: Unique identifier for the feed
            
        Returns:
            bool: True if removed successfully, False if feed_id doesn't exist
        """
        if feed_id in self.feeds:
            del self.feeds[feed_id]
            return True
        return False
    
    def enable_feed(self, feed_id: str) -> bool:
        """Enable a feed"""
        if feed_id in self.feeds:
            self.feeds[feed_id].enabled = True
            return True
        return False
    
    def disable_feed(self, feed_id: str) -> bool:
        """Disable a feed"""
        if feed_id in self.feeds:
            self.feeds[feed_id].enabled = False
            return True
        return False
    
    def get_feed(self, feed_id: str) -> Optional[RSSFeed]:
        """Get a specific feed by ID"""
        return self.feeds.get(feed_id)
    
    def get_feeds_by_category(self, category: str) -> Dict[str, RSSFeed]:
        """Get all feeds for a specific category"""
        return {
            feed_id: feed for feed_id, feed in self.feeds.items()
            if feed.category == category and feed.enabled
        }
    
    def get_enabled_feeds(self) -> Dict[str, RSSFeed]:
        """Get all enabled feeds"""
        return {
            feed_id: feed for feed_id, feed in self.feeds.items()
            if feed.enabled
        }
    
    def get_all_feeds(self) -> Dict[str, RSSFeed]:
        """Get all feeds (enabled and disabled)"""
        return self.feeds.copy()
    
    def list_categories(self) -> List[str]:
        """Get list of all available categories"""
        return list(set(feed.category for feed in self.feeds.values()))
    
    def get_feed_summary(self) -> Dict:
        """Get summary of all feeds"""
        summary = {
            'total_feeds': len(self.feeds),
            'enabled_feeds': len(self.get_enabled_feeds()),
            'categories': {},
            'priorities': {}
        }
        
        # Count by category
        for feed in self.feeds.values():
            if feed.category not in summary['categories']:
                summary['categories'][feed.category] = {'total': 0, 'enabled': 0}
            summary['categories'][feed.category]['total'] += 1
            if feed.enabled:
                summary['categories'][feed.category]['enabled'] += 1
        
        # Count by priority
        for feed in self.feeds.values():
            priority = feed.priority
            if priority not in summary['priorities']:
                summary['priorities'][priority] = {'total': 0, 'enabled': 0}
            summary['priorities'][priority]['total'] += 1
            if feed.enabled:
                summary['priorities'][priority]['enabled'] += 1
        
        return summary

# Global feed manager instance
feed_manager = FeedManager()

def get_default_feeds() -> Dict[str, RSSFeed]:
    """Get default feeds (backward compatibility)"""
    return feed_manager.get_enabled_feeds()

def add_feed(feed_id: str, feed: RSSFeed) -> bool:
    """Add a new feed (convenience function)"""
    return feed_manager.add_feed(feed_id, feed)

def remove_feed(feed_id: str) -> bool:
    """Remove a feed (convenience function)"""
    return feed_manager.remove_feed(feed_id)

def get_feeds_by_category(category: str) -> Dict[str, RSSFeed]:
    """Get feeds by category (convenience function)"""
    return feed_manager.get_feeds_by_category(category)
