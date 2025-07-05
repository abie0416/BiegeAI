# Time tool
import datetime
from .base_tool import MCPTool

class TimeTool:
    """Time tool for MCP"""
    
    @staticmethod
    def create_tool() -> MCPTool:
        """Create a time tool"""
        return MCPTool(
            name="get_time",
            description="Get current time and date information",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (optional, defaults to UTC)",
                        "default": "UTC"
                    }
                },
                "required": []
            },
            handler=TimeTool._handler
        )
    
    @staticmethod
    def _handler(timezone: str = "UTC") -> str:
        """Handle time and date requests"""
        try:
            now = datetime.datetime.now()
            if timezone.upper() == "UTC":
                utc_time = datetime.datetime.utcnow()
                return f"Current time (UTC): {utc_time.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                # For other timezones, you'd need pytz library
                return f"Current time (local): {now.strftime('%Y-%m-%d %H:%M:%S')} (Timezone conversion not implemented)"
                
        except Exception as e:
            return f"Time error: {str(e)}" 