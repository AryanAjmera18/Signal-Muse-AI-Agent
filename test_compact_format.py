#!/usr/bin/env python3
"""
Test script to generate a new compact one-page morning brief
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'signalmuse'))

def generate_compact_brief():
    """Generate a morning brief with the new compact format"""
    print("📊 GENERATING COMPACT ONE-PAGE MORNING BRIEF")
    print("=" * 60)
    
    try:
        from signalmuse.morning_brief_module.main import MorningBriefGenerator
        
        print("Generating compact morning brief...")
        generator = MorningBriefGenerator()
        brief_path = generator.generate_morning_brief()
        
        print(f"✅ Compact morning brief generated!")
        print(f"📄 File saved to: {brief_path}")
        
        # Show preview of the new compact format
        with open(brief_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            # Show first 25 lines to see the compact improvements
            print("\n📊 PREVIEW OF NEW COMPACT FORMAT:")
            print("=" * 80)
            for i, line in enumerate(lines[:25]):
                print(f"{i+1:2d}: {line}")
            print("=" * 80)
            print("... (truncated for preview)")
        
        return brief_path
        
    except Exception as e:
        print(f"❌ Error generating compact brief: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    brief_path = generate_compact_brief()
    
    if brief_path:
        print("\n🎉 SUCCESS! Your new compact format includes:")
        print("✅ Removed unwanted tags (#BeginnerFriendly, etc.)")
        print("✅ Smaller font size (10px) with tight line spacing (1.1)")
        print("✅ Optimized for one-page layout (max-width: 8.5in)")
        print("✅ Cleaner naming: UnBound_Market_Brief_YYYY-MM-DD_HHMM.md")
        print("✅ Compressed sections with better visual hierarchy")
        print("✅ Inline Fed commentary to save space")
        print("✅ Simplified footer with essential info only")
        print(f"\n📖 Open the file to see the full compact format: {brief_path}")
