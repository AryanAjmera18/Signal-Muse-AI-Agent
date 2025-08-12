from itemadapter import ItemAdapter
import json
from datetime import datetime

class EarningsDataPipeline:
    def __init__(self):
        self.file = None
        self.items_scraped = 0
    
    def open_spider(self, spider):
        """Initialize pipeline when spider opens"""
        spider.logger.info("Starting earnings data collection...")
        
    def close_spider(self, spider):
        """Cleanup when spider closes"""
        spider.logger.info(f"Scraped {self.items_scraped} earnings entries")
    
    def process_item(self, item, spider):
        """Process each scraped item"""
        adapter = ItemAdapter(item)
        
        # Skip error items
        if 'error' in adapter:
            spider.logger.error(f"Skipping error item: {adapter['error']}")
            return item
            
        # Validate required fields
        if not adapter.get('company_name') or not adapter.get('ticker_symbol'):
            spider.logger.warning("Skipping item with missing company/ticker data")
            return item
        
        self.items_scraped += 1
        spider.logger.info(f"Processed: {adapter['company_name']} ({adapter['ticker_symbol']})")
        
        return item
