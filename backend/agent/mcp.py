# Model Context Protocol (MCP) implementation
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
import json
import logging
from .tools import (
    MCPTool,
    PersonalKnowledgeTool,
    GeneralTool,
    WebSearchTool,
    WeatherTool,
    CalculatorTool,
    TimeTool,
    FileTool,
    URLTool
)

# Get logger for this module
logger = logging.getLogger(__name__)

@dataclass
class MCPContext:
    """Context for MCP operations"""
    tools: List[MCPTool]
    messages: List[BaseMessage]
    metadata: Dict[str, Any]

class MCPClient:
    """Model Context Protocol client for managing tools and context"""
    
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.context = MCPContext(
            tools=[],
            messages=[],
            metadata={}
        )
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools for the MCP client"""
        # Register all tools
        self.register_tool(PersonalKnowledgeTool.create_tool())
        self.register_tool(GeneralTool.create_tool(self.gemini_client))
        self.register_tool(WebSearchTool.create_tool())
        self.register_tool(WeatherTool.create_tool())
        self.register_tool(CalculatorTool.create_tool())
        self.register_tool(TimeTool.create_tool())
        self.register_tool(FileTool.create_tool())
        self.register_tool(URLTool.create_tool())
    
    def register_tool(self, tool: MCPTool):
        """Register a new tool with the MCP client"""
        self.context.tools.append(tool)
    
    def add_message(self, message: BaseMessage):
        """Add a message to the conversation context"""
        self.context.messages.append(message)
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get tools in MCP-compliant schema format"""
        tools_schema = []
        for tool in self.context.tools:
            tool_schema = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.parameters
            }
            tools_schema.append(tool_schema)
        return tools_schema
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a specific tool with given arguments"""
        for tool in self.context.tools:
            if tool.name == tool_name:
                try:
                    # Extract the main argument (query or question)
                    if "query" in arguments:
                        result = tool.handler(arguments["query"])
                    elif "question" in arguments:
                        result = tool.handler(arguments["question"])
                    elif "location" in arguments:
                        result = tool.handler(arguments["location"])
                    elif "expression" in arguments:
                        result = tool.handler(arguments["expression"])
                    elif "url" in arguments:
                        result = tool.handler(arguments["url"])
                    elif "operation" in arguments:
                        # Handle file operations with multiple parameters
                        operation = arguments["operation"]
                        filename = arguments.get("filename")
                        content = arguments.get("content")
                        result = tool.handler(operation, filename, content)
                    elif "timezone" in arguments:
                        result = tool.handler(arguments["timezone"])
                    else:
                        result = tool.handler(str(arguments))
                    return result
                except Exception as e:
                    return f"Tool execution error: {str(e)}"
        return f"Tool '{tool_name}' not found"
    
    def run_with_context(self, question: str, rag_context: Optional[str] = None) -> str:
        """Run MCP with proper tool calling protocol and multi-tool support"""
        try:
            # Build system prompt with MCP-compliant tool information
            system_prompt = """You are an AI assistant with access to tools through the Model Context Protocol (MCP).

Available tools:
"""
            
            # Add tool schemas in MCP format
            tools_schema = self.get_tools_schema()
            for tool in tools_schema:
                system_prompt += f"""
Tool: {tool['name']}
Description: {tool['description']}
Parameters: {json.dumps(tool['inputSchema'], indent=2)}
"""
            
            system_prompt += """

To use a tool, respond with a JSON object in this format:
{
  "tool": "tool_name",
  "arguments": {
    "parameter_name": "parameter_value"
  }
}

You can use multiple tools sequentially if needed. After each tool execution, you'll receive the result and can decide whether to use another tool or provide a final answer.

IMPORTANT: Do not use the same tool consecutively. If you just used a tool, use a different tool next or provide a final answer based on the results.

To provide a final answer without using more tools, respond normally with your answer.

IMPORTANT: Always respond in the same language as the user's question. If they ask in Chinese, respond in Chinese. If they ask in English, respond in English. If they ask in any other language, respond in that same language.

When you have relevant context from the knowledge base, use it to provide accurate answers.

SANITIZATION REQUIREMENTS:
When providing final answers, ensure you do NOT include any of the following sensitive information:
1. Political views, opinions, or discussions
2. Sex-related content, innuendos, or explicit discussions  
3. Personal complaints about relationships, family, or partners
4. Private personal information (addresses, phone numbers, etc.)
5. Financial information (bank details, salaries, etc.)
6. Any content that could be considered private or sensitive

If you encounter sensitive information in the context or tool results, either:
- Replace it with "[REDACTED]" 
- Skip mentioning it entirely
- Focus on neutral, factual information only

Always provide helpful, safe responses that respect privacy and avoid inappropriate content.
"""
            
            # Add RAG context if available
            if rag_context:
                system_prompt += f"\n\nRelevant context from knowledge base:\n{rag_context}\n\nUse this context along with general knowledge when relevant to the question."
            
            # Multi-tool execution loop
            max_tool_calls = 5  # Prevent infinite loops
            tool_calls_made = 0
            all_tool_results = []
            last_used_tool = None  # Track last used tool to prevent consecutive duplicates
            
            while tool_calls_made < max_tool_calls:
                # Generate response using the model
                response = self.gemini_client.generate(question, system_prompt)
                
                # Check if response contains tool call
                try:
                    # Look for JSON tool call in response
                    if "{" in response and "}" in response:
                        # Try to extract JSON from response
                        start_idx = response.find("{")
                        end_idx = response.rfind("}") + 1
                        json_str = response[start_idx:end_idx]
                        
                        tool_call = json.loads(json_str)
                        
                        if "tool" in tool_call and "arguments" in tool_call:
                            tool_name = tool_call["tool"]
                            
                            # Log tool usage decision
                            logger.info(f"🔧 Model decided to use tool: {tool_name}")
                            logger.info(f"   - Arguments: {tool_call['arguments']}")
                            
                            # Check for consecutive duplicate tool usage
                            if tool_name == last_used_tool:
                                logger.warning(f"⚠️ Preventing consecutive duplicate tool usage: {tool_name}")
                                # Add warning to system prompt and continue
                                system_prompt += f"\n\n⚠️ WARNING: Tool '{tool_name}' was just used. Please use a different tool or provide a final answer based on the previous result."
                                continue
                            
                            # Execute the tool
                            tool_result = self.execute_tool(tool_name, tool_call["arguments"])
                            logger.info(f"✅ Tool execution result: {tool_result[:200]}...")
                            
                            all_tool_results.append({
                                "tool": tool_name,
                                "arguments": tool_call["arguments"],
                                "result": tool_result
                            })
                            
                            # Update last used tool
                            last_used_tool = tool_name
                            
                            # Add to conversation context
                            self.add_message(HumanMessage(content=question))
                            self.add_message(SystemMessage(content=f"Tool call: {json_str}"))
                            self.add_message(SystemMessage(content=f"Tool result: {tool_result}"))
                            
                            # Update system prompt with tool result for next iteration
                            system_prompt += f"\n\nTool execution result: {tool_result}\n\nYou can use this result to decide whether to use another tool or provide a final answer. Remember: Do not use the same tool consecutively."
                            
                            tool_calls_made += 1
                            continue
                    
                    # If no tool call detected, log that model decided not to use tools
                    if tool_calls_made == 0:
                        logger.info(f"🤖 Model decided not to use any tools - providing direct answer")
                        logger.info(f"   - Response preview: {response[:200]}...")
                    else:
                        logger.info(f"🤖 Model decided to stop using tools after {tool_calls_made} tool calls")
                        logger.info(f"   - Final response preview: {response[:200]}...")
                    
                    # Generate final response
                    break
                    
                except (json.JSONDecodeError, KeyError):
                    # If JSON parsing fails, assume it's a final response
                    break
            
            # Generate final response with all tool results
            if all_tool_results:
                logger.info(f"📝 Generating final response using {len(all_tool_results)} tool results")
                
                # Build comprehensive context with all tool results
                conversation_context = ""
                for msg in self.context.messages:
                    if isinstance(msg, HumanMessage):
                        conversation_context += f"User: {msg.content}\n"
                    elif isinstance(msg, SystemMessage):
                        conversation_context += f"System: {msg.content}\n"
                
                # Create summary of all tool results
                tool_results_summary = "\n\nTool Execution Summary:\n"
                for i, result in enumerate(all_tool_results, 1):
                    tool_results_summary += f"{i}. {result['tool']}: {result['result']}\n"
                
                final_prompt = f"""Based on all the tool execution results and conversation context, provide a comprehensive answer to the original question: {question}

{tool_results_summary}

IMPORTANT: Respond in the same language as the original question. If the question was asked in Chinese, respond in Chinese. If the question was asked in English, respond in English. If the question was asked in any other language, respond in that same language.

SANITIZATION REQUIREMENTS:
When providing your final answer, ensure you do NOT include any of the following sensitive information:
1. Political views, opinions, or discussions
2. Sex-related content, innuendos, or explicit discussions  
3. Personal complaints about relationships, family, or partners
4. Private personal information (addresses, phone numbers, etc.)
5. Financial information (bank details, salaries, etc.)
6. Any content that could be considered private or sensitive

If you encounter sensitive information in the tool results or context, either:
- Replace it with "[REDACTED]" 
- Skip mentioning it entirely
- Focus on neutral, factual information only

Always provide helpful, safe responses that respect privacy and avoid inappropriate content.

Synthesize all the information gathered from the tools to provide a complete and accurate answer in the appropriate language."""
                
                full_context = f"{conversation_context}\n{tool_results_summary}\n\n{final_prompt}"
                final_response = self.gemini_client.generate(question, full_context)
                
                # Add final response to context
                self.add_message(SystemMessage(content=final_response))
                
                logger.info(f"✅ Final response generated using tool results")
                return final_response
            else:
                # No tools were used, return the original response
                logger.info(f"✅ Returning direct response (no tools used)")
                self.add_message(HumanMessage(content=question))
                self.add_message(SystemMessage(content=response))
                return response
            
        except Exception as e:
            logger.error(f"[DEBUG] MCP Error: {str(e)}")
            return f"[MCP Error] {str(e)}"

def run_mcp(question: str, gemini_client, rag_context: Optional[str] = None) -> str:
    """Run Model Context Protocol with the given question and optional RAG context"""
    try:
        logger.info(f"🚀 Starting MCP execution for question: {question}")
        
        # Initialize MCP client
        mcp_client = MCPClient(gemini_client)
        logger.info(f"🔧 MCP client initialized with {len(mcp_client.context.tools)} available tools")
        
        # Run with context
        result = mcp_client.run_with_context(question, rag_context)
        logger.info(f"✅ MCP execution completed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ MCP Error: {str(e)}")
        return f"[MCP Error] {str(e)}" 