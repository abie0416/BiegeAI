import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent.gemini_client import GeminiClient
from agent.mcp import run_mcp
from agent.rag import run_rag

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
gemini_client = GeminiClient(GEMINI_API_KEY)

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question")
    
    if not question:
        return {"answer": "Please provide a question."}
    
    try:
        # Try RAG first, fallback to MCP if needed
        print(f"[DEBUG] Processing question: {question}")
        
        rag_answer = run_rag(question, gemini_client)
        print(f"[DEBUG] RAG returned: {rag_answer}")
        
        # If RAG doesn't find relevant context, use MCP
        if ("don't know" in rag_answer.lower() or 
            "no relevant" in rag_answer.lower() or 
            "cannot be answered" in rag_answer.lower() or
            "does not offer" in rag_answer.lower() or
            "does not contain" in rag_answer.lower()):
            print(f"[DEBUG] RAG didn't find relevant info, switching to MCP")
            answer = run_mcp(question, gemini_client)
            print(f"[DEBUG] MCP returned: {answer}")
        else:
            print(f"[DEBUG] Using RAG answer")
            answer = rag_answer
        
        return {"answer": answer, "debug": {"rag_answer": rag_answer, "final_method": "MCP" if "don't know" in rag_answer.lower() or "no relevant" in rag_answer.lower() else "RAG"}}
    except Exception as e:
        print(f"[DEBUG] Error occurred: {str(e)}")
        # Check if it's an API quota issue
        if "quota" in str(e).lower() or "429" in str(e):
            return {"answer": f"API Quota Error: {str(e)}. Please check your Gemini API billing."}
        return {"answer": f"Error processing your question: {str(e)}"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AI Agent is running"} 