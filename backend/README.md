        n klm j]90ik[l# Backend

This backend uses FastAPI, ChromaDB, and LangChain to integrate with the Gemini API for LLM-powered RAG (Retrieval-Augmented Generation) and MCP (Multi-Component Pipeline).

## Setup

1. Place your Gemini API key in a `.env` file in this directory:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Initialize the knowledge base with sample data:
   ```
   python init_knowledge_base.py
   ```
4. Run the server:
   ```
   uvicorn main:app --reload
   ```

## Features

- **RAG (Retrieval-Augmented Generation)**: Uses ChromaDB vectorstore with sentence transformers for semantic search
- **Advanced Text Chunking**: RecursiveCharacterTextSplitter with 200-character chunks and 50-character overlap
- **Multi-Document Retrieval**: Retrieves up to 10 documents with similarity filtering
- **Map-Reduce Chain**: Uses LangChain's map_reduce for better chunk processing
- **MCP (Multi-Component Pipeline)**: LangChain agent with multiple tools for complex reasoning
- **LangChain Integration**: Clean, maintainable code using LangChain abstractions
- **Gemini Pro**: Latest Google Gemini model for text generation

## Endpoints
- `/ask`: POST endpoint for chat interaction with the agent
- `/health`: GET endpoint for health check

## Architecture

- `agent/gemini_client.py`: LangChain Gemini integration
- `agent/rag.py`: RAG pipeline using LangChain chains
- `agent/mcp.py`: Multi-component pipeline with LangChain agents
- `db/chroma_client.py`: ChromaDB vectorstore setup 