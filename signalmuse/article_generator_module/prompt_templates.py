#!/usr/bin/env python3
"""
Consistent prompt templates for article generation

Follows the same formatting structure as existing report generators
for consistent output across all modules.
"""

# Earnings prompt for 1 ticker at a time (consistent with impact)
EARNINGS_PROMPT = """
You are a financial news analyst writing comprehensive earnings reports for a newspaper.

Analyze the earnings data and news articles for {ticker} and write a detailed report:

Earnings Data: {earnings}
Related News: {news}

Write a comprehensive earnings report in markdown format following this EXACT structure:

### Company Name ({ticker})

**Earnings Date:** [Date] | **EPS Forecast:** [Value] | **EPS Actual:** [Value] | **Surprise:** [Value]

#### Summary
[2-3 paragraph summary of earnings performance and key metrics]

#### Key Developments
- [Key point 1 from news]
- [Key point 2 from news]
- [Key point 3 from news]

#### Market Impact
[Analysis of how earnings results and news affect the stock and sector]

#### Investor Implications
[What investors should know and potential next steps]

---

Use consistent formatting and professional financial analysis language.
"""

# Impact prompt for 1 ticker at a time (as specified in requirements)
IMPACT_PROMPT = """
You are a financial news analyst writing market impact reports for a newspaper.

Analyze the news articles for {ticker} and write a detailed market impact report:

Related News: {news}

Write a comprehensive market impact report in markdown format following this EXACT structure:

### Company Name ({ticker})

**Latest Developments:** [Date/Time of most recent news]

#### Summary
[2-3 paragraph summary of key news developments and their significance]

#### Key News Points
- [Key point 1 from news]
- [Key point 2 from news]
- [Key point 3 from news]

#### Market Impact Assessment
[Analysis of how these developments affect the stock price, sector, and broader market]

#### Strategic Implications
[What this means for investors, competitors, and the industry]

#### Risk Factors
[Potential risks or concerns arising from these developments]

---

Use consistent formatting and professional financial analysis language.
"""
