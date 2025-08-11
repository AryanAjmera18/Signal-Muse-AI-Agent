# Calendar Functions Documentation

This document lists all the locations where earnings and economic calendar functions are called, their parameters, and return types. This is for reference when rebuilding the calendar functionality as a standalone module.

## Function Definitions

### 1. `fetch_economic_calendar()`
- **Location:** `signalmuse/generators/enhanced_briefing_generator.py:427`
- **Method signature:** `def fetch_economic_calendar(self) -> List[EconomicEvent]:`
- **Parameters:** None (uses self.fmp_api_key, self.base_url)
- **Return type:** `List[EconomicEvent]`
- **Return structure:** List of EconomicEvent dataclass objects with fields:
  - `time: str`
  - `event: str` 
  - `consensus: str`
  - `previous: str`
  - `impact: str`

### 2. `fetch_earnings_calendar()`
- **Location:** `signalmuse/generators/enhanced_briefing_generator.py:465`
- **Method signature:** `def fetch_earnings_calendar(self) -> List[EarningsEvent]:`
- **Parameters:** None (uses self.fmp_api_key, self.base_url)
- **Return type:** `List[EarningsEvent]`
- **Return structure:** List of EarningsEvent dataclass objects with fields:
  - `company: str`
  - `ticker: str`
  - `time: str`
  - `eps_estimate: str`
  - `revenue_estimate: str`

## Function Call Locations

### 1. In `signalmuse/core/agent_orchestrator.py`

#### Agent 2 Implementation (`_run_agent2` method)
- **Location:** Lines 180-181
- **Context:** Agent 2: Economic Calendar & Events
- **Code:**
  ```python
  economic_events = generator.fetch_economic_calendar()
  earnings_events = generator.fetch_earnings_calendar()
  ```
- **Parameters passed:** None
- **Usage:** Results are converted to dictionaries and stored in AgentResult:
  ```python
  return AgentResult(
      agent_name="Agent2_EconomicCalendar",
      success=True,
      data={
          'economic_events': [asdict(event) for event in economic_events],
          'earnings_events': [asdict(event) for event in earnings_events],
          'economic_count': len(economic_events),
          'earnings_count': len(earnings_events)
      },
      timestamp=datetime.now().isoformat()
  )
  ```

### 2. In `signalmuse/generators/enhanced_briefing_generator.py`

#### Briefing Generation (`generate_briefing` method)
- **Location:** Lines 629-630
- **Context:** Part of comprehensive morning briefing generation
- **Code:**
  ```python
  economic_events = self.fetch_economic_calendar()
  earnings_events = self.fetch_earnings_calendar()
  ```
- **Parameters passed:** None
- **Usage:** Results are passed to `_format_briefing` method:
  ```python
  briefing = self._format_briefing(
      market_data=market_data,
      key_headlines=key_headlines,
      economic_events=economic_events,  # List[EconomicEvent]
      earnings_events=earnings_events,   # List[EarningsEvent]
      market_context=market_context,
      ticker=ticker
  )
  ```

#### Briefing Formatting (`_format_briefing` method)
- **Location:** Lines 721-722 (economic), Lines 732-733 (earnings)
- **Context:** Formatting calendar data into markdown tables
- **Economic Calendar Usage:**
  ```python
  for event in economic_events:
      briefing += f"| {event.time} | {event.event} | {event.consensus} | {event.previous} | {event.impact} |\n"
  ```
- **Earnings Calendar Usage:**
  ```python
  for event in earnings_events:
      briefing += f"| {event.company} | {event.ticker} | {event.time} | {event.eps_estimate} | {event.revenue_estimate} |\n"
  ```

## Configuration Dependencies

### In `main.py`
- **Location:** Line 35
- **Configuration:** `enable_economic_calendar=True` in OrchestrationConfig
- **Impact:** This flag controls whether Agent 2 (calendar functionality) runs

### In `signalmuse/core/agent_orchestrator.py`
- **Location:** Line 38 (OrchestrationConfig dataclass)
- **Configuration field:** `enable_economic_calendar: bool = True`
- **Usage:** Controls whether Agent 2 runs in the orchestration pipeline

## Data Classes Used

### EconomicEvent (dataclass)
- **Location:** `signalmuse/generators/enhanced_briefing_generator.py:68`
- **Fields:**
  - `time: str`
  - `event: str`
  - `consensus: str`
  - `previous: str`
  - `impact: str`

### EarningsEvent (dataclass)
- **Location:** `signalmuse/generators/enhanced_briefing_generator.py:77`
- **Fields:**
  - `company: str`
  - `ticker: str`
  - `time: str`
  - `eps_estimate: str`
  - `revenue_estimate: str`

## API Dependencies

Both functions depend on:
- **FMP API Key:** `self.fmp_api_key` from config
- **Base URL:** `self.base_url = "https://financialmodelingprep.com/api/v3"`
- **Date Range:** Current date + 7 days
- **Endpoints:**
  - Economic: `/economic_calendar?from={today}&to={future_date}&apikey={api_key}`
  - Earnings: `/earning_calendar?from={today}&to={future_date}&apikey={api_key}`

## Notes for Rebuilding

1. **Error Handling:** Both functions return empty lists on errors instead of raising exceptions
2. **Free Tier Limitations:** Both handle 403 status codes (free tier restrictions)
3. **Data Limits:** Both limit results to top 5 events
4. **Data Formatting:** Earnings function formats EPS and revenue estimates with proper currency symbols and units
5. **Integration Points:** New module will need to be imported in both `agent_orchestrator.py` and `enhanced_briefing_generator.py`
