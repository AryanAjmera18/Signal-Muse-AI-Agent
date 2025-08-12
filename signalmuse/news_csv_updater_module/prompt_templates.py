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
    label: int  # 0 for Earning_Release, 1 for High_Impact
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
- Label 0 (Earning_Release): Company has released earnings, quarterly results, or financial performance reports
- Label 1 (High_Impact): Company has made significant business moves, acquisitions, partnerships, or market-moving announcements

SPECIAL CASES:
- If BOTH earning release AND high impact apply → use label 0
- If NEITHER applies → use label 1

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
        "label": <0_or_1>,
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
