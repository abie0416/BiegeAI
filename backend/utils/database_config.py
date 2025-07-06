import chromadb
import logging
import os
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr
from .environment import is_railway_environment

logger = logging.getLogger(__name__)

def create_embeddings():
    """Create Google Generative AI embeddings instance"""
    google_api_key = os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=SecretStr(google_api_key)
    )

def create_vectorstore(collection_name: str = "knowledge_base", persist_directory: str = "./chroma_db"):
    """Create ChromaDB vectorstore with in-memory configuration"""
    try:
        logger.info("🔧 Creating embeddings...")
        embeddings = create_embeddings()
        logger.info("✅ Embeddings created successfully")
        
        logger.info("💾 Using in-memory ChromaDB (suitable for Railway deployment)")
        # Always use in-memory database for consistency and Railway deployment
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            client=chromadb.Client()  # In-memory client
        )
        
        logger.info("✅ Vectorstore created successfully")
        return vectorstore
        
    except Exception as e:
        logger.error(f"❌ Error creating vectorstore: {e}")
        raise

def get_database_config_info() -> dict:
    """Get database configuration information"""
    return {
        "is_railway": is_railway_environment(),
        "is_readonly": is_railway_environment(),
        "should_persist": False,  # Always in-memory
        "storage_type": "in-memory",
        "collection_name": "knowledge_base",
        "persist_directory": "N/A (in-memory)"
    } 