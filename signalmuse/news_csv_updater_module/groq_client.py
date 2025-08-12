#!/usr/bin/env python3
"""
Groq Client Manager

Handles Groq API client setup and configuration, reusing patterns from existing codebase.
"""

import time
from typing import Optional
import instructor
from groq import Groq

from ..utils.utils import get_logger, config

logger = get_logger(__name__)

class GroqClientManager:
    """Manages Groq API client with rate limiting and error handling"""
    
    def __init__(self, rate_limit_delay: float = 5.0):
        self.groq_api_key = config.groq_api_key
        self.rate_limit_delay = rate_limit_delay
        self.client = self._setup_groq_client()
        self.last_api_call = 0.0
    
    def _setup_groq_client(self) -> Optional[instructor.Instructor]:
        """Initialize Groq client for structured outputs - reused from existing code"""
        if not self.groq_api_key:
            logger.error("Groq API key not found in environment variables")
            return None
        
        try:
            # Using the same pattern as enhanced_briefing_generator.py
            client = instructor.from_groq(Groq(api_key=self.groq_api_key))
            logger.info("Groq client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            return None
    
    def enforce_rate_limit(self):
        """Enforce rate limiting with 5-second delays between API calls"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    def is_available(self) -> bool:
        """Check if Groq client is available"""
        return self.client is not None
    
    def get_client(self) -> Optional[instructor.Instructor]:
        """Get the Groq client instance"""
        return self.client
