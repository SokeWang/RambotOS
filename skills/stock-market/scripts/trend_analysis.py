import sys
import numpy as np

def analyze_trend(prices):
    if len(prices) < 2:
        return "Insufficient data for trend analysis."
    
    x = np.arange(len(prices))
    y = np.array(prices)
    
    # Linear regression: y = mx + c
    m, c = np.polyfit(x, y, 1)
    
    # Calculate R-squared for confidence
    p = np.poly1d([m, c])
    y_pred = p(x)
    y_bar = np.mean(y)
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - y_bar)**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    trend = "Upward" if m > 0 else "Downward"
    if abs(m) < 0.01:
        trend = "Stable"
    
    projected_next = m * len(prices) + c
    
    return {
        "trend": trend,
        "slope": float(m),
        "r_squared": float(r_squared),
        "projected_next": float(projected_next)
    }

if __name__ == "__main__":
    try:
        # Expecting prices as space-separated arguments
        input_prices = [float(p) for p in sys.argv[1:]]
        result = analyze_trend(input_prices)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
