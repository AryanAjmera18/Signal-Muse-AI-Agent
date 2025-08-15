#!/usr/bin/env python3
"""
Test script for real economic indicators and Fed speak data
Run this in your venv to test the new implementations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'signalmuse'))

def test_economic_indicators():
    """Test the enhanced economic indicators fetching"""
    print("=" * 60)
    print("TESTING ECONOMIC INDICATORS")
    print("=" * 60)
    
    try:
        from signalmuse.morning_brief_module.data_processor import fetch_real_economic_indicators, get_economic_indicators
        
        print("1. Testing fetch_real_economic_indicators()...")
        indicators = fetch_real_economic_indicators()
        
        if indicators:
            print(f"✅ Successfully fetched {len(indicators)} indicators:")
            for key, value in indicators.items():
                print(f"   • {key}: {value}")
        else:
            print("⚠️  No real indicators fetched, will use fallback data")
        
        print("\n2. Testing formatted economic indicators...")
        formatted = get_economic_indicators()
        print("Formatted output:")
        print(formatted)
        
    except Exception as e:
        print(f"❌ Error testing economic indicators: {e}")
        import traceback
        traceback.print_exc()

def test_fedspeak():
    """Test the enhanced Fed speak data"""
    print("\n" + "=" * 60)
    print("TESTING FEDSPEAK DATA")
    print("=" * 60)
    
    try:
        from signalmuse.morning_brief_module.data_processor import get_fedspeak_data
        
        print("Testing get_fedspeak_data()...")
        fedspeak = get_fedspeak_data()
        
        print("Fed speak output:")
        print(fedspeak)
        
    except Exception as e:
        print(f"❌ Error testing Fed speak: {e}")
        import traceback
        traceback.print_exc()

def test_full_morning_brief():
    """Test generating a full morning brief with real data"""
    print("\n" + "=" * 60)
    print("TESTING FULL MORNING BRIEF GENERATION")
    print("=" * 60)
    
    try:
        from signalmuse.morning_brief_module.main import MorningBriefGenerator
        
        print("Generating morning brief with real data...")
        generator = MorningBriefGenerator()
        brief_path = generator.generate_morning_brief()
        
        print(f"✅ Morning brief generated successfully!")
        print(f"📄 File saved to: {brief_path}")
        
        # Read and show a snippet
        with open(brief_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            # Show economic indicators section
            print("\n📊 Economic Indicators Section:")
            in_economic_section = False
            for i, line in enumerate(lines):
                if "Economic Indicators" in line:
                    in_economic_section = True
                    # Show next 10 lines
                    for j in range(i, min(i+10, len(lines))):
                        print(lines[j])
                    break
            
            # Show Fed speak section
            print("\n🎤 Fed Speak Section:")
            in_fed_section = False
            for i, line in enumerate(lines):
                if "Fedspeak" in line:
                    in_fed_section = True
                    # Show next 10 lines
                    for j in range(i, min(i+10, len(lines))):
                        print(lines[j])
                    break
        
    except Exception as e:
        print(f"❌ Error testing full morning brief: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 TESTING REAL DATA INTEGRATION")
    print("Make sure you're running this in your venv!")
    print()
    
    # Run all tests
    test_economic_indicators()
    test_fedspeak()
    test_full_morning_brief()
    
    print("\n" + "=" * 60)
    print("✅ TESTING COMPLETE")
    print("=" * 60)
    print("Check the generated morning brief file to see the real data!")
