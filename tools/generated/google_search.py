import requests
import json
import sys
from typing import List, Dict, Any, Optional
from mcp_instance import mcp

# The provided Serper.dev API Key
SERPER_API_KEY = "fec8020f4ff038e224b55b963325367a72869d31"

@mcp.tool()
def google_search(query: str, num_results: int = 5) -> str:
    """
    Search Google using Serper.dev API for the given query and return the top results as a summary.
    
    Args:
        query: The search query.
        num_results: The number of results to return (default 5).
    """
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": num_results})
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        
        organic = data.get("organic", [])
        if not organic:
            return "No results found."
            
        summary_parts = []
        for item in organic[:num_results]:
            title = item.get("title", "No Title")
            snippet = item.get("snippet", "No Snippet")
            link = item.get("link", "")
            summary_parts.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}\n")
            
        return "\n---\n".join(summary_parts)
    except Exception as e:
        return f"Error during search: {str(e)}"

@mcp.tool()
def google_search_snippets(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search Google using Serper.dev API and return a list of result objects with titles, links, and snippets.
    
    Args:
        query: The search query.
        num_results: The number of results to return (default 5).
    """
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": num_results})
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        
        organic_results = data.get("organic", [])
        return organic_results[:num_results]
    except Exception as e:
        return [{"error": f"Error during search: {str(e)}"}]