#!/usr/bin/env python3
"""
Prompt templates for morning brief generation

Consistent prompt templates for generating market summaries and other
LLM-powered content in the morning finance brief.
"""

MORNING_BRIEF_PROMPT = """
You are a professional financial analyst writing a concise market summary for a morning finance brief. 
Write a 2-3 sentence market summary that captures the current market sentiment and key drivers.

Current market context:
- Market sentiment: {sentiment}
- S&P 500 futures: {sp500_change}
- Nasdaq futures: {nasdaq_change}
- VIX (Fear Index): {vix}
- 10-Year Treasury Yield: {treasury_yield}
- Top headlines: {headlines}

Write a professional, engaging market summary that:
1. Describes the market's current mood/tone
2. Mentions key factors driving sentiment (earnings, Fed policy, economic data)
3. Sets expectations for the trading day ahead
4. Uses natural, conversational language suitable for retail investors

Keep it concise (2-3 sentences maximum) and avoid technical jargon.
"""
