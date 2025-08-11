#!/usr/bin/env python3
"""
Multi-Agent Financial News Analysis System

This showcases the complete SignalMuse system with:
1. Multi-source RSS scraping
2. Enhanced morning briefing generation
3. Agent orchestration
4. Individual AI processing for investor briefings

Usage: python main.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

from signalmuse.utils.utils import get_logger
from signalmuse.core.agent_orchestrator import AgentOrchestrator, OrchestrationConfig

logger = get_logger(__name__)


async def run_analysis():
    """Run the complete multi-agent system analysis"""
    print("\n" + "="*60)
    print("🤖 SignalMuse Multi-Agent Financial Analysis")
    print("="*60)
    
    try:
        # Create configuration
        config = OrchestrationConfig(
            enable_sentiment_analysis=True,
            enable_economic_calendar=False,  # Disabled - will be replaced by external calendar module
            enable_market_data=True,
            max_articles_per_source=10,
            briefing_format="unbound_x",
            save_intermediate_results=True
        )
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(config)
        
        print("🚀 Running full multi-agent analysis...")
        result = await orchestrator.run_full_analysis()
        
        if result['success']:
            print("✅ Multi-agent analysis completed successfully!")
            
            # Show summary
            summary = result['summary']
            print(f"📊 Success Rate: {summary['success_rate']:.1%}")
            print(f"📊 Successful Agents: {len(summary['successful_agents'])}/{summary['total_agents']}")
            
            # Show agent results
            for agent_name, agent_result in result['agents'].items():
                status = "✅" if agent_result.success else "❌"
                print(f"  {status} {agent_name}")
                
                if agent_result.success and hasattr(agent_result, 'data'):
                    data = agent_result.data
                    if 'articles_count' in data:
                        print(f"     📰 Articles: {data['articles_count']}")
                    if 'sources_count' in data:
                        print(f"     📡 Sources: {data['sources_count']}")
                    if 'briefing_filepath' in data:
                        print(f"     📄 Report: {data['briefing_filepath']}")
            
            return result
        else:
            print(f"❌ Multi-agent analysis failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error in analysis: {str(e)}")
        logger.exception("Analysis error details:")
        return None

# System architecture display removed - simplified demo

def show_results_summary(result):
    """Show analysis results summary"""
    if not result:
        print("\n❌ Analysis failed to complete")
        return
        
    print("\n" + "="*60)
    print("📊 ANALYSIS RESULTS")
    print("="*60)
    
    summary = result.get('summary', {})
    print(f"✅ Success Rate: {summary.get('success_rate', 0):.1%}")
    
    # Show output files
    agents = result.get('agents', {})
    for agent_name, agent_result in agents.items():
        if agent_result.success and agent_result.data:
            data = agent_result.data
            if 'filepath' in data:
                print(f"📁 {agent_name}: {data['filepath']}")
            if 'briefing_filepath' in data:
                print(f"📄 {agent_name}: {data['briefing_filepath']}")
    
    if 'final_report' in result and 'filepath' in result['final_report']:
        print(f"📋 Final Report: {result['final_report']['filepath']}")
    
    print("\n💡 Next steps:")
    print("   - Check the generated files in signalmuse/outputs/")
    print("   - Review the news data in signalmuse/data/real/")
    print("   - Customize the configuration for your needs")

async def main():
    """Main analysis function"""
    
    
    try:
        # Run the complete multi-agent analysis
        result = await run_analysis()
        
        # Show results summary
        show_results_summary(result)
        
        print("\n🎉 Analysis completed!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        logger.exception("Analysis failure details:")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        sys.exit(1) 