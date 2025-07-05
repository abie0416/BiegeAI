# Web search tool
import requests
from .base_tool import MCPTool

class WebSearchTool:
    """Web search tool for MCP"""
    
    @staticmethod
    def create_tool() -> MCPTool:
        """Create a web search tool"""
        return MCPTool(
            name="web_search",
            description="Search the web for current information and news",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            },
            handler=WebSearchTool._handler
        )
    
    @staticmethod
    def _handler(query: str) -> str:
        """Handle web search requests"""
        try:
            # Using DuckDuckGo Instant Answer API (no API key required)
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('Abstract'):
                return f"Web search result for '{query}': {data['Abstract']}"
            elif data.get('Answer'):
                return f"Web search result for '{query}': {data['Answer']}"
            else:
                return f"No direct answer found for '{query}'. Try rephrasing your search."
                
        except Exception as e:
            return f"Web search error: {str(e)}" 