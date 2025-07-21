"""
Reusable Yahoo Finance RSS pipeline:
- Fetches news articles by ticker
- Classifies sentiment using HuggingFace transformers
- Returns data as list of dicts (optionally saves as CSV)
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from transformers import pipeline
import torch
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional

def load_sentiment_pipeline():
    device = 0 if torch.cuda.is_available() else -1
    print(f"[YahooRSS] Sentiment model using {'cuda' if device == 0 else 'cpu'}")
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=device)

def fetch_yahoo_finance_rss(ticker: str) -> List[Dict]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, "xml")

        articles = []
        for item in soup.find_all("item"):
            title = item.title.text if item.title else "No Title"
            link = item.link.text if item.link else "No Link"
            pub_date = item.pubDate.text if item.pubDate else datetime.utcnow().isoformat()
            summary = item.description.text if item.description else ""
            articles.append({
                "title": title,
                "link": link,
                "published": pub_date,
                "publisher": "Yahoo Finance",
                "summary": summary
            })
        return articles
    except Exception as e:
        print(f"[YahooRSS] ❌ Failed to fetch articles for {ticker}:", e)
        return []

def classify_sentiment(articles: List[Dict], classifier) -> List[Dict]:
    for article in articles:
        try:
            result = classifier(article["title"])[0]
            article["sentiment"] = result["label"]
            article["confidence"] = round(result["score"], 4)
        except Exception:
            article["sentiment"] = "UNKNOWN"
            article["confidence"] = 0.0
    return articles

def save_to_csv(records: List[Dict], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    df.to_csv(path, index=False)
    print(f"[YahooRSS] ✅ Saved {len(df)} records to {path}")

def get_yahoo_news_sentiment(
    ticker: str,
    classifier=None,
    save_path: Optional[str] = None
) -> List[Dict]:
    articles = fetch_yahoo_finance_rss(ticker)
    if not articles:
        print(f"[YahooRSS] ⚠️ No articles found for {ticker}")
        return []
    if classifier is None:
        classifier = load_sentiment_pipeline()
    labeled = classify_sentiment(articles, classifier)
    if save_path:
        save_to_csv(labeled, save_path)
    return labeled

def batch_yahoo_news_sentiment(
    tickers: List[str],
    save_path: Optional[str] = None
) -> List[Dict]:
    classifier = load_sentiment_pipeline()
    all_results = []
    for ticker in tickers:
        print(f"[YahooRSS] Fetching: {ticker}")
        articles = fetch_yahoo_finance_rss(ticker)
        labeled = classify_sentiment(articles, classifier)
        for record in labeled:
            record["ticker"] = ticker
        all_results.extend(labeled)
    if save_path:
        save_to_csv(all_results, save_path)
    return all_results

if __name__ == "__main__":
    # Quick demo run
    result = get_yahoo_news_sentiment("AAPL", save_path="signalmuse/data/real/yahoo_finance_aapl_labeled.csv")
    print(result[:2])
