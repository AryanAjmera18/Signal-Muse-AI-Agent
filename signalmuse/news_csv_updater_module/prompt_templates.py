#!/usr/bin/env python3
"""
Prompt Templates for News Classification

Contains structured prompts for LLM-based news classification and ticker extraction.
"""

from typing import List, Dict
from pydantic import BaseModel

class NewsClassificationResponse(BaseModel):
    """Pydantic model for structured LLM response"""
    news_id: int
    label: int  # 0=NONE, 1=EARNINGS, 2=IMPACT, 3=BOTH
    ticker: str

class NewsClassificationPrompt:
    """Handles prompt templates for news classification"""
    
    @staticmethod
    def create_classification_prompt(articles_chunk: List[Dict]) -> str:
        """
        Create classification prompt for a chunk of articles
        
        Args:
            articles_chunk: List of dictionaries with title, summary, and id
            
        Returns:
            Formatted prompt string
        """
        
        # Format articles for the prompt
        articles_text = ""
        for i, article in enumerate(articles_chunk, 1):
            articles_text += f"""
Article {i}:
- ID: {article['id']}
- Title: {article['title']}
- Summary: {article['summary']}

"""
        
        prompt = f"""You are a financial news analyst. Your task is to classify news articles and extract company tickers.

CLASSIFICATION RULES:
- Label 0 (NONE): Neither earnings release nor high impact news - routine market updates, general economic news
- Label 1 (EARNINGS): Company has released earnings, quarterly results, or financial performance reports
- Label 2 (IMPACT): Company has made significant business moves, acquisitions, partnerships, or market-moving announcements
- Label 3 (BOTH): Both earnings-related AND high impact (e.g., major earnings surprise with significant market implications)

CLASSIFICATION GUIDELINES:
- Earnings releases include: quarterly reports, earnings calls, financial results, revenue announcements
- High impact news includes: major acquisitions, regulatory changes, CEO changes, significant product launches, major partnerships
- If an article mentions earnings but is routine/expected, it's still Label 1
- If an article is about market movements without specific company news, it's Label 0
- Label 3 should be reserved for truly significant earnings news that will have major market impact

TICKER EXTRACTION:
- Extract the primary company's stock ticker symbol (e.g., AAPL, TSLA, MSFT)
- Use "N/A" if no clear ticker can be identified
- Focus on the main company in the spotlight

NEWS ARTICLES TO ANALYZE:
{articles_text}

RESPONSE FORMAT:
Return a JSON array with this exact structure for each article:
[
    {{
        "news_id": <article_id>,
        "label": <0_1_2_or_3>,
        "ticker": "<TICKER_OR_NA>"
    }}
]

Analyze each article carefully and provide the classification and ticker extraction."""
        
        return prompt
    
    @staticmethod
    def get_system_message() -> str:
        """Get system message for consistent LLM behavior"""
        return """You are a precise financial news analyst. Always respond with valid JSON arrays only. 
Do not include any explanations, markdown formatting, or additional text outside the JSON response."""
