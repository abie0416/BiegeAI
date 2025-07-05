# Calculator tool
from .base_tool import MCPTool

class CalculatorTool:
    """Calculator tool for MCP"""
    
    @staticmethod
    def create_tool() -> MCPTool:
        """Create a calculator tool"""
        return MCPTool(
            name="calculator",
            description="Perform mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            },
            handler=CalculatorTool._handler
        )
    
    @staticmethod
    def _handler(expression: str) -> str:
        """Handle mathematical calculations"""
        try:
            # Sanitize the expression to prevent code injection
            allowed_chars = set('0123456789+-*/()., ')
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression. Only numbers, operators (+, -, *, /), parentheses, and decimal points are allowed."
            
            # Evaluate the expression
            result = eval(expression)
            return f"Calculation: {expression} = {result}"
            
        except Exception as e:
            return f"Calculation error: {str(e)}" 