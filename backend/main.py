import os
import logging
import sys

# Set protobuf environment variable BEFORE any other imports
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent.gemini_client import GeminiClient
from agent.mcp import run_mcp
from services.advanced_rag_service import get_advanced_rag_service
from conversation_manager import conversation_manager
from utils.environment import log_environment_info, get_environment_info

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
log_environment_info()

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

def get_documents_from_sheets_with_fallback():
    """Get documents from Google Sheets with fallback to hardcoded documents"""
    fallback_documents = [
        "Eric是O孝子，他非常孝顺父母，经常帮助家里做家务。Eric在朋友中很受欢迎，大家都喜欢和他一起玩。",
        "Eric投篮还可以，但是没有zzn准。Eric在篮球场上表现不错，但是zzn的投篮技术更加精准，命中率更高。",
        "911比718牛逼，保时捷911是经典跑车，性能卓越。718虽然也不错，但在很多方面都不如911出色。",
        "马棚是老司机，开车技术很好，经验丰富。他经常开车带大家出去玩，大家都觉得坐他的车很安全。",
        "Final全能王，在游戏Final中表现非常出色，各种角色都能玩得很好。他是大家公认的游戏高手。",
        "小瘦哥玩鸟狙很厉害，在射击游戏中特别擅长使用狙击枪。他的瞄准技术非常精准，经常能一枪爆头。",
        "段神是道具王，在游戏中特别擅长使用各种道具。他对游戏道具的理解很深，总能找到最有效的使用方法。",
        "吴非是亚马逊AI王，在亚马逊工作，专门负责AI相关项目。他在人工智能领域很有经验，技术能力很强。",
        "abie就是憋哥，这是他的外号。abie性格比较内向，不太爱说话，所以大家叫他憋哥。",
        "憋哥牛逼，虽然abie比较内向，但是他的能力很强，在很多方面都很出色，大家都很佩服他。",
    ]
    
    try:
        from services.google_sheets import sheets_service
        sheets_docs = sheets_service.get_documents()
        if sheets_docs:
            # Extract content from documents
            documents = [doc.get('content', '') for doc in sheets_docs if doc.get('content')]
            logger.info(f"✅ Successfully fetched {len(documents)} documents from Google Sheets")
            return documents
        else:
            logger.warning("⚠️ No documents found in Google Sheets, using fallback data")
            return fallback_documents
    except Exception as e:
        logger.warning(f"⚠️ Could not fetch from Google Sheets: {e}, using fallback data")
        return fallback_documents

def initialize_rag_knowledge_base():
    """Initialize RAG knowledge base on startup"""
    try:
        logger.info("🚀 Initializing RAG knowledge base...")
        
        if not GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY not set, skipping RAG initialization")
            return False
        
        # Get documents from Google Sheets with fallback
        documents = get_documents_from_sheets_with_fallback()
        
        if not documents:
            logger.warning("⚠️ No documents available for RAG initialization")
            return False
        
        # Get advanced RAG service
        advanced_rag = get_advanced_rag_service(GEMINI_API_KEY)
        
        # Build advanced index
        success = advanced_rag.build_advanced_index(documents)
        
        if success:
            logger.info(f"✅ RAG knowledge base initialized successfully with {len(documents)} documents")
            return True
        else:
            logger.error("❌ Failed to initialize RAG knowledge base")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing RAG knowledge base: {e}")
        return False

# Initialize RAG knowledge base on startup
rag_initialized = initialize_rag_knowledge_base()

def get_rag_context(question: str) -> str:
    """Always fetch RAG context for the question using advanced RAG service"""
    try:
        logger.info("🔍 Fetching RAG context with advanced service...")
        
        if not GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY not set, cannot use advanced RAG")
            return "Advanced RAG not available - API key not configured."
        
        # Get advanced RAG service
        advanced_rag = get_advanced_rag_service(GEMINI_API_KEY)
        
        # Get contextual documents with compression
        documents = advanced_rag.query_with_contextual_compression(question, k=5)
        
        if not documents:
            logger.warning("⚠️ No documents retrieved from advanced RAG")
            return "No relevant documents found in knowledge base."
        
        # Format documents into context
        context_parts = []
        for i, doc in enumerate(documents):
            score_info = f" (relevance: {doc['score']:.3f})" if doc['score'] is not None else ""
            context_parts.append(f"Document {i+1}{score_info}:\n{doc['content']}")
        
        context = "\n\n".join(context_parts)
        logger.info(f"✅ Advanced RAG context fetched: {len(context)} characters from {len(documents)} documents")
        return context
        
    except Exception as e:
        logger.error(f"❌ Advanced RAG context fetch failed: {e}")
        return f"Advanced RAG Error: {str(e)}"

@app.get("/")
async def root():
    logger.info("📥 Root endpoint accessed")
    return {
        "message": "Welcome to Biege AI Backend!",
        "status": "running",
        "debug": {
            "api_key_configured": GEMINI_API_KEY is not None,
            "gemini_client_ready": gemini_client is not None,
            "rag_initialized": rag_initialized,
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
        session_id = data.get("session_id")  # Optional session ID from frontend
        
        if not question:
            logger.warning("⚠️ No question provided in request")
            return {"answer": "Please provide a question.", "debug": {"error": "no_question_provided"}}
        
        logger.info(f"🤔 Processing question: {question[:50]}...")
        
        # Step 1: Manage conversation session
        session_id = conversation_manager.get_or_create_session(session_id)
        logger.info(f"📝 Using conversation session: {session_id}")
        
        # Step 2: Get conversation context
        conversation_context, context_debug = conversation_manager.get_conversation_context(session_id, question)
        logger.info(f"💬 Conversation context: {context_debug['message_count']} messages, {context_debug['context_length']} chars")
        
        # Step 3: Always fetch RAG context
        rag_context = get_rag_context(question)
        
        # Step 4: Combine RAG and conversation context
        combined_context = ""
        if conversation_context:
            combined_context += f"Previous conversation:\n{conversation_context}\n\n"
        if rag_context:
            combined_context += f"Relevant knowledge:\n{rag_context}\n\n"
        
        # Step 5: Run MCP with combined context
        try:
            answer = run_mcp(question, gemini_client, combined_context)
            logger.info(f"✅ MCP completed successfully")
            method_used = "MCP_WITH_COMBINED_CONTEXT"
        except Exception as e:
            logger.error(f"❌ MCP failed: {e}")
            # Fallback to direct RAG answer if MCP fails
            answer = rag_context
            method_used = "RAG_FALLBACK"
            logger.info("⚠️ Using RAG answer as fallback")
        
        # Step 6: Store messages in conversation history
        conversation_manager.add_message(session_id, "user", question)
        conversation_manager.add_message(session_id, "agent", answer)
        
        # Step 7: Prepare debug information
        debug_info = {
            "session_id": session_id,
            "rag_context_length": len(rag_context),
            "conversation_context_length": context_debug['context_length'],
            "combined_context_length": len(combined_context),
            "final_method": method_used,
            "question_length": len(question),
            "answer_length": len(answer) if answer else 0,
            "conversation_stats": context_debug
        }
        
        logger.info(f"✅ Successfully processed question using {method_used}")
        return {
            "answer": answer,
            "session_id": session_id,
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
            "rag_initialized": rag_initialized,
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
            "gemini_client": "Ready" if gemini_client else "Not ready",
            "rag_knowledge_base": "Initialized" if rag_initialized else "Not initialized"
        },
        "conversation_manager": {
            "total_sessions": len(conversation_manager.sessions),
            "max_sessions": conversation_manager.max_sessions,
            "session_timeout_minutes": conversation_manager.session_timeout_minutes
        },
        "environment": get_environment_info(),
        "endpoints": {
            "root": "/",
            "health": "/health",
            "ask": "/ask (POST)",
            "debug": "/debug",
            "test_logs": "/test-logs",
            "conversations": "/conversations (GET)",
            "conversation_stats": "/conversation-stats (GET)",
            "rebuild_rag": "/rebuild-rag (POST) - rebuilds Advanced RAG knowledge base"
        }
    }

@app.get("/conversations")
async def get_conversations():
    """Get all conversation sessions"""
    logger.info("📥 Conversations endpoint accessed")
    return conversation_manager.get_all_sessions_stats()

@app.get("/conversation-stats")
async def get_conversation_stats():
    """Get conversation manager statistics"""
    logger.info("📥 Conversation stats endpoint accessed")
    return {
        "total_sessions": len(conversation_manager.sessions),
        "max_sessions": conversation_manager.max_sessions,
        "session_timeout_minutes": conversation_manager.session_timeout_minutes,
        "max_messages_per_session": conversation_manager.max_messages_per_session,
        "max_context_length": conversation_manager.max_context_length,
        "consecutive_timeout_minutes": conversation_manager.consecutive_timeout_minutes
    }

@app.post("/rebuild-rag")
async def rebuild_rag():
    """Rebuild Advanced RAG knowledge base and return results"""
    logger.info("📥 Rebuild RAG endpoint accessed")
    
    try:
        # Ensure environment variables are loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get documents from Google Sheets with fallback
        documents = get_documents_from_sheets_with_fallback()
        from db.chroma_client import get_vectorstore
        
        total_documents = len(documents)
        
        # Initialize results
        results = {
            "advanced_rag": {"success": False, "documents_embedded": 0}
        }
        
        # Rebuild Advanced RAG
        logger.info("🔨 Rebuilding Advanced RAG knowledge base...")
        try:
            if not GEMINI_API_KEY:
                logger.warning("⚠️ GEMINI_API_KEY not set, skipping Advanced RAG rebuild")
                results["advanced_rag"] = {"success": False, "documents_embedded": 0, "error": "GEMINI_API_KEY not configured"}
            else:
                # Clear existing vectorstore completely
                logger.info("🗑️ Clearing existing vectorstore completely...")
                try:
                    import chromadb
                    import time
                    # Use in-memory client for consistency
                    client = chromadb.Client()
                    
                    # Check if collection exists before deleting
                    try:
                        existing_collection = client.get_collection("knowledge_base")
                        logger.info("🗑️ Found existing collection, deleting...")
                        client.delete_collection("knowledge_base")
                        logger.info("✅ Existing collection deleted completely")
                    except:
                        logger.info("ℹ️ No existing collection found, will create new one")
                    
                    # Small delay to ensure deletion is complete
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"⚠️ Could not delete existing collection: {e}")
                
                # Get advanced RAG service
                advanced_rag = get_advanced_rag_service(GEMINI_API_KEY)
                
                # Build advanced index
                success = advanced_rag.build_advanced_index(documents)
                
                if success:
                    # Verify rebuild by counting documents
                    try:
                        # Get fresh vectorstore to count documents
                        fresh_vectorstore = get_vectorstore()
                        collection = fresh_vectorstore._collection
                        count = collection.count()
                        results["advanced_rag"] = {"success": True, "documents_embedded": count}
                        logger.info(f"✅ Advanced RAG rebuild completed successfully. {count} documents embedded.")
                        
                        # Update global RAG status
                        global rag_initialized
                        rag_initialized = True
                        
                    except Exception as e:
                        logger.error(f"❌ Error counting documents after rebuild: {e}")
                        results["advanced_rag"] = {"success": False, "documents_embedded": 0, "error": str(e)}
                else:
                    results["advanced_rag"] = {"success": False, "documents_embedded": 0, "error": "Advanced RAG build process failed"}
                    
        except Exception as e:
            logger.error(f"❌ Error rebuilding Advanced RAG: {e}")
            results["advanced_rag"] = {"success": False, "documents_embedded": 0, "error": str(e)}
        
        # Prepare response
        advanced_rag_success = results["advanced_rag"]["success"]
        advanced_rag_count = results["advanced_rag"]["documents_embedded"]
        
        # Create detailed message
        if advanced_rag_success:
            details = f"Successfully rebuilt Advanced RAG: {advanced_rag_count} chunks with AI metadata from {total_documents} documents"
        else:
            details = f"Advanced RAG rebuild failed"
            if "error" in results["advanced_rag"]:
                details += f": {results['advanced_rag']['error']}"
        
        return {
            "success": advanced_rag_success,
            "message": f"Advanced RAG knowledge base rebuild {'completed' if advanced_rag_success else 'failed'}",
            "documents_embedded": advanced_rag_count,
            "total_sample_documents": total_documents,
            "details": details,
            "advanced_rag": results["advanced_rag"]
        }
            
    except Exception as e:
        error_msg = f"❌ Error rebuilding RAG knowledge base: {str(e)}"
        logger.error(f"❌ Error in rebuild_rag endpoint: {e}")
        return {
            "success": False,
            "message": error_msg,
            "documents_embedded": 0,
            "total_sample_documents": "unknown",
            "error": str(e)
        }



 