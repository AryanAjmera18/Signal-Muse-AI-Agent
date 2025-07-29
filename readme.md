# SignalMuse: AI Financial News Analysis Agent

SignalMuse is an AI-powered financial news analysis system that scrapes real-time stock market news, performs sentiment analysis, and generates comprehensive human-like reports using advanced language models. It transforms raw financial news into actionable insights, making financial analysis more accessible and intelligent.

## 🚀 Key Features

* **Real-time News Scraping**: Fetches latest news from Yahoo Finance RSS feeds
* **AI-Powered Sentiment Analysis**: Uses DistilBERT for accurate sentiment classification
* **Human-like Report Generation**: Leverages Groq's LLM to create professional financial analysis reports
* **Automated Workflow**: Complete pipeline from ticker input to final markdown report
* **Structured Output**: Professional markdown reports with summaries, key points, and market implications
* **Error Handling**: Robust fallbacks and progress tracking

## 🏗️ System Architecture

```
signalmuse/
├── api/              # API clients (Finnhub, future integrations)
├── scrapers/         # Yahoo Finance RSS scraper with sentiment analysis
├── outputs/          # Groq-powered report generator
├── data/            
│   └── real/         # Generated CSV files with news data
├── extractors/       # NLP and information extraction modules
├── core/            # Core agent logic and orchestration
├── tests/           # Unit and integration tests
└── docs/            # Project documentation

Root files:
├── news_analysis_driver.py    # Main workflow script
├── requirements.txt           # Python dependencies  
├── env.template              # Environment variables template
├── .env                      # Your API keys (create from template)
└── pyproject.toml            # Project configuration
```

## 📋 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Signal-Muse-AI-Agent.git
cd Signal-Muse-AI-Agent
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Copy the environment template and configure your API keys:

```bash
# Copy the template
cp env.template .env
# And then edit the .env file with your actual API keys --> Follow steps given in env.template
```

## 🎯 Usage

### Complete Workflow (Recommended)

Run the main driver script for the full experience:

```bash
python news_analysis_driver.py
```

This will:
1. Ask you for a stock ticker symbol (e.g., AAPL, TSLA, GOOGL) and then confirm it for safety.
2. Fetch the latest news from Yahoo Finance
3. Perform sentiment analysis on each article
4. Generate a comprehensive AI-powered report
5. Save everything with timestamped filenames

### 🚀 Example Workflow

```bash
$ uv run python news_analysis_driver.py

🚀 News Analysis Driver - Stock Market Intelligence
This tool will fetch news and generate AI-powered analysis reports

🔍 Checking dependencies...
✅ All dependencies are ready!

==================================================
📈 Stock News Analysis
==================================================

🎯 Enter stock ticker symbol (e.g., AAPL, GOOGL, TSLA): TSLA

✅ You entered: TSLA. Proceed? (y/n): y

🔄 Step 1: Fetching news for TSLA...
📡 Scraping Yahoo Finance news for TSLA...
[YahooRSS] Sentiment model using cuda
✅ Successfully scraped 15 articles
📁 Data saved to: signalmuse/data/real/tsla_news_20250129_143022.csv

🔄 Step 2: Generating AI-powered report...
🔧 Setting up Groq API client...
📖 Reading news data from: signalmuse/data/real/tsla_news_20250129_143022.csv
Found 15 news items to process
🔄 Processing article 1/15: Tesla's Q4 Earnings Beat Expectations...
✅ Report generated and appended (1/15)
...

🎉 ANALYSIS COMPLETE!
============================================================
📊 Ticker analyzed: TSLA
📁 Raw data: signalmuse/data/real/tsla_news_20250129_143022.csv  
📄 AI Report: signalmuse/outputs/tsla_analysis_report_20250129_143025.md
============================================================
```


## 📊 Outputs

The system generates two main outputs:

**1. CSV Data File** (`signalmuse/data/real/`)
- Raw news articles with sentiment scores
- Columns: title, link, published, publisher, summary, sentiment, confidence

**2. Markdown Report** (`signalmuse/outputs/`)
- AI-generated analysis for each article
- Professional formatting with headlines, summaries, key points
- Market implications and sentiment analysis
- Direct links to original articles

## 🛠️ Technical Details

### News Scraping Pipeline
1. **RSS Fetching**: Connects to Yahoo Finance RSS feeds by ticker
2. **Content Parsing**: Extracts title, summary, publication date, and links
3. **Sentiment Analysis**: Uses DistilBERT model for sentiment classification
4. **Data Storage**: Saves structured data to CSV with confidence scores

### Report Generation Pipeline
1. **CSV Processing**: Reads scraped news data
2. **AI Analysis**: Uses Groq's Llama3-8B model via Instructor library
3. **Structured Output**: Generates reports with consistent schema
4. **Markdown Formatting**: Creates professional, readable reports

### Key Technologies
- **Sentiment Model**: `distilbert-base-uncased-finetuned-sst-2-english`
- **LLM**: Groq's `llama3-8b-8192` model
- **Web Scraping**: BeautifulSoup with XML parsing
- **GPU Support**: Automatic CUDA detection for faster inference

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for high-speed LLM inference
- [Hugging Face](https://huggingface.co/) for sentiment analysis models  
- [Yahoo Finance](https://finance.yahoo.com/) for news RSS feeds

---

**⚠️ Disclaimer**: This tool is for educational and research purposes only. It does not provide financial advice. Always consult with qualified financial professionals before making investment decisions.