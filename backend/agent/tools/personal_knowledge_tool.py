# Knowledge base search tool
from .base_tool import MCPTool

class PersonalKnowledgeTool:
    """Personal knowledge tool for accessing RAG documents about friends and events"""
    
    @staticmethod
    def create_tool() -> MCPTool:
        """Create a personal knowledge tool for friends and events"""
        return MCPTool(
            name="personal_knowledge",
            description="Access personal knowledge base for information about personal acquaintances, friends, family members, or private events that aren't widely known. Use this tool when asked about specific names or events that aren't public figures, celebrities, or major historical events. This tool helps answer questions about your personal relationships and private experiences.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question about a specific person (friend, family, acquaintance) or private event that isn't a well-known public figure or major historical event"
                    }
                },
                "required": ["query"]
            },
            handler=PersonalKnowledgeTool._handler
        )
    
    @staticmethod
    def _handler(query: str) -> str:
        """Handle personal knowledge queries about friends and events"""
        try:
            # This tool leverages the RAG context already provided in the system prompt
            # to answer questions about personal friends, events, and experiences
            return f"Personal knowledge query: {query} - I'll use the available context about your friends and events to provide an accurate answer."
        except Exception as e:
            return f"Personal knowledge query error: {str(e)}" 