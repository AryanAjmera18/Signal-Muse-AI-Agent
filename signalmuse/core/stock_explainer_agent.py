"""
Stock Explainer AI Agent for SignalMuse
- Fetches real-time stock quote from Finnhub
- Fetches recent news & sentiment from Yahoo Finance
- Generates an educational explanation for the user
"""

from scrapers.yahoo_scraper import get_yahoo_news_sentiment
from datetime import datetime
from typing import Dict, List
from apis.finnhub_client import FinnhubClient

def summarize_sentiment(news: List[Dict]) -> str:
    if not news:
        return "No recent news or sentiment data."
    pos = sum(1 for item in news if item["sentiment"] == "POSITIVE")
    neg = sum(1 for item in news if item["sentiment"] == "NEGATIVE")
    neu = sum(1 for item in news if item["sentiment"] == "NEUTRAL")
    total = max(1, pos + neg + neu)
    return f"Recent news: {pos} positive, {neg} negative, {neu} neutral headlines."

def educational_explanation(stock: Dict, news: List[Dict]) -> str:
    expl = []
    expl.append(f"Stock: {stock['ticker']} | Price: ${stock['price']:.2f} | Change: {stock['gain_percent']:.2f}%")

    # Explain gain/loss in context
    if stock["gain_percent"] > 0.5:
        expl.append("The stock is up today.")
    elif stock["gain_percent"] < -0.5:
        expl.append("The stock is down today.")
    else:
        expl.append("The stock price is relatively stable today.")

    # Add sentiment
    expl.append(summarize_sentiment(news))

    # Show the most recent relevant headline (if any)
    if news:
        top_news = news[0]
        expl.append(f"Most recent headline: \"{top_news['title']}\"")
        expl.append(f"Published: {top_news['published']}")
        expl.append(f"Sentiment: {top_news['sentiment']} (confidence {top_news.get('confidence', 0):.2f})")
        if top_news['sentiment'] == 'POSITIVE':
            expl.append("This news may be helping to push the stock price up.")
        elif top_news['sentiment'] == 'NEGATIVE':
            expl.append("This news may be contributing to a price drop.")
        else:
            expl.append("This news appears neutral.")

    expl.append("\nEducational note: Stock prices often move in response to news about the company, the broader industry, or market trends. Positive news can boost investor confidence, while negative news can lead to selling.")
    return "\n".join(expl)

def explain_stock(ticker: str):
    print(f"\n[SignalMuse] Getting educational explanation for {ticker}...\n")
    # Fetch Finnhub data
    client = FinnhubClient()
    stock = client.get_quote(ticker)
    if not stock:
        print("Could not fetch stock data.")
        return

    # Fetch Yahoo news + sentiment
    news = get_yahoo_news_sentiment(ticker)

    # Generate educational explanation
    explanation = educational_explanation(stock, news)
    print("\n=== Educational Explanation ===")
    print(explanation)
    print("==============================")

if __name__ == "__main__":
    ticker = input("Enter stock ticker (e.g. AAPL): ").strip().upper()
    explain_stock(ticker)
