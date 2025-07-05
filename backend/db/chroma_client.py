# LangChain ChromaDB integration
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

def get_chroma_client():
    """Get ChromaDB client for direct access"""
    return chromadb.Client()

def get_vectorstore():
    """Get LangChain Chroma vectorstore with embeddings"""
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # Create or load existing vectorstore
    vectorstore = Chroma(
        collection_name="knowledge_base",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )
    
    return vectorstore

def add_documents_to_vectorstore(texts, metadatas=None):
    """Add documents to the vectorstore"""
    vectorstore = get_vectorstore()
    vectorstore.add_texts(texts, metadatas=metadatas)
    vectorstore.persist()
    return vectorstore 