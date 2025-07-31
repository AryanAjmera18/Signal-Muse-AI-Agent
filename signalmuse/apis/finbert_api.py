#!/usr/bin/env python3
"""
FastAPI Wrapper for FinBERT Sentiment Analysis

A microservice that provides financial sentiment analysis using FinBERT.
Perfect for integrating into Agent 1 pipeline for news analysis.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import logging
from typing import Dict, List, Optional
import uvicorn
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FinBERT Sentiment Analysis API",
    description="Financial sentiment analysis using FinBERT model",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SentimentRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for sentiment")
    source: Optional[str] = Field(None, description="Source of the text (e.g., 'Reuters', 'Bloomberg')")
    category: Optional[str] = Field(None, description="Category of the text (e.g., 'earnings', 'macro', 'crypto')")

class SentimentResponse(BaseModel):
    text: str
    sentiment: str  # "positive", "negative", "neutral"
    confidence: float
    source: Optional[str] = None
    category: Optional[str] = None
    timestamp: str
    model: str = "finbert-tone"

class BatchSentimentRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to analyze")
    sources: Optional[List[str]] = Field(None, description="List of sources for each text")
    categories: Optional[List[str]] = Field(None, description="List of categories for each text")

class BatchSentimentResponse(BaseModel):
    results: List[SentimentResponse]
    total_processed: int
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    timestamp: str

# Global variables for model
model = None
tokenizer = None
model_name = "yiyanghkust/finbert-tone"

def load_model():
    """Load FinBERT model and tokenizer"""
    global model, tokenizer
    
    try:
        logger.info(f"Loading FinBERT model: {model_name}")
        
        # Load tokenizer and model
        tokenizer = BertTokenizer.from_pretrained(model_name)
        model = BertForSequenceClassification.from_pretrained(model_name)
        
        # Set model to evaluation mode
        model.eval()
        
        # Move to GPU if available
        if torch.cuda.is_available():
            model = model.cuda()
            logger.info("Model loaded on GPU")
        else:
            logger.info("Model loaded on CPU")
        
        logger.info("FinBERT model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return False

def classify_sentiment(text: str) -> Dict[str, any]:
    """Classify sentiment of a single text"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Tokenize input
        inputs = tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512,
            padding=True
        )
        
        # Move to GPU if available
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Get predictions
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=1)
        
        # Get predicted class and confidence
        predicted_class = torch.argmax(probs, dim=1).item()
        confidence = torch.max(probs).item()
        
        # Map class to sentiment
        sentiment_map = ["neutral", "positive", "negative"]
        sentiment = sentiment_map[predicted_class]
        
        return {
            "sentiment": sentiment,
            "confidence": round(confidence, 4),
            "probabilities": {
                "neutral": round(probs[0][0].item(), 4),
                "positive": round(probs[0][1].item(), 4),
                "negative": round(probs[0][2].item(), 4)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in sentiment classification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    success = load_model()
    if not success:
        logger.error("Failed to load model on startup")

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        model_name=model_name,
        timestamp=datetime.now().isoformat()
    )

@app.post("/classify", response_model=SentimentResponse)
async def classify_single(request: SentimentRequest):
    """Classify sentiment of a single text"""
    start_time = datetime.now()
    
    # Perform sentiment analysis
    result = classify_sentiment(request.text)
    
    return SentimentResponse(
        text=request.text,
        sentiment=result["sentiment"],
        confidence=result["confidence"],
        source=request.source,
        category=request.category,
        timestamp=start_time.isoformat()
    )

@app.post("/classify/batch", response_model=BatchSentimentResponse)
async def classify_batch(request: BatchSentimentRequest):
    """Classify sentiment of multiple texts"""
    start_time = datetime.now()
    results = []
    
    # Validate input lengths
    if request.sources and len(request.sources) != len(request.texts):
        raise HTTPException(status_code=400, detail="Sources list must match texts list length")
    
    if request.categories and len(request.categories) != len(request.texts):
        raise HTTPException(status_code=400, detail="Categories list must match texts list length")
    
    # Process each text
    for i, text in enumerate(request.texts):
        try:
            result = classify_sentiment(text)
            
            response = SentimentResponse(
                text=text,
                sentiment=result["sentiment"],
                confidence=result["confidence"],
                source=request.sources[i] if request.sources else None,
                category=request.categories[i] if request.categories else None,
                timestamp=datetime.now().isoformat()
            )
            
            results.append(response)
            
        except Exception as e:
            logger.error(f"Error processing text {i}: {str(e)}")
            # Continue with other texts instead of failing completely
            continue
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return BatchSentimentResponse(
        results=results,
        total_processed=len(results),
        processing_time=round(processing_time, 3)
    )

@app.get("/model/info")
async def model_info():
    """Get model information"""
    return {
        "model_name": model_name,
        "model_loaded": model is not None,
        "device": "cuda" if torch.cuda.is_available() and model is not None and next(model.parameters()).is_cuda else "cpu",
        "max_length": 512,
        "supported_sentiments": ["neutral", "positive", "negative"]
    }

@app.post("/test")
async def test_classification():
    """Test endpoint with sample financial text"""
    test_text = "Fed raises interest rates by 25 basis points, signaling more hikes to come"
    
    result = classify_sentiment(test_text)
    
    return {
        "test_text": test_text,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Load model before starting server
    if load_model():
        uvicorn.run(
            "finbert_api:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    else:
        logger.error("Failed to load model. Exiting.")
        exit(1) 