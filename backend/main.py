import os
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent.gemini_client import GeminiClient
from agent.mcp import run_mcp
from agent.rag import fetch_documents
from init_knowledge_base import init_knowledge_base

# Configure logging with forced output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Force stdout to flush immediately
sys.stdout.flush()

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

# Initialize knowledge base with sample data
try:
    logger.info("📚 Initializing knowledge base...")
    init_knowledge_base()
    logger.info("✅ Knowledge base initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize knowledge base: {e}")

def get_rag_context(question: str) -> str:
    """Always fetch RAG context for the question"""
    try:
        logger.info("🔍 Fetching RAG context...")
        rag_context = fetch_documents(question)
        logger.info(f"✅ RAG context fetched: {len(rag_context)} characters")
        return rag_context
    except Exception as e:
        logger.error(f"❌ RAG context fetch failed: {e}")
        return f"RAG Error: {str(e)}"

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

@app.get("/test-logs")
async def test_logs():
    """Test endpoint to verify logging is working"""
    logger.debug("DEBUG: This is a debug message")
    logger.info("INFO: This is an info message")
    logger.warning("WARNING: This is a warning message")
    logger.error("ERROR: This is an error message")
    
    # Also test print statements
    print("PRINT: This is a print statement")
    sys.stdout.flush()
    
    return {"message": "Log test completed", "check_console": True}

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
        
        # Step 1: Always fetch RAG context
        rag_context = get_rag_context(question)
        
        # Step 2: Run MCP with RAG context and let model decide tools
        try:
            answer = run_mcp(question, gemini_client, rag_context)
            logger.info(f"✅ MCP completed successfully")
            method_used = "MCP_WITH_RAG_CONTEXT"
        except Exception as e:
            logger.error(f"❌ MCP failed: {e}")
            # Fallback to direct RAG answer if MCP fails
            answer = rag_context
            method_used = "RAG_FALLBACK"
            logger.info("⚠️ Using RAG answer as fallback")
        
        # Prepare debug information
        debug_info = {
            "rag_context_length": len(rag_context),
            "final_method": method_used,
            "question_length": len(question),
            "answer_length": len(answer) if answer else 0
        }
        
        logger.info(f"✅ Successfully processed question using {method_used}")
        return {
            "answer": answer, 
            "debug": debug_info
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
            "debug": "/debug",
            "test_logs": "/test-logs"
        }
    } 