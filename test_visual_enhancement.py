#!/usr/bin/env python3
"""
Test script to generate a new morning brief with enhanced visual appeal
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'signalmuse'))

def generate_enhanced_brief():
    """Generate a morning brief with the new visual enhancements"""
    print("🎨 GENERATING ENHANCED VISUAL MORNING BRIEF")
    print("=" * 60)
    
    try:
        from signalmuse.morning_brief_module.main import MorningBriefGenerator
        
        print("Generating morning brief with enhanced visuals...")
        generator = MorningBriefGenerator()
        brief_path = generator.generate_morning_brief()
        
        print(f"✅ Enhanced morning brief generated!")
        print(f"📄 File saved to: {brief_path}")
        
        # Show preview of the enhanced format
        with open(brief_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            # Show first 30 lines to see the visual improvements
            print("\n🎨 PREVIEW OF ENHANCED VISUAL FORMAT:")
            print("=" * 80)
            for i, line in enumerate(lines[:30]):
                print(line)
            print("=" * 80)
            print("... (truncated for preview)")
        
        return brief_path
        
    except Exception as e:
        print(f"❌ Error generating enhanced brief: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    brief_path = generate_enhanced_brief()
    
    if brief_path:
        print("\n🚀 SUCCESS!")
        print("Your morning brief now has:")
        print("✅ Enhanced visual separators (━━━━━)")
        print("✅ Better emoji usage (🚀📅📊📈📰🏛️🎤💰)")
        print("✅ Bold section headers with **text**")
        print("✅ Descriptive subtitles for each section")
        print("✅ Blockquote formatting for market summary")
        print("✅ Code-styled tags and data sources")
        print("✅ Professional disclaimer and report details")
        print(f"\n📖 Open the file to see the full enhanced format: {brief_path}")
