# General knowledge tool
from .base_tool import MCPTool

class GeneralTool:
    """General knowledge tool for MCP"""
    
    @staticmethod
    def create_tool(gemini_client) -> MCPTool:
        """Create a general knowledge tool"""
        return MCPTool(
            name="general_knowledge",
            description="Answer general questions using AI knowledge",
            parameters={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to answer"
                    }
                },
                "required": ["question"]
            },
            handler=lambda question: GeneralTool._handler(question, gemini_client)
        )
    
    @staticmethod
    def _handler(question: str, gemini_client) -> str:
        """Handle general knowledge questions"""
        try:
            return gemini_client.generate(question)
        except Exception as e:
            return f"General knowledge error: {str(e)}" 