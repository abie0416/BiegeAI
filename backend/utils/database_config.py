import chromadb
import logging
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from .environment import is_railway_environment, is_readonly_environment

logger = logging.getLogger(__name__)

def create_embeddings():
    """Create HuggingFace embeddings instance"""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )

def create_chroma_client():
    """Create appropriate ChromaDB client based on environment"""
    if is_railway_environment():
        logger.info("🚂 Railway environment detected - using in-memory ChromaDB client")
        return chromadb.Client()  # In-memory client
    else:
        logger.info("💻 Local environment - using persistent ChromaDB client")
        return chromadb.Client()

def create_vectorstore(collection_name: str = "knowledge_base", persist_directory: str = "./chroma_db"):
    """Create ChromaDB vectorstore with appropriate configuration for environment"""
    embeddings = create_embeddings()
    
    if is_railway_environment():
        logger.info("🚂 Railway environment detected - using in-memory ChromaDB")
        # Use in-memory database for Railway
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            client=chromadb.Client()  # In-memory client
        )
    else:
        logger.info("💻 Local environment - using persistent ChromaDB")
        # Use persistent database for local development
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_directory
        )
    
    return vectorstore

def should_persist_vectorstore() -> bool:
    """Determine if vectorstore should be persisted based on environment"""
    return not is_railway_environment()

def get_database_config_info() -> dict:
    """Get database configuration information"""
    return {
        "is_railway": is_railway_environment(),
        "is_readonly": is_readonly_environment(),
        "should_persist": should_persist_vectorstore(),
        "storage_type": "in-memory" if is_railway_environment() else "persistent",
        "collection_name": "knowledge_base",
        "persist_directory": "./chroma_db" if not is_railway_environment() else "N/A"
    } 