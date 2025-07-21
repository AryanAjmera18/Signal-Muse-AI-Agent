import os
import time
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
import logging

# Load env vars
load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"

# Logging setup
logging.basicConfig(level=logging.INFO, filename="api.log")

# --- JSON Schema using Pydantic
class StockQuote(BaseModel):
    ticker: str
    name: str = ""
    price: float
    volume: int
    gain_percent: float
    market_cap: float
    sector: str = ""

class FinnhubClient:
    def __init__(self, api_key=FINNHUB_API_KEY, max_calls_per_min=60):
        self.api_key = api_key
        self.calls_per_min = int(os.getenv("API_CALLS_PER_MINUTE", max_calls_per_min))
        self.calls = 0
        self.last_reset = time.time()

    def throttle(self):
        now = time.time()
        if now - self.last_reset > 60:
            self.calls = 0
            self.last_reset = now
        if self.calls >= self.calls_per_min:
            sleep_time = 60 - (now - self.last_reset)
            logging.info(f"Rate limit hit, sleeping {sleep_time}s")
            time.sleep(sleep_time)
            self.calls = 0
            self.last_reset = time.time()
        self.calls += 1

    def get_quote(self, symbol):
        self.throttle()
        url = f"{BASE_URL}/quote"
        params = {"symbol": symbol, "token": self.api_key}
        tries = 3
        for i in range(tries):
            try:
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 429:
                    logging.warning("429 Too Many Requests, retrying...")
                    time.sleep(5)
                    continue
                resp.raise_for_status()
                data = resp.json()
                # Compose normalized output:
                result = StockQuote(
                    ticker=symbol,
                    price=data["c"],
                    volume=data.get("v", 0),
                    gain_percent=((data["c"] - data["pc"]) / data["pc"] * 100) if data["pc"] else 0,
                    market_cap=0,  # Set by another call
                )
                return  result.model_dump()
            except (requests.RequestException, ValidationError) as e:
                logging.error(f"Error fetching quote for {symbol}: {e}")
                if i == tries - 1:
                    raise
                time.sleep(2)
        return None

# Usage Example
if __name__ == "__main__":
    client = FinnhubClient()
    print(client.get_quote("AAPL"))
