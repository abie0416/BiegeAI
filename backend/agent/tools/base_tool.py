# Base tool class for MCP implementation
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class MCPTool:
    """Base class for tools in the Model Context Protocol"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Any 