#!/usr/bin/env python3
"""
Chunk Processor

Handles chunking of CSV data and processing through LLM for classification.
"""

import json
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pydantic import ValidationError

from ..utils.utils import get_logger
from .groq_client import GroqClientManager
from .prompt_templates import NewsClassificationPrompt, NewsClassificationResponse

logger = get_logger(__name__)

class ChunkProcessor:
    """Processes chunks of news articles through LLM for classification"""
    
    def __init__(self, groq_manager: GroqClientManager):
        self.groq_manager = groq_manager
        self.prompt_template = NewsClassificationPrompt()
    
    def create_chunks(self, df: pd.DataFrame, chunk_size: int = 10) -> List[pd.DataFrame]:
        """
        Split DataFrame into chunks of specified size
        
        Args:
            df: Input DataFrame
            chunk_size: Number of rows per chunk
            
        Returns:
            List of DataFrame chunks
        """
        chunks = []
        total_rows = len(df)
        
        for i in range(0, total_rows, chunk_size):
            chunk = df.iloc[i:i + chunk_size].copy()
            chunks.append(chunk)
            logger.debug(f"Created chunk {len(chunks)} with {len(chunk)} articles")
        
        logger.debug(f"Total chunks created: {len(chunks)}")
        return chunks
    
    def extract_article_fields(self, chunk_df: pd.DataFrame) -> List[Dict]:
        """
        Extract only required fields (title, summary, id) from chunk
        
        Args:
            chunk_df: DataFrame chunk
            
        Returns:
            List of dictionaries with extracted fields
        """
        articles = []
        
        for _, row in chunk_df.iterrows():
            article = {
                'id': row['id'],
                'title': row['title'],
                'summary': row['summary'] if pd.notna(row['summary']) else "No summary available"
            }
            articles.append(article)
        
        return articles
    
    def process_chunk_with_llm(self, articles: List[Dict]) -> Optional[List[Dict]]:
        """
        Process chunk through LLM for classification and ticker extraction
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of classification results or None if failed
        """
        if not self.groq_manager.is_available():
            logger.error("Groq client not available")
            return None
        
        try:
            # Enforce rate limiting
            self.groq_manager.enforce_rate_limit()
            
            # Create prompt
            prompt = self.prompt_template.create_classification_prompt(articles)
            system_message = self.prompt_template.get_system_message()
            
            # Call LLM
            client = self.groq_manager.get_client()
            
            # Use the Groq client directly without instructor for JSON responses
            from groq import Groq
            groq_client = Groq(api_key=self.groq_manager.groq_api_key)
            
            response = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1  # Low temperature for consistent classification
            )
            
            # Extract content
            response_content = response.choices[0].message.content.strip()
            logger.debug(f"LLM response received: {response_content[:100]}...")
            
            # Parse JSON response
            return self.parse_llm_response(response_content)
            
        except Exception as e:
            logger.error(f"Error processing chunk with LLM: {e}")
            return None
    
    def parse_llm_response(self, response_content: str) -> Optional[List[Dict]]:
        """
        Parse LLM JSON response and validate structure
        
        Args:
            response_content: Raw LLM response string
            
        Returns:
            Parsed and validated response data or None if failed
        """
        try:
            # Clean response content (remove markdown formatting if present)
            clean_content = response_content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content.replace("```json", "").replace("```", "").strip()
            elif clean_content.startswith("```"):
                clean_content = clean_content.replace("```", "").strip()
            
            # Parse JSON
            response_data = json.loads(clean_content)
            
            # Validate structure
            if not isinstance(response_data, list):
                logger.error("Response is not a list")
                return None
            
            validated_results = []
            for item in response_data:
                try:
                    # Validate using Pydantic model
                    validated_item = NewsClassificationResponse(**item)
                    validated_results.append({
                        'news_id': validated_item.news_id,
                        'label': validated_item.label,
                        'ticker': validated_item.ticker
                    })
                except ValidationError as ve:
                    logger.warning(f"Invalid item in response: {item}, error: {ve}")
                    continue
            
            logger.debug(f"Parsed {len(validated_results)} valid classifications")
            return validated_results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response_content}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return None
    
    def validate_response_data(self, response_data: List[Dict], expected_count: int) -> bool:
        """
        Validate that response data matches expected article count
        
        Args:
            response_data: Parsed response data
            expected_count: Expected number of articles
            
        Returns:
            True if validation passes
        """
        if len(response_data) != expected_count:
            logger.warning(f"Response count mismatch: expected {expected_count}, got {len(response_data)}")
            return False
        
        # Validate label values
        for item in response_data:
            if item['label'] not in [0, 1]:
                logger.warning(f"Invalid label value: {item['label']} for news_id: {item['news_id']}")
                return False
        
        return True
