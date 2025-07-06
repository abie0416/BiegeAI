#!/usr/bin/env python3
"""
Initialize the knowledge base with sample data for testing RAG functionality.
"""

import logging
import os
import shutil
from db.chroma_client import add_documents_to_vectorstore, get_vectorstore
from utils.environment import is_railway_environment, log_environment_info

# Get logger for this module
logger = logging.getLogger(__name__)

# Sample knowledge base data
sample_documents = [
    "Eric是O孝子",
    "Eric投篮还可以，但是没有zzn准",
    "911比718牛逼",
    "马棚是老司机",
    "Final全能王",
    "小瘦哥玩鸟狙很厉害",
    "段神是道具王",
    "吴非是亚马逊AI王",
    "abie就是憋哥",
    "憋哥牛逼",
]

# sample_metadatas = [
#     {"source": "ai_basics", "category": "definition"},
#     {"source": "ai_basics", "category": "definition"},
#     {"source": "ai_basics", "category": "definition"},
#     {"source": "ai_basics", "category": "definition"},
#     {"source": "ai_basics", "category": "definition"},
#     {"source": "tools", "category": "framework"},
#     {"source": "tools", "category": "database"},
#     {"source": "techniques", "category": "methodology"}
# ]

def init_knowledge_base():
    """Initialize the knowledge base with sample data"""
    logger.info("Initializing knowledge base with sample data...")
    log_environment_info()
    
    try:
        chroma_db_path = "./chroma_db"
        
        if is_railway_environment():
            logger.info("🚂 Railway environment detected - using in-memory database")
            # Use in-memory database for Railway
            vectorstore = get_vectorstore()
            
            # Try to get collection count to see if it's empty
            try:
                collection = vectorstore._collection
                count = collection.count()
                logger.info(f"Existing database has {count} documents")
                
                if count > 0:
                    logger.info("✅ Knowledge base already initialized with data")
                    return
            except Exception as e:
                logger.info(f"No existing collection found or error accessing: {e}")
            
            # Try to add documents to existing or new collection
            try:
                add_documents_to_vectorstore(sample_documents)
                logger.info("✅ Knowledge base initialized successfully in Railway!")
                logger.info(f"Added {len(sample_documents)} documents to the vectorstore.")
                return
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize database in Railway: {e}")
                logger.info("🔄 Continuing without persistent knowledge base - will use RAG only")
                return
        else:
            # Local development - use file-based database
            vectorstore = get_vectorstore()
            
            # Try to get collection count to see if it's empty
            try:
                collection = vectorstore._collection
                count = collection.count()
                logger.info(f"Existing database has {count} documents")
                
                if count > 0:
                    logger.info("✅ Knowledge base already initialized with data")
                    return
            except Exception:
                logger.info("No existing collection found, will create new one")
            
            # Clear existing database if it exists but is empty or corrupted
            if os.path.exists(chroma_db_path):
                try:
                    logger.info("Clearing existing ChromaDB data...")
                    shutil.rmtree(chroma_db_path)
                    logger.info("✅ Existing database cleared")
                except PermissionError:
                    logger.warning("⚠️ Could not clear existing database (files in use), will try to add to existing")
            
            # Initialize fresh vectorstore
            add_documents_to_vectorstore(sample_documents)
            logger.info("✅ Knowledge base initialized successfully!")
            logger.info(f"Added {len(sample_documents)} documents to the vectorstore.")
        
    except Exception as e:
        logger.error(f"❌ Error initializing knowledge base: {e}")
        logger.info("🔄 Continuing without knowledge base - will use RAG only")
        # Don't raise the exception - let the app continue without the knowledge base

if __name__ == "__main__":
    init_knowledge_base() 