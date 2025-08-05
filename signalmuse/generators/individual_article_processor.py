#!/usr/bin/env python3
"""
Individual Article Processor for Investor Briefings

Processes individual articles with AI analysis using Groq API to generate
the specific format requested for investor briefings.
"""

import pandas as pd
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel
import instructor
from groq import Groq

from signalmuse.utils.utils import get_logger, config

logger = get_logger(__name__)

class ArticleAnalysis(BaseModel):
    """Pydantic model for article analysis response"""
    company_name: str
    ticker: str
    impact_assessment: str  # High/Medium/Low impact with reasoning
    detailed_summary: str   # AI-generated detailed summary
    confidence: float

@dataclass
class ProcessedArticle:
    """Processed article for investor briefing"""
    title: str
    company: str
    ticker: str
    impact: str
    detailed_summary: str
    source: str
    link: str
    published_at: datetime
    relevance_score: float

class IndividualArticleProcessor:
    """Processor for individual article AI analysis"""
    
    def __init__(self):
        self.groq_api_key = config.groq_api_key
        self.groq_client = self._setup_groq_client() if self.groq_api_key else None
        
        # Common tickers for company identification
        self.common_tickers = {
            'AAPL': 'Apple', 'MSFT': 'Microsoft', 'GOOGL': 'Alphabet', 'AMZN': 'Amazon',
            'TSLA': 'Tesla', 'META': 'Meta', 'NVDA': 'NVIDIA', 'NFLX': 'Netflix',
            'PLTR': 'Palantir', 'AMD': 'Advanced Micro Devices', 'INTC': 'Intel',
            'CRM': 'Salesforce', 'ORCL': 'Oracle', 'ADBE': 'Adobe', 'PYPL': 'PayPal',
            'UBER': 'Uber', 'LYFT': 'Lyft', 'SNAP': 'Snap', 'COIN': 'Coinbase',
            'HOOD': 'Robinhood', 'RIVN': 'Rivian', 'JPM': 'JPMorgan', 'BAC': 'Bank of America',
            'WFC': 'Wells Fargo', 'GS': 'Goldman Sachs', 'MS': 'Morgan Stanley',
            'JNJ': 'Johnson & Johnson', 'PFE': 'Pfizer', 'UNH': 'UnitedHealth',
            'WMT': 'Walmart', 'COST': 'Costco', 'HD': 'Home Depot', 'DIS': 'Disney',
            'V': 'Visa', 'MA': 'Mastercard', 'BRK-A': 'Berkshire Hathaway'
        }

    def _setup_groq_client(self):
        """Initialize Groq client for article analysis"""
        if not self.groq_api_key:
            logger.warning("Groq API key not found")
            return None
        try:
            return instructor.from_groq(Groq(api_key=self.groq_api_key))
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            return None

    async def process_article(self, article: Dict) -> ProcessedArticle:
        """Process individual article with AI analysis"""
        
        if not self.groq_client:
            logger.warning("Groq client not available, using fallback processing")
            return self._fallback_processing(article)
        
        try:
            # Create comprehensive prompt for article analysis
            ticker_list = ", ".join([f"{ticker} ({name})" for ticker, name in list(self.common_tickers.items())[:30]])
            
            prompt = f"""
            Analyze this financial news article for an investor briefing. Provide comprehensive analysis.
            
            ARTICLE DETAILS:
            Title: {article['title']}
            Summary: {article.get('summary', 'No summary available')}
            Source: {article.get('source', 'Unknown')}
            Category: {article.get('category', 'general')}
            Published: {article.get('published', 'Unknown')}
            
            KNOWN COMPANIES/TICKERS:
            {ticker_list}
            
            ANALYSIS REQUIREMENTS:
            1. COMPANY IDENTIFICATION: Identify the primary company and ticker symbol mentioned
            2. IMPACT ASSESSMENT: Assess market impact (High/Medium/Low) with specific reasoning
            3. DETAILED SUMMARY: Create an investor-focused summary (2-3 paragraphs) that explains:
               - What happened and why it matters to investors
               - Potential financial implications
               - Key metrics, numbers, or strategic significance
               - Context for investment decisions
            
            RULES:
            - If multiple companies mentioned, focus on the PRIMARY subject
            - If no specific company, use "Market General" and "N/A" for ticker
            - Impact should include WHY (reasoning), not just level
            - Summary should be substantive and investor-focused
            - Be specific about financial implications when possible
            - Confidence should reflect certainty of company identification (0.0-1.0)
            """
            
            # Get AI analysis
            analysis = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",  # Use larger model for better analysis
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert financial analyst creating investor briefings. Provide detailed, actionable analysis for sophisticated investors."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_model=ArticleAnalysis,
                max_tokens=1000,
                temperature=0.3  # Lower temperature for more focused analysis
            )
            
            # Calculate relevance score based on various factors
            relevance_score = self._calculate_relevance_score(article, analysis)
            
            return ProcessedArticle(
                title=article['title'],
                company=f"{analysis.company_name} ({analysis.ticker})" if analysis.ticker != "N/A" else analysis.company_name,
                ticker=analysis.ticker,
                impact=analysis.impact_assessment,
                detailed_summary=analysis.detailed_summary,
                source=article.get('source', 'Unknown'),
                link=article.get('link', ''),
                published_at=pd.to_datetime(article.get('published', datetime.now())),
                relevance_score=relevance_score
            )
            
        except Exception as e:
            logger.error(f"Error processing article '{article.get('title', 'Unknown')}': {e}")
            return self._fallback_processing(article)

    def _calculate_relevance_score(self, article: Dict, analysis: ArticleAnalysis) -> float:
        """Calculate relevance score for article prioritization"""
        score = 0.0
        
        # Base score from AI confidence
        score += analysis.confidence * 0.3
        
        # Impact assessment scoring
        impact_lower = analysis.impact_assessment.lower()
        if 'high' in impact_lower:
            score += 0.4
        elif 'medium' in impact_lower:
            score += 0.2
        elif 'low' in impact_lower:
            score += 0.1
        
        # Source priority scoring
        high_priority_sources = ['Bloomberg', 'CNBC', 'MarketWatch', 'Seeking Alpha']
        source = article.get('source', '')
        if any(priority_source in source for priority_source in high_priority_sources):
            score += 0.2
        
        # Recency scoring (articles from today get higher scores)
        try:
            pub_date = pd.to_datetime(article.get('published', datetime.now()))
            hours_old = (datetime.now() - pub_date.replace(tzinfo=None)).total_seconds() / 3600
            if hours_old < 6:  # Last 6 hours
                score += 0.1
            elif hours_old < 24:  # Last 24 hours
                score += 0.05
        except:
            pass
        
        return min(score, 1.0)  # Cap at 1.0

    def _fallback_processing(self, article: Dict) -> ProcessedArticle:
        """Fallback processing when AI is not available"""
        
        # Simple ticker extraction from title
        title = article.get('title', '')
        company = "Market General"
        ticker = "N/A"
        
        # Basic pattern matching for common companies
        for tick, name in self.common_tickers.items():
            if tick in title.upper() or name.lower() in title.lower():
                company = f"{name} ({tick})"
                ticker = tick
                break
        
        return ProcessedArticle(
            title=article['title'],
            company=company,
            ticker=ticker,
            impact="Medium - Unable to perform detailed analysis",
            detailed_summary=article.get('summary', 'No summary available'),
            source=article.get('source', 'Unknown'),
            link=article.get('link', ''),
            published_at=pd.to_datetime(article.get('published', datetime.now())),
            relevance_score=0.5  # Default score when AI unavailable
        )

    async def process_top_articles(self, articles_df: pd.DataFrame, num_articles: int = 5) -> List[ProcessedArticle]:
        """Process top articles for investor briefing with rate limit optimization"""
        
        logger.info(f"Processing top {num_articles} articles for investor briefing")
        
        # Sort by publication date to prioritize latest news
        articles_df = articles_df.sort_values('published', ascending=False)
        
        # Convert top articles to dict format for processing
        top_articles = articles_df.head(20).to_dict('records')  # Process more to get best 5
        
        # Process articles individually with AI (with rate limit handling)
        processed_articles = []
        for i, article in enumerate(top_articles):
            try:
                # Add delay between requests to be API-friendly and avoid rate limits
                if i > 0:
                    await asyncio.sleep(5)  # 5 second delay between requests
                
                processed = await self.process_article(article)
                processed_articles.append(processed)
                logger.info(f"Processed: {processed.title[:60]}... | Relevance: {processed.relevance_score:.2f}")
                
                # Stop early if we have enough high-quality articles
                if len(processed_articles) >= num_articles * 2:  # Get 2x to ensure good selection
                    break
                    
            except Exception as e:
                logger.error(f"Failed to process article: {e}")
                continue
        
        # Sort by relevance score and return top N
        processed_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Selected top {num_articles} articles based on relevance scoring")
        return processed_articles[:num_articles]

    def generate_investor_briefing_format(self, articles: List[ProcessedArticle], market_data=None) -> str:
        """Generate briefing in the specific format requested with market data"""
        
        briefing_sections = []
        
        # Add market data section if available
        if market_data:
            market_section = f"""## Market Futures Overview

**Pre-Market Sentiment:** {market_data.get('sentiment', 'Neutral')}

- **S&P 500 futures:** {market_data.get('sp500_change', 0.0):+.2f}%
- **Nasdaq futures:** {market_data.get('nasdaq_change', 0.0):+.2f}%
- **Russell 2000 futures:** {market_data.get('russell_change', 0.0):+.2f}%
- **Crude Oil (WTI):** ${market_data.get('crude_oil', 75.0):.2f}
- **10Y Treasury Yield:** {market_data.get('treasury_yield', 4.2):.2f}%
- **VIX:** {market_data.get('vix', 15.0):.1f}

---

## Current Market Data

**Current Index Levels:**

- **S&P 500:** {market_data.get('sp500_current', 0.0):.2f}
- **Nasdaq Composite:** {market_data.get('nasdaq_current', 0.0):.2f}
- **Russell 2000:** {market_data.get('russell_current', 0.0):.2f}

---

## Top Market News"""
            briefing_sections.append(market_section)
        
        for article in articles:
            section = f"""### {article.title}

**Company:** {article.company} | **Impact:** {article.impact}

{article.detailed_summary}

*Source: {article.source}*  
**📰 [Read Full Article]({article.link})**"""
            
            briefing_sections.append(section)
        
        # Combine all sections
        full_briefing = "\n\n".join(briefing_sections)
        
        # Add header
        current_date = datetime.now().strftime("%B %d, %Y")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""# UnBound X Morning Market Briefing

**📅 Date:** {current_date}

**Generated:** {timestamp}  
**Top {len(articles)} Articles with Individual AI Analysis**

---

"""
        
        # Add footer
        footer = f"""

---

## Compliance Disclosure

*This briefing is provided for informational purposes only and does not constitute investment advice, recommendations, or offers to buy or sell securities. All data sourced from public markets and third-party providers. UnBound X users should conduct their own research and consult with qualified professionals before making investment decisions.*"""
        
        return header + full_briefing + footer

async def main():
    """Test the individual article processor"""
    print("🔍 Testing Individual Article Processor")
    print("=" * 50)
    
    # Load latest scraped data
    from signalmuse.scrapers.multi_source_scraper import MultiSourceScraper
    
    scraper = MultiSourceScraper()
    df = scraper.fetch_all_feeds(max_articles_per_feed=10)
    
    if df.empty:
        print("❌ No articles to process")
        return
    
    print(f"📊 Processing {len(df)} articles")
    
    # Initialize processor
    processor = IndividualArticleProcessor()
    
    # Process top articles
    processed_articles = await processor.process_top_articles(df, num_articles=5)
    
    # Generate briefing
    briefing = processor.generate_investor_briefing_format(processed_articles)
    
    print("✅ Generated investor briefing with individual AI analysis")
    print(f"📄 Briefing length: {len(briefing)} characters")
    
    # Save briefing
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"individual_ai_briefing_{timestamp}.md"
    filepath = config.output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(briefing)
    
    print(f"💾 Saved to: {filepath}")
    
    # Show sample
    print("\n📰 Sample Output:")
    print(briefing[:500] + "..." if len(briefing) > 500 else briefing)

if __name__ == "__main__":
    asyncio.run(main())