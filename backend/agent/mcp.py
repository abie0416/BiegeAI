# LangChain MCP (Multi-Component Pipeline) implementation
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.tools import BaseTool
from typing import Optional
from agent.rag import run_rag

class RAGTool(BaseTool):
    name: str = "knowledge_base_search"
    description: str = "Search the knowledge base for relevant information to answer questions"
    gemini_client: any = None
    
    def _run(self, query: str) -> str:
        # This will be set when the tool is created
        if self.gemini_client:
            return self.gemini_client.generate(f"Search query: {query}")
        return f"Search query: {query} (Gemini client not set)"
    
    def _arun(self, query: str) -> str:
        raise NotImplementedError("Async not implemented")

def run_mcp(question, gemini_client):
    """Run MCP (Multi-Component Pipeline) with multiple tools"""
    try:
        print(f"[DEBUG] MCP: Starting with question: {question}")
        
        # Create RAG tool
        rag_tool = RAGTool()
        rag_tool.gemini_client = gemini_client
        print(f"[DEBUG] MCP: Created RAG tool")
        
        # Create general knowledge tool
        general_tool = Tool(
            name="general_knowledge",
            func=lambda q: gemini_client.generate(q),
            description="Answer general questions using AI knowledge"
        )
        print(f"[DEBUG] MCP: Created general knowledge tool")
        
        # Initialize agent with tools
        agent = initialize_agent(
            tools=[rag_tool, general_tool],
            llm=gemini_client.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        print(f"[DEBUG] MCP: Initialized agent with tools: {[tool.name for tool in agent.tools]}")
        
        # Run agent
        print(f"[DEBUG] MCP: Running agent...")
        result = agent.run(question)
        print(f"[DEBUG] MCP: Agent returned: {result}")
        return result
        
    except Exception as e:
        print(f"[DEBUG] MCP Error: {str(e)}")
        return f"[MCP Error] {str(e)}" 