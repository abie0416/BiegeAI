# LangChain ChromaDB integration
import logging
from utils.database_config import create_vectorstore

logger = logging.getLogger(__name__)

def get_vectorstore():
    """Get LangChain Chroma vectorstore with embeddings"""
    
    try:
        logger.info("🔧 Creating vectorstore...")
        vectorstore = create_vectorstore()
        logger.info("✅ Vectorstore created successfully")
        return vectorstore
    except Exception as e:
        logger.error(f"❌ Error creating vectorstore: {e}")
        raise

 