# SignalMuse: AI Financial Education Agent

SignalMuse is an educational AI agent that analyzes real-time stock market data and recent news to explain why a stock is performing well or poorly. It fetches live financial data, processes news, and provides easy-to-understand explanations, making financial literacy more accessible.

## Project Overview

* **Real-time data**: Connects to financial APIs to get up-to-date prices, volume, and news.
* **Explanation engine**: Uses AI and NLP to summarize why a stock’s price has moved, referencing real events and news.
* **Educational focus**: Designed for learning and transparency, not financial advice.
* **Extensible**: Modular structure with `api`, `scrapers`, `extractors`, and more.

## Directory Structure

```
signalmuse/
├── api/          # API clients for market data and news
├── scrapers/     # Custom web/data scrapers
├── extractors/   # NLP, info extraction modules
├── data/         # Datasets, raw and processed
├── core/         # Core agent logic, orchestration
├── outputs/      # Reports, explanations, user outputs
├── config/       # .env and configuration files
├── tests/        # Unit and integration tests
└── docs/         # Project documentation
```

## Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/signalmuse.git
   cd signalmuse
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**

   * Copy `.env.example` to `.env` and add your API keys and settings.

4. **Run initial setup (create DB, etc.):**

   ```bash
   python core/setup.py
   ```

5. **Run tests:**

   ```bash
   pytest
   ```

## Python Dependencies

See [requirements.txt](./requirements.txt) for core packages.

* `requests`
* `pydantic`
* `python-dotenv`
* `pytest`
* `sqlite3`
* `black` (for code formatting)
* ... *(add as project grows)*

## Style Guide

* **Python version:** 3.9+
* **Formatting:** [Black](https://black.readthedocs.io/en/stable/) (autoformat)
* **Linting:** [PEP8](https://peps.python.org/pep-0008/)
* **Testing:** [pytest](https://docs.pytest.org/en/stable/)

**All code should be formatted with Black before commit.**

```bash
black .
```

## References

* [PEP8 Python Style Guide](https://peps.python.org/pep-0008/)
* [Black Formatter](https://black.readthedocs.io/en/stable/)


