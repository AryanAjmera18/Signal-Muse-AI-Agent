#!/usr/bin/env python3
"""
MarketWatch Economic Calendar Scraper

Scrapes MarketWatch's economic calendar to get real economic indicators data
for the morning finance brief.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
import time
import sys
from pathlib import Path

# Add project root to path for absolute imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from signalmuse.utils.utils import get_logger

logger = get_logger(__name__)


class MarketWatchEconomicScraper:
    """Scrapes MarketWatch economic calendar for economic indicators"""
    
    def __init__(self):
        self.base_url = "https://www.marketwatch.com"
        self.economic_calendar_url = "https://www.marketwatch.com/economy-politics/calendar"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    def get_economic_indicators(self) -> Dict[str, str]:
        """
        Get economic indicators from MarketWatch economic calendar
        
        Returns:
            Dict[str, str]: Economic indicators with values
        """
        try:
            logger.info("Scraping MarketWatch economic calendar...")
            
            # Get today's date and recent dates
            today = datetime.now()
            recent_dates = [
                today.strftime('%Y-%m-%d'),
                (today - timedelta(days=1)).strftime('%Y-%m-%d'),
                (today - timedelta(days=2)).strftime('%Y-%m-%d'),
                (today - timedelta(days=3)).strftime('%Y-%m-%d'),
                (today - timedelta(days=7)).strftime('%Y-%m-%d'),
            ]
            
            indicators = {}
            
            for date in recent_dates:
                try:
                    date_indicators = self._scrape_date_economic_data(date)
                    if date_indicators:
                        indicators.update(date_indicators)
                        logger.debug(f"Found {len(date_indicators)} indicators for {date}")
                        
                        # If we have enough data, break
                        if len(indicators) >= 5:
                            break
                            
                except Exception as e:
                    logger.debug(f"Failed to scrape {date}: {e}")
                    continue
                    
                # Be respectful with rate limiting
                time.sleep(1)
            
            logger.info(f"Successfully scraped {len(indicators)} economic indicators")
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to get economic indicators: {e}")
            return {}
    
    def _scrape_date_economic_data(self, date: str) -> Dict[str, str]:
        """
        Scrape economic data for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dict[str, str]: Economic indicators for that date
        """
        try:
            # MarketWatch economic calendar URL (they show current week by default)
            url = self.economic_calendar_url
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            indicators = {}
            
            # MarketWatch economic calendar is typically in a table format
            # Look for the main content area that contains economic data
            main_content = soup.find('main') or soup.find('div', {'class': 'content'}) or soup.find('div', {'id': 'main'})
            
            if main_content:
                # Look for any text that contains economic indicators
                page_text = main_content.get_text().lower()
                
                # Extract economic indicators using regex patterns
                import re
                
                # Look for CPI/Inflation data
                cpi_patterns = [
                    r'cpi.*?(\d+\.?\d*)\s*%',
                    r'inflation.*?(\d+\.?\d*)\s*%',
                    r'consumer price index.*?(\d+\.?\d*)\s*%'
                ]
                
                for pattern in cpi_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        indicators['inflation_cpi'] = f"{matches[0]}% YoY"
                        break
                
                # Look for employment data
                employment_patterns = [
                    r'non.?farm payrolls.*?(\d+(?:,\d+)*)\s*k',
                    r'employment.*?(\d+(?:,\d+)*)\s*k',
                    r'jobs.*?(\d+(?:,\d+)*)\s*k'
                ]
                
                for pattern in employment_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        indicators['non_farm_payrolls'] = f"{matches[0].replace(',', '')}K"
                        break
                
                # Look for unemployment rate
                unemployment_patterns = [
                    r'unemployment rate.*?(\d+\.?\d*)\s*%',
                    r'unemployment.*?(\d+\.?\d*)\s*%'
                ]
                
                for pattern in unemployment_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        indicators['unemployment_rate'] = f"{matches[0]}%"
                        break
                
                # Look for PMI data
                pmi_patterns = [
                    r'pmi manufacturing.*?(\d+\.?\d*)',
                    r'ism manufacturing.*?(\d+\.?\d*)',
                    r'manufacturing pmi.*?(\d+\.?\d*)'
                ]
                
                for pattern in pmi_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        indicators['pmi_manufacturing'] = matches[0]
                        break
                
                # Look for retail sales
                retail_patterns = [
                    r'retail sales.*?(\d+\.?\d*)\s*%',
                    r'retail.*?(\d+\.?\d*)\s*%'
                ]
                
                for pattern in retail_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        indicators['retail_sales'] = f"{matches[0]}%"
                        break
            
            # If we still don't have data, try alternative approach - look for specific economic news articles
            if not indicators:
                # Look for economic news headlines that might contain data
                headlines = soup.find_all(['h1', 'h2', 'h3', 'h4'])
                for headline in headlines:
                    headline_text = headline.get_text().lower()
                    
                    # Check for economic indicators in headlines
                    if 'cpi' in headline_text or 'inflation' in headline_text:
                        # Extract percentage
                        percentage_match = re.search(r'(\d+\.?\d*)\s*%', headline_text)
                        if percentage_match:
                            indicators['inflation_cpi'] = f"{percentage_match.group(1)}% YoY"
                    
                    if 'employment' in headline_text or 'jobs' in headline_text:
                        # Extract number
                        number_match = re.search(r'(\d+(?:,\d+)*)\s*k', headline_text)
                        if number_match:
                            indicators['non_farm_payrolls'] = f"{number_match.group(1).replace(',', '')}K"
            
            return indicators
            
        except Exception as e:
            logger.debug(f"Failed to scrape date {date}: {e}")
            return {}
    
    def _parse_economic_event(self, event_element) -> Optional[Dict[str, str]]:
        """
        Parse individual economic event from HTML element
        
        Args:
            event_element: BeautifulSoup element containing event data
            
        Returns:
            Optional[Dict[str, str]]: Parsed event data
        """
        try:
            # Get all text from the event element
            event_text = event_element.get_text(strip=True).lower()
            
            # Skip if no meaningful text
            if not event_text or len(event_text) < 10:
                return None
            
            # Extract event name - try multiple approaches
            event_name = ""
            
            # Try to find event name in various ways
            name_selectors = [
                'td[class*="event"]',
                'div[class*="event"]',
                'span[class*="event"]',
                'td[class*="name"]',
                'div[class*="name"]',
                'span[class*="name"]'
            ]
            
            for selector in name_selectors:
                name_element = event_element.select_one(selector)
                if name_element:
                    event_name = name_element.get_text(strip=True).lower()
                    break
            
            # If no specific name element found, try to extract from the full text
            if not event_name:
                # Look for common economic indicator patterns in the text
                economic_keywords = [
                    'non-farm payrolls', 'employment', 'unemployment rate', 'unemployment',
                    'cpi', 'consumer price index', 'inflation', 'pmi manufacturing',
                    'ism manufacturing', 'pmi services', 'ism services', 'gdp',
                    'gross domestic product', 'retail sales', 'housing starts',
                    'industrial production', 'federal reserve', 'fed', 'interest rate'
                ]
                
                for keyword in economic_keywords:
                    if keyword in event_text:
                        event_name = keyword
                        break
            
            # Extract actual value - try multiple approaches
            actual_value = ""
            
            # Try to find actual value in various ways
            actual_selectors = [
                'td[class*="actual"]',
                'div[class*="actual"]',
                'span[class*="actual"]',
                'td[class*="value"]',
                'div[class*="value"]',
                'span[class*="value"]'
            ]
            
            for selector in actual_selectors:
                actual_element = event_element.select_one(selector)
                if actual_element:
                    actual_value = actual_element.get_text(strip=True)
                    break
            
            # If no specific actual element found, try to extract from text
            if not actual_value:
                # Look for number patterns in the text
                import re
                number_patterns = [
                    r'(\d+(?:\.\d+)?)\s*%',  # Percentage
                    r'(\d+(?:,\d+)*(?:\.\d+)?)\s*k',  # Thousands with K
                    r'(\d+(?:,\d+)*(?:\.\d+)?)',  # General numbers
                ]
                
                for pattern in number_patterns:
                    matches = re.findall(pattern, event_text)
                    if matches:
                        actual_value = matches[0]
                        break
            
            # Extract previous value for context
            previous_value = ""
            prev_selectors = [
                'td[class*="previous"]',
                'div[class*="previous"]',
                'span[class*="previous"]'
            ]
            
            for selector in prev_selectors:
                prev_element = event_element.select_one(selector)
                if prev_element:
                    previous_value = prev_element.get_text(strip=True)
                    break
            
            # Map event names to our indicator keys
            indicator_mapping = {
                'non-farm payrolls': 'non_farm_payrolls',
                'employment': 'non_farm_payrolls',
                'unemployment rate': 'unemployment_rate',
                'unemployment': 'unemployment_rate',
                'cpi': 'inflation_cpi',
                'consumer price index': 'inflation_cpi',
                'inflation': 'inflation_cpi',
                'pmi manufacturing': 'pmi_manufacturing',
                'ism manufacturing': 'pmi_manufacturing',
                'pmi services': 'pmi_services',
                'ism services': 'pmi_services',
                'gdp': 'gdp_growth',
                'gross domestic product': 'gdp_growth',
                'retail sales': 'retail_sales',
                'housing starts': 'housing_starts',
                'industrial production': 'industrial_production'
            }
            
            # Find matching indicator
            indicator_key = None
            for event_keyword, indicator_key in indicator_mapping.items():
                if event_keyword in event_name:
                    break
            
            if not indicator_key:
                return None
            
            # Format the value based on indicator type
            formatted_value = self._format_indicator_value(indicator_key, actual_value, previous_value)
            
            if formatted_value:
                return {
                    'name': indicator_key,
                    'value': formatted_value
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to parse economic event: {e}")
            return None
    
    def _format_indicator_value(self, indicator_key: str, actual_value: str, previous_value: str) -> str:
        """
        Format indicator value based on type
        
        Args:
            indicator_key: Type of indicator
            actual_value: Actual reported value
            previous_value: Previous period value
            
        Returns:
            str: Formatted value
        """
        try:
            if not actual_value or actual_value.lower() in ['n/a', '--', '']:
                return ""
            
            # Clean the value
            actual_value = actual_value.strip()
            previous_value = previous_value.strip() if previous_value else ""
            
            # Format based on indicator type
            if indicator_key == 'non_farm_payrolls':
                # Extract number and add K suffix
                number_match = re.search(r'([+-]?\d+(?:,\d+)*(?:\.\d+)?)', actual_value)
                if number_match:
                    number = number_match.group(1).replace(',', '')
                    return f"{number}K"
                return actual_value
                
            elif indicator_key == 'unemployment_rate':
                # Add % if not present
                if '%' not in actual_value:
                    return f"{actual_value}%"
                return actual_value
                
            elif indicator_key == 'inflation_cpi':
                # Add % YoY if not present
                if '%' not in actual_value:
                    return f"{actual_value}% YoY"
                elif 'YoY' not in actual_value:
                    return f"{actual_value} YoY"
                return actual_value
                
            elif indicator_key in ['pmi_manufacturing', 'pmi_services']:
                # PMI values are typically just numbers
                number_match = re.search(r'(\d+(?:\.\d+)?)', actual_value)
                if number_match:
                    return number_match.group(1)
                return actual_value
                
            elif indicator_key == 'gdp_growth':
                # Add % if not present
                if '%' not in actual_value:
                    return f"{actual_value}%"
                return actual_value
                
            elif indicator_key == 'retail_sales':
                # Add % if not present
                if '%' not in actual_value:
                    return f"{actual_value}%"
                return actual_value
                
            else:
                return actual_value
                
        except Exception as e:
            logger.debug(f"Failed to format indicator value: {e}")
            return actual_value
    
    def get_latest_indicators(self) -> Dict[str, str]:
        """
        Get the most recent economic indicators
        
        Returns:
            Dict[str, str]: Latest economic indicators
        """
        try:
            # Try to get indicators from the last few days
            indicators = self.get_economic_indicators()
            
            # If we don't have enough data, try alternative sources
            if len(indicators) < 3:
                logger.info("Insufficient data from MarketWatch, trying alternative sources...")
                alternative_indicators = self._get_alternative_sources()
                indicators.update(alternative_indicators)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to get latest indicators: {e}")
            return {}
    
    def _get_alternative_sources(self) -> Dict[str, str]:
        """
        Get economic indicators from alternative sources
        
        Returns:
            Dict[str, str]: Economic indicators from alternative sources
        """
        try:
            # Try Yahoo Finance for some indicators
            import yfinance as yf
            
            indicators = {}
            
            # Get 10-year Treasury yield
            try:
                treasury = yf.Ticker("^TNX")
                treasury_info = treasury.info
                if 'regularMarketPrice' in treasury_info:
                    indicators['treasury_yield'] = f"{treasury_info['regularMarketPrice']:.2f}%"
            except:
                pass
            
            # Get DXY (US Dollar Index)
            try:
                dxy = yf.Ticker("DX-Y.NYB")
                dxy_info = dxy.info
                if 'regularMarketPrice' in dxy_info:
                    indicators['dollar_index'] = f"{dxy_info['regularMarketPrice']:.2f}"
            except:
                pass
            
            return indicators
            
        except Exception as e:
            logger.debug(f"Alternative sources failed: {e}")
            return {}


def get_marketwatch_economic_indicators() -> Dict[str, str]:
    """
    Convenience function to get economic indicators from MarketWatch
    
    Returns:
        Dict[str, str]: Economic indicators
    """
    try:
        scraper = MarketWatchEconomicScraper()
        return scraper.get_latest_indicators()
    except Exception as e:
        logger.error(f"MarketWatch scraper failed: {e}")
        return {}


if __name__ == "__main__":
    # Test the scraper
    scraper = MarketWatchEconomicScraper()
    indicators = scraper.get_latest_indicators()
    
    print("Economic Indicators from MarketWatch:")
    for key, value in indicators.items():
        print(f"  {key}: {value}")
