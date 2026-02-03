---
name: stock-market
description: Fetch real-time stock prices, market trends, and financial data. Includes ML-based trend analysis for future price projections. Use when the user asks for stock quotes, market indices, company performance, or future price trends.
---

# Stock Market

This skill provides guidance on fetching and presenting financial market data, including trend analysis.

## Workflows

### 1. Fetching Stock Prices
When asked for a stock price:
1. Identify the ticker symbol. If unsure, use `web_search` to find the symbol (e.g., "AAPL for Apple").
2. Search for the current price using `web_search` with a query like "[Ticker] stock price today".
3. Report the price, the daily change (if available), and the timestamp of the data.

### 2. Market Indices
When asked about the "market" or specific indices (S&P 500, Dow Jones, NASDAQ):
1. Use `web_search` to get the current value and daily percentage change.
2. Provide a brief summary of the market sentiment (e.g., "The Dow is up 1.2% today").

### 3. Future Trend Analysis (ML Model)
When asked for trend analysis or future price predictions:
1. Fetch historical price data (last 5-10 data points) using `web_search` (e.g., "[Ticker] historical stock prices last 10 days").
2. Parse the prices into a list of numbers.
3. Execute the trend analysis script:
   ```bash
   python3 scripts/trend_analysis.py [price1] [price2] [price3] ...
   ```
4. Interpret the results:
   - **Trend**: Direction of movement.
   - **Projected Next**: A mathematical projection based on linear regression.
   - **R-squared**: Confidence level (closer to 1.0 is better).
5. Present the analysis clearly, noting that it is a mathematical projection and not financial advice.

### 4. Financial Research
When asked for company details or news:
1. Search for recent news and major financial metrics (P/E ratio, Market Cap) using `web_search`.
2. Present a concise summary.

## Reference Material
- See [tickers.md](references/tickers.md) for a list of common ticker symbols.
