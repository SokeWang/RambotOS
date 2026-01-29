from mcp_instance import mcp
import requests

@mcp.tool()
def check_connectivity():
    """
    Checks the reachability and measures the exact latency (ping time via HTTP) for Google (google.com) and Bing (bing.com).
    """
    results = {}
    sites = {
        "Google": "https://www.google.com",
        "Bing": "https://www.bing.com"
    }
    
    for name, url in sites.items():
        try:
            # Using requests.get and measuring response.elapsed for precise timing
            response = requests.get(url, timeout=5)
            latency_ms = response.elapsed.total_seconds() * 1000
            
            if response.status_code == 200:
                results[name] = {
                    "status": "Online",
                    "latency_ms": round(latency_ms, 2)
                }
            else:
                results[name] = {
                    "status": f"Error: Status code {response.status_code}",
                    "latency_ms": round(latency_ms, 2)
                }
        except Exception as e:
            results[name] = {
                "status": f"Offline: {str(e)}",
                "latency_ms": None
            }
            
    return results