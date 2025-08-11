import scrapy
from datetime import datetime
import os

# Get the absolute path to the data directory
def get_output_path():
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate to the project root and then to data/real
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    output_dir = os.path.join(project_root, 'signalmuse', 'data', 'real')
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, 'earnings_data.json')

class EarningsSpider(scrapy.Spider):
    name = 'earnings'
    allowed_domains = ['www.marketwatch.com']
    start_urls = ['https://www.marketwatch.com/tools/earnings-calendar']
    
    # Custom settings for this spider
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        },
        'FEEDS': {
            get_output_path(): {
                'format': 'json',
                'overwrite': True,
            }
        }
    }

    def start_requests(self):
        """Generate initial requests with custom headers"""
        headers = {
            'Referer': 'https://www.google.com/',
        }
        
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                dont_filter=True
            )

    def parse(self, response):
        """Main parsing method to extract earnings data"""
        
        if response.status != 200:
            self.logger.error(f"Got status {response.status} for {response.url}")
            return
        
        # Check if we got blocked by Cloudflare
        if "Please enable JS and disable any ad blocker" in response.text:
            self.logger.warning("MarketWatch blocked by Cloudflare protection")
            return
        
        # Look for earnings data in MarketWatch format
        table_rows = response.css('tr.table__row')
        
        self.logger.info(f"Found {len(table_rows)} earnings entries")
        
        for row in table_rows:
            try:
                # Extract company information (first column - fixed column)
                company_cell = row.css('td.overflow__cell.fixed--column.align--left')
                company_name = self._extract_text(company_cell.css('div.cell__content.fixed--cell a.link::text'))
                
                # Extract ticker symbol (exclude the fixed--column)
                ticker_cells = row.css('td.overflow__cell.align--left:not(.fixed--column)')
                ticker = None
                
                if len(ticker_cells) > 0:
                    ticker_cell = ticker_cells[0]
                    ticker = self._extract_text(ticker_cell.css('div.cell__content a.link::text'))
                
                if company_name and ticker:
                    # Extract other data cells (excluding company and ticker columns)
                    data_cells = row.css('td.overflow__cell:not(.fixed--column):not(.align--left)')
                    
                    earnings_item = {
                        'company_name': company_name,
                        'ticker_symbol': ticker,
                        'source': 'marketwatch',
                        'scraped_at': datetime.now().isoformat(),
                        'source_url': response.url
                    }
                    
                    # Add additional data if available
                    if len(data_cells) > 0:
                        earnings_item['earnings_date'] = self._extract_text(data_cells[0].css('div.cell__content::text'))
                    if len(data_cells) > 1:
                        earnings_item['estimated_eps'] = self._extract_text(data_cells[1].css('div.cell__content::text'))
                    if len(data_cells) > 2:
                        earnings_item['prior_eps'] = self._extract_text(data_cells[2].css('div.cell__content::text'))
                    
                    # Extract surprise data
                    surprise_cells = row.css('td.overflow__cell.negative, td.overflow__cell.positive') or data_cells[-1:] if data_cells else []
                    if surprise_cells:
                        surprise_cell = surprise_cells[-1]
                        surprise_text = self._extract_text(surprise_cell.css('div.cell__content::text'))
                        earnings_item['surprise'] = surprise_text
                    
                    yield earnings_item
                    
            except Exception as e:
                self.logger.error(f"Error processing row: {e}")

    def _extract_text(self, selector):
        """Safely extract text from CSS selector"""
        if selector:
            text = selector.get()
            return text.strip() if text else None
        return None
