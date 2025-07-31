#!/usr/bin/env python3
"""
Agent Orchestrator

Coordinates the multi-agent system for financial news analysis:
- Agent 1: News Collection & Sentiment Analysis
- Agent 2: Economic Calendar & Events
- Agent 3: Market Data & Futures
- Agent 4: Report Generation & Synthesis
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import json
import requests
from dataclasses import dataclass, asdict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentResult:
    """Result from an agent execution"""
    agent_name: str
    success: bool
    data: Dict
    timestamp: str
    error: Optional[str] = None

@dataclass
class OrchestrationConfig:
    """Configuration for agent orchestration"""
    enable_sentiment_analysis: bool = True
    enable_economic_calendar: bool = True
    enable_market_data: bool = True
    enable_finbert_api: bool = True
    max_articles_per_source: int = 20
    briefing_format: str = "unbound_x"  # "unbound_x" or "detailed"
    save_intermediate_results: bool = True

class AgentOrchestrator:
    """Orchestrates the multi-agent financial news analysis system"""
    
    def __init__(self, config: OrchestrationConfig = None):
        self.config = config or OrchestrationConfig()
        self.results = {}
        self.finbert_api_url = "http://localhost:8000" if self.config.enable_finbert_api else None
        
    async def run_full_analysis(self, ticker: str = None, category: str = None) -> Dict:
        """Run the complete multi-agent analysis pipeline"""
        logger.info("🚀 Starting multi-agent financial analysis pipeline")
        
        try:
            # Agent 1: News Collection & Sentiment Analysis
            agent1_result = await self._run_agent1(ticker, category)
            self.results['agent1'] = agent1_result
            
            if not agent1_result.success:
                logger.error(f"Agent 1 failed: {agent1_result.error}")
                return self._create_error_response("Agent 1 failed")
            
            # Agent 2: Economic Calendar & Events
            agent2_result = await self._run_agent2()
            self.results['agent2'] = agent2_result
            
            # Agent 3: Market Data & Futures
            agent3_result = await self._run_agent3()
            self.results['agent3'] = agent3_result
            
            # Agent 4: Report Generation & Synthesis
            agent4_result = await self._run_agent4()
            self.results['agent4'] = agent4_result
            
            # Generate final report
            final_report = await self._generate_final_report()
            
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'agents': self.results,
                'final_report': final_report,
                'summary': self._create_summary()
            }
            
        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}")
            return self._create_error_response(f"Orchestration error: {str(e)}")
    
    async def _run_agent1(self, ticker: str = None, category: str = None) -> AgentResult:
        """Agent 1: News Collection & Sentiment Analysis"""
        logger.info("📰 Agent 1: Collecting news and performing sentiment analysis")
        
        try:
            # Import the multi-source scraper
            from signalmuse.scrapers.multi_source_scraper import MultiSourceScraper
            
            scraper = MultiSourceScraper()
            
            # Fetch news data
            if category:
                df = scraper.fetch_by_category(category, max_articles=100)
            else:
                df = scraper.fetch_all_feeds(max_articles_per_feed=self.config.max_articles_per_source)
            
            if df.empty:
                return AgentResult(
                    agent_name="Agent1_NewsCollection",
                    success=False,
                    data={},
                    timestamp=datetime.now().isoformat(),
                    error="No news articles fetched"
                )
            
            # Perform sentiment analysis if enabled
            if self.config.enable_sentiment_analysis:
                df = await self._add_sentiment_analysis(df)
            
            # Save intermediate results
            if self.config.save_intermediate_results:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"agent1_news_{timestamp}.csv"
                filepath = scraper.save_to_csv(df, filename)
            else:
                filepath = scraper.save_to_csv(df)
            
            # Calculate summary statistics (handle missing columns)
            articles_count = len(df)
            
            # Handle source/publisher column mapping
            if 'source' in df.columns:
                sources_count = df['source'].nunique()
            elif 'publisher' in df.columns:
                sources_count = df['publisher'].nunique()
                # Add source column for compatibility
                df['source'] = df['publisher']
            else:
                sources_count = 0
            
            # Handle categories if available
            categories = {}
            if 'category' in df.columns:
                categories = df['category'].value_counts().to_dict()
            
            return AgentResult(
                agent_name="Agent1_NewsCollection",
                success=True,
                data={
                    'articles_count': articles_count,
                    'sources_count': sources_count,
                    'categories': categories,
                    'filepath': filepath,
                    'sample_articles': df.head(5).to_dict('records')
                },
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Agent 1 error: {str(e)}")
            return AgentResult(
                agent_name="Agent1_NewsCollection",
                success=False,
                data={},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
    
    async def _run_agent2(self) -> AgentResult:
        """Agent 2: Economic Calendar & Events"""
        logger.info("📅 Agent 2: Fetching economic calendar and events")
        
        try:
            # Import the enhanced briefing generator for economic data
            from signalmuse.outputs.enhanced_briefing_generator import EnhancedBriefingGenerator
            
            generator = EnhancedBriefingGenerator()
            
            # Fetch economic calendar
            economic_events = generator.fetch_economic_calendar()
            earnings_events = generator.fetch_earnings_calendar()
            
            return AgentResult(
                agent_name="Agent2_EconomicCalendar",
                success=True,
                data={
                    'economic_events': [asdict(event) for event in economic_events],
                    'earnings_events': [asdict(event) for event in earnings_events],
                    'economic_count': len(economic_events),
                    'earnings_count': len(earnings_events)
                },
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Agent 2 error: {str(e)}")
            return AgentResult(
                agent_name="Agent2_EconomicCalendar",
                success=False,
                data={},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
    
    async def _run_agent3(self) -> AgentResult:
        """Agent 3: Market Data & Futures"""
        logger.info("📊 Agent 3: Fetching market data and futures")
        
        try:
            # Import the enhanced briefing generator for market data
            from signalmuse.outputs.enhanced_briefing_generator import EnhancedBriefingGenerator
            
            generator = EnhancedBriefingGenerator()
            
            # Fetch market futures data
            market_data = generator.fetch_market_futures()
            
            return AgentResult(
                agent_name="Agent3_MarketData",
                success=True,
                data={
                    'market_data': asdict(market_data),
                    'futures_summary': {
                        'sp500_change': market_data.sp500_futures,
                        'nasdaq_change': market_data.nasdaq_futures,
                        'russell_change': market_data.russell_futures,
                        'crude_oil': market_data.crude_oil,
                        'treasury_yield': market_data.treasury_yield,
                        'vix': market_data.vix,
                        'sentiment': market_data.sentiment
                    }
                },
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Agent 3 error: {str(e)}")
            return AgentResult(
                agent_name="Agent3_MarketData",
                success=False,
                data={},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
    
    async def _run_agent4(self) -> AgentResult:
        """Agent 4: Report Generation & Synthesis"""
        logger.info("📝 Agent 4: Generating comprehensive report")
        
        try:
            # Get the news data filepath from Agent 1
            agent1_result = self.results.get('agent1')
            if not agent1_result or not agent1_result.success:
                return AgentResult(
                    agent_name="Agent4_ReportGeneration",
                    success=False,
                    data={},
                    timestamp=datetime.now().isoformat(),
                    error="Agent 1 failed or not available"
                )
            
            news_filepath = agent1_result.data.get('filepath')
            
            if not news_filepath or not Path(news_filepath).exists():
                return AgentResult(
                    agent_name="Agent4_ReportGeneration",
                    success=False,
                    data={},
                    timestamp=datetime.now().isoformat(),
                    error="News data file not found"
                )
            
            # Import the enhanced briefing generator
            from signalmuse.outputs.enhanced_briefing_generator import EnhancedBriefingGenerator
            
            generator = EnhancedBriefingGenerator()
            
            # Generate briefing
            briefing = generator.generate_briefing(news_filepath)
            
            # Save briefing
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"orchestrated_briefing_{timestamp}.md"
            filepath = generator.save_briefing(briefing, filename)
            
            return AgentResult(
                agent_name="Agent4_ReportGeneration",
                success=True,
                data={
                    'briefing_filepath': filepath,
                    'briefing_length': len(briefing),
                    'format': self.config.briefing_format
                },
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Agent 4 error: {str(e)}")
            return AgentResult(
                agent_name="Agent4_ReportGeneration",
                success=False,
                data={},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
    
    async def _add_sentiment_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add sentiment analysis to the DataFrame"""
        if not self.finbert_api_url:
            logger.warning("FinBERT API not available, skipping sentiment analysis")
            return df
        
        try:
            # Prepare texts for batch analysis
            texts = df['title'].tolist()
            
            # Handle optional columns with publisher/source mapping
            if 'source' in df.columns:
                sources = df['source'].tolist()
            elif 'publisher' in df.columns:
                sources = df['publisher'].tolist()
            else:
                sources = ['Unknown'] * len(texts)
            
            categories = df['category'].tolist() if 'category' in df.columns else ['general'] * len(texts)
            
            # Call FinBERT API
            payload = {
                'texts': texts,
                'sources': sources,
                'categories': categories
            }
            
            response = requests.post(
                f"{self.finbert_api_url}/classify/batch",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            results = response.json()['results']
            
            # Add sentiment data to DataFrame
            df['sentiment'] = [r['sentiment'] for r in results]
            df['sentiment_confidence'] = [r['confidence'] for r in results]
            
            logger.info(f"Added sentiment analysis to {len(df)} articles")
            return df
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            # Return DataFrame without sentiment analysis
            return df
    
    async def _generate_final_report(self) -> Dict:
        """Generate final comprehensive report"""
        try:
            # Combine all agent results
            report = {
                'execution_summary': {
                    'total_agents': len(self.results),
                    'successful_agents': sum(1 for r in self.results.values() if r.success),
                    'timestamp': datetime.now().isoformat()
                },
                'agent_results': {
                    name: {
                        'success': result.success,
                        'data': result.data,
                        'timestamp': result.timestamp,
                        'error': result.error
                    }
                    for name, result in self.results.items()
                }
            }
            
            # Save final report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filepath = f"signalmuse/outputs/orchestration_report_{timestamp}.json"
            
            with open(report_filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            report['filepath'] = report_filepath
            return report
            
        except Exception as e:
            logger.error(f"Final report generation error: {str(e)}")
            return {'error': str(e)}
    
    def _create_summary(self) -> Dict:
        """Create a summary of the orchestration results"""
        successful_agents = [name for name, result in self.results.items() if result.success]
        failed_agents = [name for name, result in self.results.items() if not result.success]
        
        return {
            'total_agents': len(self.results),
            'successful_agents': successful_agents,
            'failed_agents': failed_agents,
            'success_rate': len(successful_agents) / len(self.results) if self.results else 0
        }
    
    def _create_error_response(self, error: str) -> Dict:
        """Create error response"""
        return {
            'success': False,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'agents': self.results
        }

async def main():
    """Test the agent orchestrator"""
    print("🔍 Agent Orchestrator Test")
    print("=" * 50)
    
    # Create configuration
    config = OrchestrationConfig(
        enable_sentiment_analysis=True,
        enable_economic_calendar=True,
        enable_market_data=True,
        enable_finbert_api=False,  # Set to False for testing without FinBERT API
        max_articles_per_source=10,
        briefing_format="unbound_x",
        save_intermediate_results=True
    )
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(config)
    
    # Run full analysis
    print("\n🚀 Running full multi-agent analysis...")
    result = await orchestrator.run_full_analysis()
    
    if result['success']:
        print("✅ Analysis completed successfully!")
        print(f"📊 Summary: {result['summary']}")
        
        # Show agent results
        for agent_name, agent_result in result['agents'].items():
            status = "✅" if agent_result.success else "❌"
            print(f"{status} {agent_name}: {'Success' if agent_result.success else 'Failed'}")
            
            if agent_result.success and 'data' in agent_result:
                data = agent_result.data
                if 'articles_count' in data:
                    print(f"   📰 Articles: {data['articles_count']}")
                if 'sources_count' in data:
                    print(f"   📡 Sources: {data['sources_count']}")
                if 'briefing_filepath' in data:
                    print(f"   📄 Report: {data['briefing_filepath']}")
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main()) 