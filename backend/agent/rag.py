# LangChain RAG implementation
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from db.chroma_client import get_vectorstore
import logging
from typing import List, Tuple, Dict
import numpy as np

# Get logger for this module
logger = logging.getLogger(__name__)

# Configuration for RAG filtering
SIMILARITY_THRESHOLD = 1.5  # lower is better
MIN_DOCUMENTS = 1  # Minimum documents to return even if below threshold
MAX_DOCUMENTS = 10  # Maximum documents to retrieve initially

def fetch_documents_with_scores(question, k=MAX_DOCUMENTS) -> List[Tuple[Document, float]]:
    """Fetch relevant documents with similarity scores"""
    try:
        logger.info(f"[DEBUG] RAG: Fetching documents with scores for question: {question}")
        
        # Get vectorstore
        vectorstore = get_vectorstore()
        logger.info(f"[DEBUG] RAG: Got vectorstore")
        
        # Get relevant documents with scores using similarity search
        docs_and_scores = vectorstore.similarity_search_with_score(question, k=k)
        logger.info(f"[DEBUG] RAG: Retrieved {len(docs_and_scores)} documents with scores")
        
        # Log all documents and their scores
        for i, (doc, score) in enumerate(docs_and_scores):
            logger.info(f"[DEBUG] RAG: Document {i+1} (score: {score:.3f}): {doc.page_content[:100]}...")
        
        return docs_and_scores
        
    except Exception as e:
        logger.error(f"[DEBUG] RAG Error in fetch_documents_with_scores: {str(e)}")
        return []

def filter_documents_by_similarity(docs_and_scores: List[Tuple[Document, float]], 
                                 threshold: float = SIMILARITY_THRESHOLD,
                                 min_docs: int = MIN_DOCUMENTS) -> List[Tuple[Document, float]]:
    """Filter documents based on similarity threshold"""
    if not docs_and_scores:
        return []
    
    # For cosine distance, scores are 0-1 where lower is better (more similar)
    logger.info(f"[DEBUG] RAG: Using cosine distance filtering (lower is better)")
    # Filter by <= threshold (lower scores are more similar)
    filtered_docs = [(doc, score) for doc, score in docs_and_scores if score <= threshold]
    # If too few documents, include more (take first min_docs)
    if len(filtered_docs) < min_docs and len(docs_and_scores) > 0:
        logger.info(f"[DEBUG] RAG: Only {len(filtered_docs)} documents below distance threshold {threshold}, including {min_docs - len(filtered_docs)} more")
        filtered_docs = docs_and_scores[:min_docs]
    
    logger.info(f"[DEBUG] RAG: Filtered to {len(filtered_docs)} documents (threshold: {threshold})")
    for i, (doc, score) in enumerate(filtered_docs):
        logger.info(f"[DEBUG] RAG: Filtered Document {i+1} (score: {score:.3f}): {doc.page_content[:50]}...")
    
    return filtered_docs

def fetch_documents(question, k=MAX_DOCUMENTS):
    """Fetch relevant documents from the knowledge base with similarity filtering"""
    try:
        logger.info(f"[DEBUG] RAG: Fetching documents for question: {question}")
        
        # Get documents with scores
        docs_and_scores = fetch_documents_with_scores(question, k=MAX_DOCUMENTS)
        
        if not docs_and_scores:
            logger.warning("[DEBUG] RAG: No documents retrieved")
            return "No relevant documents found in knowledge base. Please provide a general answer based on your training data."
        
        # Filter by similarity threshold
        filtered_docs = filter_documents_by_similarity(docs_and_scores, SIMILARITY_THRESHOLD, MIN_DOCUMENTS)
        
        if not filtered_docs:
            logger.warning(f"[DEBUG] RAG: No documents met similarity threshold {SIMILARITY_THRESHOLD}")
            return "No highly relevant documents found in knowledge base. Please provide a general answer based on your training data."
        
        # Format documents into context
        context_parts = []
        for i, (doc, score) in enumerate(filtered_docs):
            logger.info(f"[DEBUG] RAG: Using Document {i+1} (score: {score:.3f}): {doc.page_content[:100]}...")
            context_parts.append(f"Document {i+1} (relevance: {score:.3f}):\n{doc.page_content}")
        
        context = "\n\n".join(context_parts)
        logger.info(f"[DEBUG] RAG: Final context length: {len(context)} characters")
        return context
        
    except Exception as e:
        logger.error(f"[DEBUG] RAG Error: {str(e)}")
        # Return a fallback message instead of error
        logger.info("[DEBUG] RAG: Using fallback context due to error")
        return "No specific knowledge base context available. Please provide a general answer based on your training data."

def run_rag(question, gemini_client):
    """Run RAG (Retrieval-Augmented Generation) pipeline with similarity filtering"""
    try:
        logger.info(f"[DEBUG] RAG: Starting with question: {question}")
        
        # Get vectorstore
        vectorstore = get_vectorstore()
        logger.info(f"[DEBUG] RAG: Got vectorstore")
        
        # Get relevant documents with scores using the new filtering approach
        docs_and_scores = fetch_documents_with_scores(question, k=MAX_DOCUMENTS)
        
        if not docs_and_scores:
            logger.warning("[DEBUG] RAG: No documents retrieved for QA chain")
            return "No relevant documents found in knowledge base to answer this question."
        
        # Filter by similarity threshold
        filtered_docs = filter_documents_by_similarity(docs_and_scores, SIMILARITY_THRESHOLD, MIN_DOCUMENTS)
        
        if not filtered_docs:
            logger.warning(f"[DEBUG] RAG: No documents met similarity threshold {SIMILARITY_THRESHOLD} for QA chain")
            return "No highly relevant documents found in knowledge base to answer this question."
        
        # Extract just the documents for the QA chain
        docs = [doc for doc, score in filtered_docs]
        
        for i, (doc, score) in enumerate(filtered_docs):
            logger.info(f"[DEBUG] RAG: QA Document {i+1} (score: {score:.3f}): {doc.page_content[:100]}...")
        
        # Create RAG chain
        template = """Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Answer:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Create retrieval QA chain with filtered documents
        qa_chain = RetrievalQA.from_chain_type(
            llm=gemini_client.llm,
            chain_type="map_reduce",
            retriever=vectorstore.as_retriever(search_kwargs={"k": len(docs)}),
            chain_type_kwargs={"prompt": prompt}
        )
        
        # Get answer
        logger.info(f"[DEBUG] RAG: Invoking QA chain with {len(docs)} filtered documents...")
        result = qa_chain.invoke({"query": question})
        answer = result["result"]
        logger.info(f"[DEBUG] RAG: QA chain returned: {answer}")
        return answer
        
    except Exception as e:
        logger.error(f"[DEBUG] RAG Error: {str(e)}")
        return f"[RAG Error] {str(e)}" 