# Weather tool
import requests
import os
from .base_tool import MCPTool

class WeatherTool:
    """Weather tool for MCP"""
    
    @staticmethod
    def create_tool() -> MCPTool:
        """Create a weather tool"""
        return MCPTool(
            name="get_weather",
            description="Get current weather information for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location"
                    }
                },
                "required": ["location"]
            },
            handler=WeatherTool._handler
        )
    
    @staticmethod
    def _handler(location: str) -> str:
        """Handle weather requests"""
        try:
            # Using OpenWeatherMap API (free tier)
            # Note: In production, you'd want to use an API key
            api_key = os.getenv("OPENWEATHER_API_KEY", "")
            if not api_key:
                return f"Weather information for {location}: API key not configured. Please set OPENWEATHER_API_KEY environment variable."
            
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                temp = data['main']['temp']
                description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                return f"Weather in {location}: {temp}°C, {description}, Humidity: {humidity}%"
            else:
                return f"Weather data not available for {location}"
                
        except Exception as e:
            return f"Weather error: {str(e)}" 