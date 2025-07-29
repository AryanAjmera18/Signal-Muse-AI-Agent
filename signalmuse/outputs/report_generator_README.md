# News Report Generator

This module generates human-like financial news reports using the Groq API. It takes CSV files containing news data and produces comprehensive markdown reports.

## Features

- **AI-Powered Analysis**: Uses Groq's LLM to generate human-like reports
- **Structured Output**: Uses Pydantic models for consistent report structure
- **Markdown Export**: Generates professional markdown reports
- **Error Handling**: Graceful fallback when API calls fail
- **Progress Tracking**: Shows progress during report generation
- **CLI Interface**: Easy command-line usage

## Setup

### 1. Install Dependencies

```bash
uv pip install groq instructor
```

### 2. Get Groq API Key

1. Visit [Groq Console](https://console.groq.com/keys)
2. Create an account and generate an API key
3. Set the environment variable:

**PowerShell:**
```powershell
$env:GROQ_API_KEY="your_api_key_here"
```

**Command Prompt:**
```cmd
set GROQ_API_KEY=your_api_key_here
```

**Or create a .env file:**
```
GROQ_API_KEY=your_api_key_here
```

## Usage

### Command Line

```bash
uv run python signalmuse/outputs/report_generator.py path/to/your/news.csv
```

**With custom output path:**
```bash
uv run python signalmuse/outputs/report_generator.py path/to/your/news.csv -o custom_report.md
```

### Python Code

```python
from signalmuse.outputs.report_generator import process_csv_to_report

# Generate report
output_path = process_csv_to_report(
    csv_file_path="signalmuse/data/real/yahoo_finance_aapl_labeled.csv",
    output_file_path="my_report.md"
)

print(f"Report generated: {output_path}")
```

## CSV Format

The CSV file should contain the following columns:
- `title`: News article title
- `link`: URL to the full article
- `published`: Publication date
- `publisher`: News source
- `summary`: Article summary/description
- `sentiment`: Sentiment classification (POSITIVE/NEGATIVE/NEUTRAL)
- `confidence`: Sentiment confidence score

## Output Format

The generated markdown report includes:

- **Header**: Report metadata and summary
- **Individual Articles**: For each news item:
  - Compelling headline
  - Publication details and source link
  - Detailed summary
  - Sentiment analysis explanation
  - Key takeaways (bullet points)
  - Market implications
- **Footer**: Report statistics

## Testing

Run the test script to verify everything is working:

```bash
uv run python test_report_generator.py
```

## Integration with Yahoo Scraper

This module is designed to work with the Yahoo scraper output:

1. Run the scraper: `uv run python signalmuse/scrapers/yahoo_scraper.py`
2. Generate report: `uv run python signalmuse/outputs/report_generator.py signalmuse/data/real/yahoo_finance_aapl_labeled.csv`

## Error Handling

- **Missing API Key**: Clear instructions provided
- **API Failures**: Fallback to simple report format
- **Invalid CSV**: Validation with helpful error messages
- **File Permissions**: Automatic directory creation

## Configuration

The module uses the Groq `llama3-8b-8192` model with:
- Max tokens: 1000
- Temperature: 0.7 (balanced creativity/consistency)
- Structured output via Instructor library 