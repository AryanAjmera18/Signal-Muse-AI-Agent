#!/usr/bin/env python3
"""
Multi-Agent Financial News Analysis System Demo

This demo showcases the complete SignalMuse system with:
1. Multi-source RSS scraping
2. FinBERT sentiment analysis API
3. Enhanced morning briefing generation
4. Agent orchestration
5. UnBound X format reports

Usage: python demo_multi_agent_system.py
"""

import asyncio
import sys
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_banner():
    """Print system banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SignalMuse Multi-Agent Financial System                    ║
║                                                                              ║
║  📰 Agent 1: News Collection & Sentiment Analysis                           ║
║  📅 Agent 2: Economic Calendar & Events                                     ║
║  📊 Agent 3: Market Data & Futures                                          ║
║  📝 Agent 4: Report Generation & Synthesis                                  ║
║                                                                              ║
║  Powered by: RSS Feeds | FinBERT | Groq LLM | UnBound X Format             ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking system dependencies...")
    
    required_modules = [
        'pandas', 'requests', 'feedparser', 'transformers', 
        'torch', 'fastapi', 'uvicorn', 'asyncio'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module} - Missing")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing dependencies: {', '.join(missing_modules)}")
        print("Please install missing dependencies:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available!")
    return True

async def demo_multi_source_scraper():
    """Demo the multi-source RSS scraper"""
    print("\n" + "="*60)
    print("📡 DEMO 1: Multi-Source RSS Scraper")
    print("="*60)
    
    try:
        from signalmuse.scrapers.multi_source_scraper import MultiSourceScraper
        
        scraper = MultiSourceScraper()
        
        print("🔍 Available RSS feeds:")
        for feed_id, feed in scraper.feeds.items():
            status = "✅" if feed.enabled else "❌"
            print(f"  {status} {feed.name} ({feed.category})")
        
        print("\n📡 Fetching news from all sources...")
        df = scraper.fetch_all_feeds(max_articles_per_feed=5)
        
        if not df.empty:
            print(f"✅ Successfully fetched {len(df)} articles from {df['source'].nunique()} sources")
            
            # Show summary by category
            print("\n📊 Articles by Category:")
            category_counts = df['category'].value_counts()
            for category, count in category_counts.items():
                print(f"  {category}: {count} articles")
            
            # Save to CSV
            filepath = scraper.save_to_csv(df)
            print(f"\n💾 Data saved to: {filepath}")
            
            # Show sample articles
            print("\n📰 Sample Articles:")
            for _, row in df.head(3).iterrows():
                print(f"  {row['source']}: {row['title'][:60]}...")
            
            return filepath
        else:
            print("❌ No articles fetched")
            return None
            
    except Exception as e:
        print(f"❌ Error in multi-source scraper demo: {str(e)}")
        return None

async def demo_finbert_api():
    """Demo the FinBERT sentiment analysis API"""
    print("\n" + "="*60)
    print("🧠 DEMO 2: FinBERT Sentiment Analysis API")
    print("="*60)
    
    try:
        import requests
        
        # Test if FinBERT API is running
        api_url = "http://localhost:8000"
        
        try:
            response = requests.get(f"{api_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ FinBERT API is running")
                
                # Test sentiment analysis
                test_texts = [
                    "Fed raises interest rates by 25 basis points",
                    "Apple reports strong quarterly earnings",
                    "Market volatility increases amid economic uncertainty"
                ]
                
                payload = {
                    'texts': test_texts,
                    'sources': ['Reuters', 'Bloomberg', 'CNBC'],
                    'categories': ['macro', 'earnings', 'market']
                }
                
                response = requests.post(f"{api_url}/classify/batch", json=payload, timeout=10)
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"✅ Processed {results['total_processed']} texts in {results['processing_time']}s")
                    
                    for i, result in enumerate(results['results']):
                        print(f"  Text {i+1}: {result['sentiment']} (confidence: {result['confidence']:.3f})")
                    
                    return True
                else:
                    print(f"❌ API error: {response.status_code}")
                    return False
            else:
                print("❌ FinBERT API not responding correctly")
                return False
                
        except requests.exceptions.ConnectionError:
            print("⚠️  FinBERT API not running (expected for demo)")
            print("   To start: python signalmuse/apis/finbert_api.py")
            return False
            
    except Exception as e:
        print(f"❌ Error in FinBERT API demo: {str(e)}")
        return False

async def demo_enhanced_briefing():
    """Demo the enhanced briefing generator"""
    print("\n" + "="*60)
    print("📝 DEMO 3: Enhanced Morning Briefing Generator")
    print("="*60)
    
    try:
        from signalmuse.outputs.enhanced_briefing_generator import EnhancedBriefingGenerator
        
        generator = EnhancedBriefingGenerator()
        
        # Use sample data if available
        sample_csv = "signalmuse/data/real/googl_news_20250731_224935.csv"
        
        if Path(sample_csv).exists():
            print(f"📊 Generating briefing from: {sample_csv}")
            briefing = generator.generate_briefing(sample_csv, "GOOGL")
            
            # Save briefing
            filepath = generator.save_briefing(briefing)
            print(f"✅ Briefing saved to: {filepath}")
            
            # Show preview
            print("\n📰 Briefing Preview:")
            lines = briefing.split('\n')[:20]
            for line in lines:
                print(f"  {line}")
            print("  ...")
            
            return filepath
        else:
            print("⚠️  No sample data available")
            print("   Run the multi-source scraper first to generate data")
            return None
            
    except Exception as e:
        print(f"❌ Error in enhanced briefing demo: {str(e)}")
        return None

async def demo_agent_orchestrator():
    """Demo the agent orchestrator"""
    print("\n" + "="*60)
    print("🤖 DEMO 4: Agent Orchestrator")
    print("="*60)
    
    try:
        from signalmuse.core.agent_orchestrator import AgentOrchestrator, OrchestrationConfig
        
        # Create configuration
        config = OrchestrationConfig(
            enable_sentiment_analysis=True,
            enable_economic_calendar=True,
            enable_market_data=True,
            enable_finbert_api=False,  # Disable for demo
            max_articles_per_source=5,
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
        print(f"❌ Error in agent orchestrator demo: {str(e)}")
        return None

def show_system_architecture():
    """Show the system architecture"""
    print("\n" + "="*60)
    print("🏗️  SYSTEM ARCHITECTURE")
    print("="*60)
    
    architecture = """
📡 Data Sources:
├── Reuters Business RSS
├── MarketWatch Top Stories
├── CNBC World News
├── The Motley Fool
├── CoinDesk (Crypto)
├── Cointelegraph (Crypto)
└── 10+ additional sources

🤖 Agent Pipeline:
├── Agent 1: News Collection & Sentiment Analysis
│   ├── Multi-source RSS scraping
│   ├── FinBERT sentiment analysis
│   └── Data preprocessing
├── Agent 2: Economic Calendar & Events
│   ├── FMP API integration
│   ├── Economic calendar
│   └── Earnings calendar
├── Agent 3: Market Data & Futures
│   ├── Market futures data
│   ├── Commodity prices
│   └── Volatility indices
└── Agent 4: Report Generation & Synthesis
    ├── UnBound X format
    ├── Strategic insights
    └── Risk monitoring

📊 Output Formats:
├── Morning Briefing (UnBound X)
├── Detailed Analysis
├── CSV data exports
└── JSON orchestration reports
    """
    
    print(architecture)

def show_usage_instructions():
    """Show usage instructions"""
    print("\n" + "="*60)
    print("📖 USAGE INSTRUCTIONS")
    print("="*60)
    
    instructions = """
🚀 Quick Start:
1. Install dependencies: pip install -r requirements.txt
2. Set up environment variables: cp env.template .env
3. Run demo: python demo_multi_agent_system.py

🔧 Individual Components:
├── Multi-source scraper: python signalmuse/scrapers/multi_source_scraper.py
├── FinBERT API: python signalmuse/apis/finbert_api.py
├── Enhanced briefing: python signalmuse/outputs/enhanced_briefing_generator.py
└── Agent orchestrator: python signalmuse/core/agent_orchestrator.py

📊 API Endpoints (when FinBERT API is running):
├── GET  / - Health check
├── POST /classify - Single text sentiment
├── POST /classify/batch - Batch sentiment analysis
└── GET  /model/info - Model information

🔑 Required API Keys:
├── GROQ_API_KEY - For LLM report generation
├── FMP_API_KEY - For economic/market data (optional)
└── No key required for RSS scraping

📁 Output Files:
├── signalmuse/data/real/ - CSV news data
├── signalmuse/outputs/ - Markdown reports
└── signalmuse/outputs/ - JSON orchestration reports
    """
    
    print(instructions)

async def main():
    """Main demo function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        return
    
    # Show system architecture
    show_system_architecture()
    
    # Run demos
    demos = [
        ("Multi-Source RSS Scraper", demo_multi_source_scraper),
        ("FinBERT Sentiment Analysis", demo_finbert_api),
        ("Enhanced Briefing Generator", demo_enhanced_briefing),
        ("Agent Orchestrator", demo_agent_orchestrator)
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        try:
            result = await demo_func()
            results[demo_name] = result
        except Exception as e:
            print(f"❌ {demo_name} failed: {str(e)}")
            results[demo_name] = None
    
    # Show summary
    print("\n" + "="*60)
    print("📊 DEMO SUMMARY")
    print("="*60)
    
    successful_demos = sum(1 for result in results.values() if result is not None)
    total_demos = len(demos)
    
    print(f"✅ Successful demos: {successful_demos}/{total_demos}")
    
    for demo_name, result in results.items():
        status = "✅" if result is not None else "❌"
        print(f"  {status} {demo_name}")
    
    # Show usage instructions
    show_usage_instructions()
    
    print("\n🎉 Demo completed! Check the generated files in signalmuse/outputs/")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        sys.exit(1) 