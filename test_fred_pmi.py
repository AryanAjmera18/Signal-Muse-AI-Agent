#!/usr/bin/env python3
"""
Test FRED API for PMI data specifically
"""

import sys
import os
import requests
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'signalmuse'))

def test_fred_pmi_direct():
    """Test FRED API for PMI data directly"""
    print("🏛️ TESTING FRED API FOR PMI DATA")
    print("=" * 60)
    
    session = requests.Session()
    
    # Test PMI Manufacturing (NAPM)
    print("\n1. Testing PMI Manufacturing (NAPM series)...")
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': 'NAPM',  # ISM Manufacturing PMI
            'api_key': 'DEMO_KEY',
            'file_type': 'json',
            'limit': 5,
            'sort_order': 'desc'
        }
        
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        response = session.get(url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            if 'observations' in data:
                observations = data['observations']
                print(f"Found {len(observations)} observations")
                
                for i, obs in enumerate(observations):
                    value = obs.get('value', 'N/A')
                    date = obs.get('date', 'N/A')
                    print(f"  {i+1}. Date: {date}, Value: {value}")
                    
                    if value and value != '.' and value != 'N/A':
                        try:
                            pmi_val = float(value)
                            if 35 <= pmi_val <= 65:
                                date_obj = datetime.strptime(date, '%Y-%m-%d')
                                date_str = date_obj.strftime('%b %Y')
                                print(f"  ✅ VALID PMI Manufacturing: {value} ({date_str})")
                                break
                        except ValueError:
                            continue
            else:
                print(f"❌ No observations in response")
        else:
            print(f"❌ HTTP Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ FRED Manufacturing PMI failed: {e}")
    
    # Test PMI Services (NAPMNMI)
    print("\n2. Testing PMI Services (NAPMNMI series)...")
    try:
        params = {
            'series_id': 'NAPMNMI',  # ISM Non-Manufacturing PMI
            'api_key': 'DEMO_KEY',
            'file_type': 'json',
            'limit': 5,
            'sort_order': 'desc'
        }
        
        print(f"Params: {params}")
        
        response = session.get(url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'observations' in data:
                observations = data['observations']
                print(f"Found {len(observations)} observations")
                
                for i, obs in enumerate(observations):
                    value = obs.get('value', 'N/A')
                    date = obs.get('date', 'N/A')
                    print(f"  {i+1}. Date: {date}, Value: {value}")
                    
                    if value and value != '.' and value != 'N/A':
                        try:
                            pmi_val = float(value)
                            if 35 <= pmi_val <= 65:
                                date_obj = datetime.strptime(date, '%Y-%m-%d')
                                date_str = date_obj.strftime('%b %Y')
                                print(f"  ✅ VALID PMI Services: {value} ({date_str})")
                                break
                        except ValueError:
                            continue
            else:
                print(f"❌ No observations in response")
        else:
            print(f"❌ HTTP Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ FRED Services PMI failed: {e}")

def test_updated_pmi_fetcher():
    """Test our updated PMI fetcher"""
    print("\n🔍 TESTING UPDATED PMI FETCHER")
    print("=" * 60)
    
    try:
        from signalmuse.morning_brief_module.fresh_data_fetcher import FreshDataFetcher
        
        fetcher = FreshDataFetcher()
        
        print("Testing updated Manufacturing PMI fetcher...")
        mfg_value, mfg_date = fetcher._get_latest_pmi_manufacturing()
        if mfg_value and mfg_date:
            print(f"✅ Manufacturing PMI: {mfg_value} ({mfg_date})")
        else:
            print(f"❌ Manufacturing PMI: No data returned")
        
        print("\nTesting updated Services PMI fetcher...")
        svc_value, svc_date = fetcher._get_latest_pmi_services()
        if svc_value and svc_date:
            print(f"✅ Services PMI: {svc_value} ({svc_date})")
        else:
            print(f"❌ Services PMI: No data returned")
            
        return (mfg_value is not None and mfg_date is not None), (svc_value is not None and svc_date is not None)
        
    except Exception as e:
        print(f"❌ Updated fetcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, False

if __name__ == "__main__":
    print("🏛️ FRED API PMI TESTING")
    print("Testing FRED API as a reliable source for PMI data")
    print("=" * 70)
    
    # Test FRED API directly
    test_fred_pmi_direct()
    
    # Test our updated fetcher
    mfg_success, svc_success = test_updated_pmi_fetcher()
    
    print("\n" + "=" * 70)
    print("🏁 FRED PMI TEST RESULTS")
    print(f"Manufacturing PMI: {'✅ WORKING' if mfg_success else '❌ FAILED'}")
    print(f"Services PMI: {'✅ WORKING' if svc_success else '❌ FAILED'}")
    
    if mfg_success and svc_success:
        print("\n🎉 SUCCESS! FRED API PMI data is working!")
        print("PMI indicators should now show real data in morning briefs.")
    elif mfg_success or svc_success:
        print("\n⚠️  PARTIAL SUCCESS - One PMI indicator working")
    else:
        print("\n❌ PMI indicators still need work")
        
    print("\n📊 FRED API provides official PMI data from the Federal Reserve")
    print("This should be more reliable than web scraping Trading Economics or ISM")
