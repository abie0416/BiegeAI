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

try:
    from services.llamaindex_graphrag_service import get_llamaindex_graphrag_service
except ImportError:
    # Fallback for Railway deployment
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from services.llamaindex_graphrag_service import get_llamaindex_graphrag_service
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

# Suppress verbose LlamaIndex debug logs
logging.getLogger("llama_index.core.node_parser.node_utils").setLevel(logging.WARNING)
logging.getLogger("llama_index.core.indices.knowledge_graph.base").setLevel(logging.WARNING)
logging.getLogger("llama_index.core.indices.vector_store.base").setLevel(logging.WARNING)
logging.getLogger("llama_index.core.retrievers").setLevel(logging.WARNING)
logging.getLogger("llama_index.core.query_engine").setLevel(logging.WARNING)

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
        {"content": "Eric是O孝子，他非常孝顺父母，经常帮助家里做家务。Eric在朋友中很受欢迎，大家都喜欢和他一起玩。"},
        {"content": "Eric投篮还可以，但是没有zzn准。Eric在篮球场上表现不错，但是zzn的投篮技术更加精准，命中率更高。"},
        {"content": "911比718牛逼，保时捷911是经典跑车，性能卓越。718虽然也不错，但在很多方面都不如911出色。"},
        {"content": "马棚是老司机，开车技术很好，经验丰富。他经常开车带大家出去玩，大家都觉得坐他的车很安全。"},
        {"content": "Final全能王，在游戏Final中表现非常出色，各种角色都能玩得很好。他是大家公认的游戏高手。"},
        {"content": "小瘦哥玩鸟狙很厉害，在射击游戏中特别擅长使用狙击枪。他的瞄准技术非常精准，经常能一枪爆头。"},
        {"content": "段神是道具王，在游戏中特别擅长使用各种道具。他对游戏道具的理解很深，总能找到最有效的使用方法。"},
        {"content": "吴非是亚马逊AI王，在亚马逊工作，专门负责AI相关项目。他在人工智能领域很有经验，技术能力很强。"},
        {"content": "abie就是憋哥，这是他的外号。abie性格比较内向，不太爱说话，所以大家叫他憋哥。"},
        {"content": "憋哥牛逼，虽然abie比较内向，但是他的能力很强，在很多方面都很出色，大家都很佩服他。"},
    ]
    
    try:
        from services.google_sheets import sheets_service
        sheets_docs = sheets_service.get_documents()
        if sheets_docs:
            logger.info(f"✅ Successfully fetched {len(sheets_docs)} documents from Google Sheets")
            return sheets_docs
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
        
        # Get GCP configuration from environment
        gcp_bucket_name = os.getenv("GCP_BUCKET_NAME")
        gcp_project_id = os.getenv("GCP_PROJECT_ID")
        
        # Initialize LlamaIndex GraphRAG with GCP support
        try:
            llamaindex_graphrag = get_llamaindex_graphrag_service(
                google_api_key=GEMINI_API_KEY,
                gcp_bucket_name=gcp_bucket_name,
                gcp_project_id=gcp_project_id
            )
            
            # Try to initialize from GCP first
            if gcp_bucket_name and gcp_project_id:
                logger.info("🔄 Attempting to initialize RAG from GCP...")
                if llamaindex_graphrag.initialize_from_gcp():
                    logger.info("✅ RAG knowledge base initialized from GCP successfully")
                    return True
                else:
                    logger.warning("⚠️ Failed to initialize from GCP, trying local storage...")
            
            # Try to load from local storage
            if llamaindex_graphrag.load_index():
                logger.info("✅ RAG knowledge base loaded from local storage")
                return True
            
            # If no existing index found, don't rebuild automatically
            logger.warning("⚠️ No existing RAG index found in GCP or local storage")
            logger.info("💡 Use the /rebuild-rag endpoint to build the initial knowledge base")
            return False
                
        except Exception as e:
            logger.error(f"❌ LlamaIndex GraphRAG initialization failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing RAG knowledge base: {e}")
        return False

# Initialize RAG knowledge base on startup
rag_initialized = initialize_rag_knowledge_base()

def get_rag_context(question: str) -> str:
    """Fetch RAG context using GraphRAG"""
    try:
        logger.info("🔍 Fetching RAG context with GraphRAG...")
        
        if not GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY not set, cannot use RAG")
            return "RAG not available - API key not configured."
        
        # Use LlamaIndex GraphRAG
        try:
            llamaindex_graphrag = get_llamaindex_graphrag_service(GEMINI_API_KEY)
            documents = llamaindex_graphrag.hybrid_search(question, k=5)
            
            if documents:
                # Format documents into context
                context_parts = []
                logger.info(f"📚 Formatting {len(documents)} retrieved documents into context:")
                
                for i, doc in enumerate(documents):
                    source_info = f" ({doc['source']})" if 'source' in doc else ""
                    score_info = f" (relevance: {doc['score']:.3f})" if doc['score'] is not None else ""
                    context_parts.append(f"Document {i+1}{source_info}{score_info}:\n{doc['content']}")
                    
                    # Log each document being added to context
                    logger.info(f"   📄 Document {i+1}:")
                    logger.info(f"      - Source: {doc.get('source', 'unknown')}")
                    logger.info(f"      - Score: {doc.get('score', 'N/A')}")
                    logger.info(f"      - Content length: {len(doc['content'])} characters")
                    logger.info(f"      - Content preview: {doc['content'][:200]}...")
                
                context = "\n\n".join(context_parts)
                logger.info(f"✅ GraphRAG context fetched: {len(context)} characters from {len(documents)} documents")
                logger.info(f"📋 Final context preview: {context[:300]}...")
                return context
        except Exception as e:
            logger.error(f"❌ LlamaIndex GraphRAG failed: {e}")
        
        logger.warning("⚠️ No documents retrieved from RAG system")
        return "No relevant documents found in knowledge base."
        
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
        
        # Log the combined context being sent to the model
        logger.info(f"📤 Sending combined context to model:")
        logger.info(f"   - Question: {question}")
        logger.info(f"   - Conversation context length: {len(conversation_context)} characters")
        logger.info(f"   - RAG context length: {len(rag_context)} characters")
        logger.info(f"   - Combined context length: {len(combined_context)} characters")
        logger.info(f"   - Combined context preview: {combined_context[:500]}...")
        
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
            "rag_knowledge_base": "Initialized" if rag_initialized else "Not initialized - use /rebuild-rag to build"
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
    """Rebuild RAG knowledge base (both Advanced RAG and GraphRAG) and return results"""
    logger.info("📥 Rebuild RAG endpoint accessed")
    
    try:
        # Ensure environment variables are loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get documents from Google Sheets with fallback
        documents = get_documents_from_sheets_with_fallback()

        
        total_documents = len(documents)
        
        # Initialize results
        results = {
            "llamaindex_graphrag": {"success": False, "nodes_created": 0, "edges_created": 0}
        }
        

        

        
        # Rebuild LlamaIndex GraphRAG
        logger.info("🔨 Rebuilding LlamaIndex GraphRAG knowledge base...")
        try:
            if not GEMINI_API_KEY:
                logger.warning("⚠️ GEMINI_API_KEY not set, skipping LlamaIndex GraphRAG rebuild")
                results["llamaindex_graphrag"] = {"success": False, "nodes_created": 0, "edges_created": 0, "error": "GEMINI_API_KEY not configured"}
            else:
                # Get GCP configuration
                gcp_bucket_name = os.getenv("GCP_BUCKET_NAME")
                gcp_project_id = os.getenv("GCP_PROJECT_ID")
                
                # Get LlamaIndex GraphRAG service with GCP support
                llamaindex_graphrag = get_llamaindex_graphrag_service(
                    google_api_key=GEMINI_API_KEY,
                    gcp_bucket_name=gcp_bucket_name,
                    gcp_project_id=gcp_project_id
                )
                
                # Build knowledge graph
                success = llamaindex_graphrag.build_knowledge_graph(documents)
                
                if success:
                    # Save to both local storage and GCP
                    save_success = llamaindex_graphrag.save_index()
                    
                    # Get graph statistics
                    stats = llamaindex_graphrag.get_graph_statistics()
                    results["llamaindex_graphrag"] = {
                        "success": True, 
                        "nodes_created": stats.get("total_nodes", 0),
                        "edges_created": stats.get("total_edges", 0),
                        "node_types": stats.get("node_types", {}),
                        "relationship_types": stats.get("relationship_types", {}),
                        "saved_locally": save_success,
                        "saved_to_gcp": gcp_bucket_name is not None and gcp_project_id is not None
                    }
                    logger.info(f"✅ LlamaIndex GraphRAG rebuild completed successfully. {stats.get('total_nodes', 0)} nodes, {stats.get('total_edges', 0)} edges.")
                    if gcp_bucket_name:
                        logger.info(f"📤 Index saved to GCP bucket: {gcp_bucket_name}")
                else:
                    results["llamaindex_graphrag"] = {"success": False, "nodes_created": 0, "edges_created": 0, "error": "LlamaIndex GraphRAG build process failed"}
                    
        except Exception as e:
            logger.error(f"❌ Error rebuilding LlamaIndex GraphRAG: {e}")
            results["llamaindex_graphrag"] = {"success": False, "nodes_created": 0, "edges_created": 0, "error": str(e)}
        
        # Update global RAG status
        global rag_initialized
        rag_initialized = results["llamaindex_graphrag"]["success"]
        
        # Prepare response
        llamaindex_success = results["llamaindex_graphrag"]["success"]
        
        # Create detailed message
        details_parts = []
        if llamaindex_success:
            details_parts.append(f"LlamaIndex GraphRAG: {results['llamaindex_graphrag']['nodes_created']} nodes, {results['llamaindex_graphrag']['edges_created']} edges")
        
        if details_parts:
            details = f"Successfully rebuilt: {'; '.join(details_parts)} from {total_documents} source documents"
        else:
            details = "RAG rebuild failed"
        
        return {
            "success": llamaindex_success,
            "message": f"RAG knowledge base rebuild {'completed' if llamaindex_success else 'failed'}",
            "total_sample_documents": total_documents,
            "details": details,
            "llamaindex_graphrag": results["llamaindex_graphrag"]
        }
            
    except Exception as e:
        error_msg = f"❌ Error rebuilding RAG knowledge base: {str(e)}"
        logger.error(f"❌ Error in rebuild_rag endpoint: {e}")
        return {
            "success": False,
            "message": error_msg,
            "total_sample_documents": "unknown",
            "error": str(e)
        }

@app.get("/llamaindex-graph-stats")
async def get_llamaindex_graph_stats():
    """Get LlamaIndex GraphRAG knowledge graph statistics"""
    logger.info("📥 LlamaIndex Graph stats endpoint accessed")
    
    try:
        if not GEMINI_API_KEY:
            return {"error": "GEMINI_API_KEY not configured"}
        
        llamaindex_graphrag = get_llamaindex_graphrag_service(GEMINI_API_KEY)
        stats = llamaindex_graphrag.get_graph_statistics()
        
        return {
            "success": True,
            "graph_statistics": stats,
            "message": f"LlamaIndex knowledge graph has {stats.get('total_nodes', 0)} nodes and {stats.get('total_edges', 0)} edges"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting LlamaIndex graph stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/llamaindex-graph-search")
async def llamaindex_graph_search(request: Request):
    """Perform LlamaIndex GraphRAG search"""
    logger.info("📥 LlamaIndex Graph search endpoint accessed")
    
    try:
        data = await request.json()
        query = data.get("query")
        k = data.get("k", 5)
        
        if not query:
            return {"error": "Query parameter is required"}
        
        if not GEMINI_API_KEY:
            return {"error": "GEMINI_API_KEY not configured"}
        
        llamaindex_graphrag = get_llamaindex_graphrag_service(GEMINI_API_KEY)
        results = llamaindex_graphrag.hybrid_search(query, k=k)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in LlamaIndex graph search: {e}")
        return {
            "success": False,
            "error": str(e)
        }



 