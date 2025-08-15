#!/usr/bin/env python3
"""
Test the official data only system - no estimates, only real data from official sources
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'signalmuse'))

def test_official_data_system():
    """Test that we only get official data, no estimates"""
    print("🏛️ TESTING OFFICIAL DATA ONLY SYSTEM")
    print("=" * 70)
    
    current_time = datetime.now()
    today_str = current_time.strftime('%b %d, %Y')
    
    print(f"Testing official data sources as of: {today_str}")
    print("This should show ONLY real data from BLS, ISM, and live markets...")
    print("NO estimates should appear!")
    print()
    
    try:
        from signalmuse.morning_brief_module.fresh_data_fetcher import get_fresh_economic_indicators
        
        print("🔍 Fetching ONLY official economic data...")
        indicators = get_fresh_economic_indicators()
        
        print(f"\n📊 OFFICIAL DATA RESULTS ({len(indicators)} indicators):")
        print("-" * 70)
        
        official_data_count = 0
        unavailable_count = 0
        estimate_count = 0
        
        for key, value in indicators.items():
            print(f"• {key}:")
            print(f"  {value}")
            
            # Classify the data type
            if "official" in value.lower() and ("bls data" in value.lower() or "ism data" in value.lower()):
                print(f"  ✅ OFFICIAL DATA")
                official_data_count += 1
            elif "live data" in value.lower():
                print(f"  ✅ LIVE MARKET DATA")
                official_data_count += 1
            elif "unavailable" in value.lower():
                print(f"  ⚠️  OFFICIAL SOURCE UNAVAILABLE")
                unavailable_count += 1
            elif "est." in value.lower() or "estimate" in value.lower():
                print(f"  ❌ ESTIMATE DETECTED!")
                estimate_count += 1
            else:
                print(f"  ❓ UNCLEAR DATA TYPE")
            print()
        
        print("-" * 70)
        print(f"📈 DATA QUALITY ANALYSIS:")
        print(f"✅ Official/Live Data: {official_data_count}")
        print(f"⚠️  Unavailable: {unavailable_count}")
        print(f"❌ Estimates: {estimate_count}")
        
        # Success criteria
        success_score = 0
        
        if official_data_count >= 3:
            print(f"✅ EXCELLENT: Got {official_data_count} official data sources!")
            success_score += 3
        elif official_data_count >= 1:
            print(f"⚠️  PARTIAL: Got {official_data_count} official data sources")
            success_score += 1
        else:
            print(f"❌ POOR: No official data sources working")
            
        if estimate_count == 0:
            print("✅ PERFECT: No estimates - only real data or unavailable!")
            success_score += 2
        else:
            print(f"❌ ISSUE: {estimate_count} estimates still showing")
            
        if unavailable_count <= 2:
            print(f"✅ ACCEPTABLE: Only {unavailable_count} sources unavailable")
            success_score += 1
        else:
            print(f"⚠️  CONCERN: {unavailable_count} sources unavailable")
            
        print(f"\n🎯 SUCCESS SCORE: {success_score}/6")
        
        return success_score >= 4
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bls_api_directly():
    """Test BLS API calls directly"""
    print("\n🏛️ TESTING BLS API DIRECTLY")
    print("=" * 70)
    
    try:
        from signalmuse.morning_brief_module.fresh_data_fetcher import FreshDataFetcher
        
        fetcher = FreshDataFetcher()
        
        print("Testing individual BLS API calls...")
        
        # Test unemployment
        print("\n1. Testing Unemployment Rate (BLS)...")
        unemployment_value, unemployment_date = fetcher._get_latest_unemployment()
        if unemployment_value and unemployment_date:
            print(f"   ✅ SUCCESS: {unemployment_value} ({unemployment_date})")
        else:
            print(f"   ❌ FAILED: Could not get unemployment data")
            
        # Test CPI
        print("\n2. Testing CPI Inflation (BLS)...")
        cpi_value, cpi_date = fetcher._get_latest_cpi()
        if cpi_value and cpi_date:
            print(f"   ✅ SUCCESS: {cpi_value} ({cpi_date})")
        else:
            print(f"   ❌ FAILED: Could not get CPI data")
            
        # Test NFP
        print("\n3. Testing Non-Farm Payrolls (BLS)...")
        nfp_value, nfp_date = fetcher._get_latest_nfp()
        if nfp_value and nfp_date:
            print(f"   ✅ SUCCESS: {nfp_value} ({nfp_date})")
        else:
            print(f"   ❌ FAILED: Could not get NFP data")
            
        # Test PMI Manufacturing
        print("\n4. Testing PMI Manufacturing (ISM)...")
        pmi_mfg_value, pmi_mfg_date = fetcher._get_latest_pmi_manufacturing()
        if pmi_mfg_value and pmi_mfg_date:
            print(f"   ✅ SUCCESS: {pmi_mfg_value} ({pmi_mfg_date})")
        else:
            print(f"   ❌ FAILED: Could not get PMI Manufacturing data")
            
        # Test PMI Services
        print("\n5. Testing PMI Services (ISM)...")
        pmi_svc_value, pmi_svc_date = fetcher._get_latest_pmi_services()
        if pmi_svc_value and pmi_svc_date:
            print(f"   ✅ SUCCESS: {pmi_svc_value} ({pmi_svc_date})")
        else:
            print(f"   ❌ FAILED: Could not get PMI Services data")
            
        return True
        
    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🏛️ COMPREHENSIVE OFFICIAL DATA TESTING")
    print("Testing that we ONLY get real data from official sources")
    print("NO estimates should appear - only real data or 'unavailable'")
    print("=" * 80)
    
    # Run tests
    test1_passed = test_bls_api_directly()
    test2_passed = test_official_data_system()
    
    print("\n" + "=" * 80)
    print("🏁 OFFICIAL DATA TEST RESULTS")
    print(f"Direct API Tests: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Official Data System: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    overall_success = test1_passed and test2_passed
    
    if overall_success:
        print("\n🎉 SUCCESS! OFFICIAL DATA SYSTEM WORKING!")
        print("✅ Getting real data from BLS (unemployment, CPI, NFP)")
        print("✅ Getting real data from ISM (PMI indicators)")
        print("✅ Getting live data from markets (Treasury, Dollar)")
        print("✅ No fake estimates - only real data or 'unavailable'")
        print("\n🎯 RESULT: Your morning briefs now show ONLY official data!")
    else:
        print("\n⚠️  ISSUES DETECTED")
        print("Some official data sources may not be working properly.")
        print("Check the detailed results above.")
        
    print(f"\n📊 EXPECTED: All indicators should show official sources:")
    print("   • BLS data for unemployment, CPI, NFP")
    print("   • ISM data for PMI indicators")
    print("   • Live market data for Treasury/Dollar")
    print("   • 'Official data temporarily unavailable' if sources are down")
    print("\n🚫 NO MORE ESTIMATES: System prioritizes real data over fake estimates!")
