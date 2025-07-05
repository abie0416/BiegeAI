import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent.gemini_client import GeminiClient
from agent.mcp import run_mcp
from agent.rag import run_rag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Debug startup information
logger.info("🚀 Starting Biege AI Backend...")
logger.info(f"📋 Environment check:")
logger.info(f"   - GEMINI_API_KEY: {'✅ Set' if GEMINI_API_KEY else '❌ Not set'}")
logger.info(f"   - PORT: {os.getenv('PORT', 'Not set')}")

app = FastAPI(title="Biege AI Backend", description="AI Agent with RAG and MCP capabilities")

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
try:
    gemini_client = GeminiClient(GEMINI_API_KEY)
    logger.info("✅ Gemini client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Gemini client: {e}")
    gemini_client = None

@app.get("/")
async def root():
    logger.info("📥 Root endpoint accessed")
    return {
        "message": "Welcome to Biege AI Backend!",
        "status": "running",
        "debug": {
            "api_key_configured": GEMINI_API_KEY is not None,
            "gemini_client_ready": gemini_client is not None,
            "port": os.getenv("PORT", "Not set"),
            "environment": "production" if os.getenv("RAILWAY_ENVIRONMENT") else "development"
        },
        "endpoints": {
            "health": "/health",
            "ask": "/ask (POST)"
        }
    }

@app.post("/ask")
async def ask(request: Request):
    logger.info("📥 /ask endpoint accessed")
    
    # Check if Gemini client is available
    if not gemini_client:
        error_msg = "❌ Gemini client not initialized. Check GEMINI_API_KEY configuration."
        logger.error(error_msg)
        return {"answer": error_msg, "debug": {"error": "gemini_client_not_initialized"}}
    
    try:
        data = await request.json()
        question = data.get("question")
        
        if not question:
            logger.warning("⚠️ No question provided in request")
            return {"answer": "Please provide a question.", "debug": {"error": "no_question_provided"}}
        
        logger.info(f"🤔 Processing question: {question[:50]}...")
        
        # Try RAG first, fallback to MCP if needed
        try:
            rag_answer = run_rag(question, gemini_client)
            logger.info(f"🔍 RAG returned: {rag_answer[:100]}...")
        except Exception as e:
            logger.error(f"❌ RAG failed: {e}")
            rag_answer = f"RAG Error: {str(e)}"
        
        # If RAG doesn't find relevant context, use MCP
        if ("don't know" in rag_answer.lower() or 
            "no relevant" in rag_answer.lower() or 
            "cannot be answered" in rag_answer.lower() or
            "does not offer" in rag_answer.lower() or
            "does not contain" in rag_answer.lower() or
            "rag error" in rag_answer.lower()):
            
            logger.info("🔄 RAG didn't find relevant info, switching to MCP")
            try:
                answer = run_mcp(question, gemini_client)
                logger.info(f"🧠 MCP returned: {answer[:100]}...")
                method_used = "MCP"
            except Exception as e:
                logger.error(f"❌ MCP failed: {e}")
                answer = f"MCP Error: {str(e)}"
                method_used = "MCP_ERROR"
        else:
            logger.info("✅ Using RAG answer")
            answer = rag_answer
            method_used = "RAG"
        
        logger.info(f"✅ Successfully processed question using {method_used}")
        return {
            "answer": answer, 
            "debug": {
                "rag_answer": rag_answer, 
                "final_method": method_used,
                "question_length": len(question),
                "answer_length": len(answer)
            }
        }
        
    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"
        logger.error(f"❌ Error in /ask endpoint: {e}")
        return {
            "answer": error_msg, 
            "debug": {
                "error": "unexpected_error",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        }

@app.get("/health")
async def health_check():
    logger.info("📥 Health check accessed")
    return {
        "status": "healthy", 
        "message": "AI Agent is running",
        "debug": {
            "api_key_configured": GEMINI_API_KEY is not None,
            "gemini_client_ready": gemini_client is not None,
            "port": os.getenv("PORT", "Not set"),
            "environment": "production" if os.getenv("RAILWAY_ENVIRONMENT") else "development"
        }
    }

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check service status"""
    logger.info("📥 Debug endpoint accessed")
    return {
        "service": "Biege AI Backend",
        "status": "running",
        "environment_variables": {
            "GEMINI_API_KEY": "Set" if GEMINI_API_KEY else "Not set",
            "PORT": os.getenv("PORT", "Not set"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "Not set")
        },
        "services": {
            "gemini_client": "Ready" if gemini_client else "Not ready"
        },
        "endpoints": {
            "root": "/",
            "health": "/health",
            "ask": "/ask (POST)",
            "debug": "/debug"
        }
    } 