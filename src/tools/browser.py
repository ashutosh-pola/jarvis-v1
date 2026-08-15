import subprocess
import urllib.parse
import logging
from typing import Dict, Any

logger = logging.getLogger("jarvis.tools.browser")

def open_google_search(query: str) -> Dict[str, Any]:
    """
    Open default macOS web browser to Google search results for the given query.
    Used when the user explicitly requests 'search [X]'.
    """
    clean_query = query.strip()
    if not clean_query:
        return {"success": False, "message": "Search query cannot be empty"}

    try:
        encoded_query = urllib.parse.quote(clean_query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        # Execute macOS 'open' command to launch URL in default browser
        res = subprocess.run(["open", search_url], capture_output=True, text=True)
        
        if res.returncode == 0:
            logger.info(f"Opened web browser for query: {clean_query}")
            return {
                "success": True,
                "url": search_url,
                "message": f"Opened browser search results for '{clean_query}'"
            }
        else:
            return {"success": False, "message": f"Failed to open browser: {res.stderr.strip()}"}
            
    except Exception as e:
        logger.error(f"Browser launch exception: {e}")
        return {"success": False, "message": f"Browser launch error: {e}"}
