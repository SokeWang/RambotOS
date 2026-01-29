import yfinance as yf
from mcp_instance import mcp
from datetime import datetime

@mcp.tool()
def fetch_stock_price(ticker: str, start_date: str = None, end_date: str = None) -> str:
    """
    Fetches stock prices for a given ticker symbol. Can return real-time price
    or historical prices for a specific date range.

    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA').
        start_date: Optional start date for historical data (YYYY-MM-DD).
        end_date: Optional end date for historical data (YYYY-MM-DD).
    """
    try:
        stock = yf.Ticker(ticker.upper())
        
        if start_date:
            # Fetch historical data
            # yfinance history handles None end_date as 'until now'
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return f"No historical data found for {ticker.upper()} between {start_date} and {end_date or 'today'}."
            
            results = []
            for date, row in hist.iterrows():
                results.append(f"{date.strftime('%Y-%m-%d')}: Open={row['Open']:.2f}, High={row['High']:.2f}, Low={row['Low']:.2f}, Close={row['Close']:.2f}")
            
            header = f"Historical data for {ticker.upper()}:\n"
            return header + "\n".join(results)
        
        else:
            # Real-time price logic
            info = stock.fast_info
            
            if 'last_price' not in info or info['last_price'] is None:
                # Fallback to history for last closing price if fast_info fails
                hist = stock.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    return f"Could not find price information for ticker: {ticker.upper()}"
            else:
                current_price = info['last_price']
                
            currency = info.get('currency', 'USD')
            return f"The current price of {ticker.upper()} is {current_price:.2f} {currency}."
            
    except Exception as e:
        return f"Error fetching stock price for {ticker}: {str(e)}"