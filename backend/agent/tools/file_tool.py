# File operations tool
import os
from typing import Optional
from .base_tool import MCPTool

class FileTool:
    """File operations tool for MCP"""
    
    @staticmethod
    def create_tool() -> MCPTool:
        """Create a file operations tool"""
        return MCPTool(
            name="file_operations",
            description="Read, write, or list files in the current directory",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "Operation: 'read', 'write', 'list'",
                        "enum": ["read", "write", "list"]
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (for write operation)"
                    }
                },
                "required": ["operation"]
            },
            handler=FileTool._handler
        )
    
    @staticmethod
    def _handler(operation: str, filename: Optional[str] = None, content: Optional[str] = None) -> str:
        """Handle file operations"""
        try:
            if operation == "list":
                files = os.listdir(".")
                return f"Files in current directory: {', '.join(files[:10])}"  # Limit to first 10
            elif operation == "read":
                if not filename:
                    return "Error: filename required for read operation"
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                return f"File content of {filename}: {content[:500]}..."  # Limit content length
            elif operation == "write":
                if not filename or not content:
                    return "Error: filename and content required for write operation"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully wrote content to {filename}"
            else:
                return f"Unknown operation: {operation}"
                
        except Exception as e:
            return f"File operation error: {str(e)}" 