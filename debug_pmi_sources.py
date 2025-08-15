#!/usr/bin/env python3
"""
Debug PMI sources to see exactly why they're failing
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'signalmuse'))

def test_trading_economics_pmi():
    """Test Trading Economics PMI sources directly"""
    print("🔍 TESTING TRADING ECONOMICS PMI SOURCES")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    })
    
    # Test Manufacturing PMI
    print("\n1. Testing Manufacturing PMI...")
    try:
        url = "https://tradingeconomics.com/united-states/manufacturing-pmi"
        print(f"URL: {url}")
        
        response = session.get(url, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find the main value
            selectors_to_try = [
                {'id': 'p'},
                {'class': 'table-summary-value'},
                {'class': 'indicator-value'},
                {'id': 'actual'},
                {'class': 'te-indicator-value'}
            ]
            
            print("Trying different selectors...")
            for i, selector in enumerate(selectors_to_try):
                elements = soup.find_all('div', selector) + soup.find_all('span', selector)
                if elements:
                    print(f"  Selector {i+1} ({selector}): Found {len(elements)} elements")
                    for j, elem in enumerate(elements[:3]):  # Show first 3
                        text = elem.get_text().strip()
                        print(f"    Element {j+1}: '{text}'")
                        
                        # Try to extract PMI value
                        pmi_match = re.search(r'(\d{2}\.?\d?)', text)
                        if pmi_match:
                            value = pmi_match.group(1)
                            try:
                                pmi_val = float(value)
                                if 35 <= pmi_val <= 65:
                                    print(f"    ✅ VALID PMI VALUE: {value}")
                                    return value
                                else:
                                    print(f"    ❌ PMI value {value} out of range (35-65)")
                            except:
                                pass
                else:
                    print(f"  Selector {i+1} ({selector}): No elements found")
            
            # Try searching in all text
            print("\nSearching in full page text...")
            page_text = soup.get_text()
            pmi_patterns = [
                r'PMI.*?(\d{2}\.\d)',
                r'Manufacturing.*?(\d{2}\.\d)',
                r'Index.*?(\d{2}\.\d)',
                r'(\d{2}\.\d).*?PMI'
            ]
            
            for pattern in pmi_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    print(f"  Pattern '{pattern}' found: {matches[:5]}")  # Show first 5
                    for match in matches:
                        try:
                            pmi_val = float(match)
                            if 35 <= pmi_val <= 65:
                                print(f"    ✅ VALID PMI VALUE: {match}")
                                return match
                        except:
                            pass
            
            print("❌ No valid PMI values found")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Trading Economics Manufacturing PMI failed: {e}")
    
    # Test Services PMI
    print("\n2. Testing Services PMI...")
    try:
        url = "https://tradingeconomics.com/united-states/services-pmi"
        print(f"URL: {url}")
        
        response = session.get(url, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Similar process for services
            print("Searching for Services PMI...")
            page_text = soup.get_text()
            
            # Look for any PMI-like values
            pmi_values = re.findall(r'(\d{2}\.\d)', page_text)
            valid_pmis = []
            
            for value in pmi_values:
                try:
                    pmi_val = float(value)
                    if 35 <= pmi_val <= 65:
                        valid_pmis.append(value)
                except:
                    pass
            
            if valid_pmis:
                print(f"✅ Found valid PMI values: {valid_pmis[:5]}")
                return valid_pmis[0]
            else:
                print("❌ No valid Services PMI values found")
                
    except Exception as e:
        print(f"❌ Trading Economics Services PMI failed: {e}")
    
    return None

def test_alternative_pmi_sources():
    """Test alternative PMI sources"""
    print("\n🔍 TESTING ALTERNATIVE PMI SOURCES")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Test Investing.com
    print("\n1. Testing Investing.com...")
    try:
        url = "https://www.investing.com/economic-calendar/ism-manufacturing-pmi-173"
        response = session.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Look for actual values
            actual_elements = soup.find_all(text=re.compile(r'\d{2}\.\d'))
            valid_pmis = []
            
            for text in actual_elements:
                pmi_match = re.search(r'(\d{2}\.\d)', str(text))
                if pmi_match:
                    value = pmi_match.group(1)
                    try:
                        pmi_val = float(value)
                        if 35 <= pmi_val <= 65:
                            valid_pmis.append(value)
                    except:
                        pass
            
            if valid_pmis:
                print(f"✅ Investing.com PMI values: {valid_pmis[:3]}")
            else:
                print("❌ No valid PMI values from Investing.com")
                
    except Exception as e:
        print(f"❌ Investing.com failed: {e}")
    
    # Test FRED API (if available)
    print("\n2. Testing FRED API for PMI...")
    try:
        # Try FRED for ISM PMI
        url = "https://api.stlouisfed.org/fred/series/observations?series_id=NAPM&api_key=DEMO_KEY&file_type=json&limit=1&sort_order=desc"
        response = session.get(url, timeout=10)
        print(f"FRED Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data and data['observations']:
                obs = data['observations'][0]
                value = obs.get('value')
                date = obs.get('date')
                if value and value != '.':
                    print(f"✅ FRED PMI: {value} (as of {date})")
                    return value, date
        else:
            print(f"❌ FRED API error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ FRED API failed: {e}")
    
    return None

def test_current_pmi_fetcher():
    """Test our current PMI fetcher to see what's failing"""
    print("\n🔍 TESTING CURRENT PMI FETCHER")
    print("=" * 60)
    
    try:
        from signalmuse.morning_brief_module.fresh_data_fetcher import FreshDataFetcher
        
        fetcher = FreshDataFetcher()
        
        print("Testing Manufacturing PMI fetcher...")
        mfg_value, mfg_date = fetcher._get_latest_pmi_manufacturing()
        print(f"Manufacturing Result: {mfg_value}, {mfg_date}")
        
        print("\nTesting Services PMI fetcher...")
        svc_value, svc_date = fetcher._get_latest_pmi_services()
        print(f"Services Result: {svc_value}, {svc_date}")
        
    except Exception as e:
        print(f"❌ Current fetcher test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 PMI SOURCES DEBUG SESSION")
    print("This will test each PMI source individually to find what's working")
    print("=" * 80)
    
    # Test all sources
    test_trading_economics_pmi()
    test_alternative_pmi_sources()
    test_current_pmi_fetcher()
    
    print("\n" + "=" * 80)
    print("🏁 DEBUG COMPLETE")
    print("Check the results above to see which PMI sources are actually working")
