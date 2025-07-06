# LangChain ChromaDB integration
import logging
from utils.database_config import create_vectorstore, should_persist_vectorstore

logger = logging.getLogger(__name__)

def get_chroma_client():
    """Get ChromaDB client for direct access"""
    from utils.database_config import create_chroma_client
    return create_chroma_client()

def get_vectorstore():
    """Get LangChain Chroma vectorstore with embeddings"""
    return create_vectorstore()

def add_documents_to_vectorstore(texts, metadatas=None):
    """Add documents to the vectorstore"""
    vectorstore = get_vectorstore()
    vectorstore.add_texts(texts, metadatas=metadatas)
    
    # Only persist if environment supports it
    if should_persist_vectorstore():
        try:
            vectorstore.persist()
            logger.info("💾 Persisted vectorstore to disk")
        except Exception as e:
            logger.warning(f"⚠️ Could not persist vectorstore: {e}")
    
    return vectorstore 