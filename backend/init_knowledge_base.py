#!/usr/bin/env python3
"""
Initialize the knowledge base with sample data for testing RAG functionality.
"""

import logging
import os
import shutil
from db.chroma_client import add_documents_to_vectorstore, get_vectorstore
from utils.environment import is_railway_environment, log_environment_info
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Get logger for this module
logger = logging.getLogger(__name__)

# Sample knowledge base data - longer texts for better chunking demonstration
sample_documents = [
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

# Enable metadata for better document organization
sample_metadatas = [
    {"source": "friends", "category": "person", "name": "Eric", "trait": "孝顺"},
    {"source": "gaming", "category": "skill", "name": "Eric", "game": "篮球", "comparison": "zzn"},
    {"source": "cars", "category": "comparison", "brand": "保时捷", "models": "911,718"},
    {"source": "friends", "category": "person", "name": "马棚", "skill": "驾驶"},
    {"source": "gaming", "category": "skill", "name": "Final", "title": "全能王"},
    {"source": "gaming", "category": "skill", "name": "小瘦哥", "weapon": "狙击枪"},
    {"source": "gaming", "category": "skill", "name": "段神", "specialty": "道具"},
    {"source": "work", "category": "person", "name": "吴非", "company": "亚马逊", "field": "AI"},
    {"source": "friends", "category": "person", "name": "abie", "nickname": "憋哥", "trait": "内向"},
    {"source": "friends", "category": "person", "name": "abie", "nickname": "憋哥", "trait": "能力强"},
]

def create_chunks_from_documents(documents, metadatas=None):
    """Create chunks from documents using text splitter"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,  # Smaller chunks for better retrieval
        chunk_overlap=50,  # Overlap to maintain context
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    all_chunks = []
    all_chunk_metadatas = []
    
    for i, doc in enumerate(documents):
        # Split the document into chunks
        chunks = text_splitter.split_text(doc)
        
        # Create metadata for each chunk
        base_metadata = metadatas[i] if metadatas and i < len(metadatas) else {"source": "unknown"}
        
        for j, chunk in enumerate(chunks):
            chunk_metadata = base_metadata.copy()
            chunk_metadata["chunk_index"] = str(j)
            chunk_metadata["total_chunks"] = str(len(chunks))
            chunk_metadata["original_document_index"] = str(i)
            
            # Ensure all metadata values are strings (ChromaDB requirement)
            for key, value in chunk_metadata.items():
                if not isinstance(value, (str, int, float, bool)) or value is None:
                    chunk_metadata[key] = str(value)
            
            all_chunks.append(chunk)
            all_chunk_metadatas.append(chunk_metadata)
    
    logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
    return all_chunks, all_chunk_metadatas

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
                # Create chunks from documents
                chunks, chunk_metadatas = create_chunks_from_documents(sample_documents, sample_metadatas)
                add_documents_to_vectorstore(chunks, chunk_metadatas)
                logger.info("✅ Knowledge base initialized successfully in Railway!")
                logger.info(f"Added {len(chunks)} chunks from {len(sample_documents)} documents to the vectorstore.")
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
            
            # Initialize fresh vectorstore with chunks
            chunks, chunk_metadatas = create_chunks_from_documents(sample_documents, sample_metadatas)
            add_documents_to_vectorstore(chunks, chunk_metadatas)
            logger.info("✅ Knowledge base initialized successfully!")
            logger.info(f"Added {len(chunks)} chunks from {len(sample_documents)} documents to the vectorstore.")
        
    except Exception as e:
        logger.error(f"❌ Error initializing knowledge base: {e}")
        logger.info("🔄 Continuing without knowledge base - will use RAG only")
        # Don't raise the exception - let the app continue without the knowledge base

if __name__ == "__main__":
    init_knowledge_base() 