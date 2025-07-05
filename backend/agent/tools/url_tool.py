# URL content fetcher tool
import requests
import re
from .base_tool import MCPTool

class URLTool:
    """URL content fetcher tool for MCP"""
    
    @staticmethod
    def create_tool() -> MCPTool:
        """Create a URL content fetcher tool"""
        return MCPTool(
            name="fetch_url_content",
            description="Fetch and summarize content from a URL",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch content from"
                    }
                },
                "required": ["url"]
            },
            handler=URLTool._handler
        )
    
    @staticmethod
    def _handler(url: str) -> str:
        """Handle URL content fetching"""
        try:
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Extract text content (basic implementation)
            content = response.text
            # Remove HTML tags and get first 500 characters
            clean_content = re.sub(r'<[^>]+>', '', content)
            clean_content = ' '.join(clean_content.split())
            
            return f"Content from {url}: {clean_content[:500]}..."
            
        except Exception as e:
            return f"URL content error: {str(e)}" 