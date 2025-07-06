"""
Advanced RAG service using LangChain for automatic chunking, analysis, and embedding
"""
import logging
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from db.chroma_client import get_vectorstore

# Get logger for this module
logger = logging.getLogger(__name__)

class AdvancedRAGService:
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.vectorstore = None
        self.text_splitter = None
        self.embeddings = None
        
    def setup_components(self):
        """Setup advanced RAG components"""
        try:
            # Advanced text splitter with smart chunking
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
                is_separator_regex=False
            )
            
            # Google Generative AI embeddings
            from pydantic import SecretStr
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=SecretStr(self.google_api_key)
            )
            
            # Get vectorstore
            try:
                self.vectorstore = get_vectorstore()
                logger.info("✅ Vectorstore initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize vectorstore: {e}")
                raise Exception(f"Vectorstore initialization failed: {e}")
            
            logger.info("✅ Advanced RAG components setup successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up advanced RAG components: {e}")
            return False
    
    def create_smart_chunks(self, documents: List[str]) -> List[Document]:
        """Create smart chunks with automatic metadata generation"""
        try:
            logger.info("🔨 Creating smart chunks with automatic processing...")
            
            if not self.text_splitter:
                logger.error("❌ Text splitter not initialized")
                return []
            
            # Create base documents
            base_docs = []
            for i, content in enumerate(documents):
                if content.strip():
                    doc = Document(
                        page_content=content.strip(),
                        metadata={
                            "source": "google_sheets",
                            "document_id": i,
                            "content_length": len(content)
                        }
                    )
                    base_docs.append(doc)
            
            # Smart chunking
            chunks = self.text_splitter.split_documents(base_docs)
            
            # Add chunk metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk.page_content)
                })
            
            logger.info(f"✅ Created {len(chunks)} smart chunks from {len(documents)} documents")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error creating smart chunks: {e}")
            return []
    
    def generate_metadata_with_ai(self, content: str) -> Dict:
        """Generate metadata using AI analysis"""
        try:
            # Create a temporary LLM for metadata generation
            from agent.gemini_client import GeminiClient
            gemini_client = GeminiClient(self.google_api_key)
            
            prompt = PromptTemplate(
                input_variables=["content"],
                template="""
                Analyze the following text and extract structured metadata. Return a JSON object with these fields:
                - source: category like "friends", "gaming", "work", "cars", "personal", etc.
                - category: type like "person", "skill", "comparison", "event", "fact", etc.
                - name: person name if mentioned
                - trait: characteristic or skill mentioned
                - game: game name if mentioned
                - sentiment: positive, negative, or neutral
                - language: primary language (zh, en, etc.)
                
                Text: {content}
                
                Return only the JSON object, no other text.
                """
            )
            
            chain = LLMChain(llm=gemini_client.llm, prompt=prompt)
            response = chain.run(content=content)
            
            # Parse JSON response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                metadata = json.loads(json_match.group())
            else:
                metadata = {
                    "source": "unknown",
                    "category": "general",
                    "name": "",
                    "trait": "",
                    "game": "",
                    "sentiment": "neutral",
                    "language": "zh"
                }
            
            return metadata
            
        except Exception as e:
            logger.warning(f"⚠️ Could not generate metadata for content: {e}")
            return {
                "source": "unknown",
                "category": "general",
                "name": "",
                "trait": "",
                "game": "",
                "sentiment": "neutral",
                "language": "zh"
            }
    
    def sanitize_metadata(self, metadata: Dict) -> Dict:
        """Sanitize metadata to ensure ChromaDB compatibility"""
        sanitized = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                sanitized[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                sanitized[key] = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                # Convert dicts to JSON strings
                import json
                sanitized[key] = json.dumps(value, ensure_ascii=False)
            else:
                # Convert any other type to string
                sanitized[key] = str(value)
        return sanitized

    def enhance_chunks_with_ai_metadata(self, chunks: List[Document]) -> List[Document]:
        """Enhance chunks with AI-generated metadata"""
        try:
            logger.info("🤖 Enhancing chunks with AI-generated metadata...")
            
            enhanced_chunks = []
            for chunk in chunks:
                # Generate AI metadata
                ai_metadata = self.generate_metadata_with_ai(chunk.page_content)
                
                # Sanitize AI metadata
                sanitized_ai_metadata = self.sanitize_metadata(ai_metadata)
                
                # Merge with existing metadata
                enhanced_metadata = {**chunk.metadata, **sanitized_ai_metadata}
                
                # Create enhanced document
                enhanced_chunk = Document(
                    page_content=chunk.page_content,
                    metadata=enhanced_metadata
                )
                enhanced_chunks.append(enhanced_chunk)
            
            logger.info(f"✅ Enhanced {len(enhanced_chunks)} chunks with AI metadata")
            return enhanced_chunks
            
        except Exception as e:
            logger.error(f"❌ Error enhancing chunks: {e}")
            return chunks
    
    def build_advanced_index(self, documents: List[str]):
        """Build advanced index with automatic processing"""
        try:
            logger.info("🔨 Building advanced RAG index...")
            
            # Setup components
            logger.info("🔧 Setting up components...")
            if not self.setup_components():
                raise Exception("Failed to setup components")
            
            # Check vectorstore status
            logger.info(f"🔍 Vectorstore is None: {self.vectorstore is None}")
            logger.info(f"🔍 Vectorstore type: {type(self.vectorstore) if self.vectorstore else 'None'}")
            if self.vectorstore is None:
                logger.error("❌ Vectorstore is None after setup_components")
                raise Exception("Vectorstore not initialized")
            else:
                logger.info("✅ Vectorstore is properly initialized")
            
            # Create smart chunks
            chunks = self.create_smart_chunks(documents)
            if not chunks:
                raise Exception("No chunks created")
            
            # Enhance with AI metadata
            enhanced_chunks = self.enhance_chunks_with_ai_metadata(chunks)
            
            # Add to vectorstore
            logger.info(f"📚 Adding {len(enhanced_chunks)} documents to vectorstore...")
            self.vectorstore.add_documents(enhanced_chunks)
            logger.info("✅ Documents added to vectorstore successfully")
            
            logger.info(f"✅ Advanced index built with {len(enhanced_chunks)} enhanced chunks")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error building advanced index: {e}")
            return False
    

    
    def query_with_contextual_compression(self, query: str, k: int = 5):
        """Query with contextual compression for better relevance"""
        try:
            if not self.vectorstore:
                logger.error("❌ Vectorstore not initialized")
                return []
            
            # Create a temporary LLM for compression
            from agent.gemini_client import GeminiClient
            gemini_client = GeminiClient(self.google_api_key)
            
            # Create compressor
            compressor_prompt = PromptTemplate(
                input_variables=["question", "context"],
                template="Given the following question and context, extract only the relevant information:\n\nQuestion: {question}\n\nContext: {context}\n\nRelevant information:"
            )
            
            compressor = LLMChainExtractor.from_llm(
                llm=gemini_client.llm,
                prompt=compressor_prompt
            )
            
            # Create retriever with compression
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
            compression_retriever = ContextualCompressionRetriever(
                base_retriever=retriever,
                base_compressor=compressor
            )
            
            # Retrieve and compress
            compressed_docs = compression_retriever.get_relevant_documents(query)
            
            # Convert to document format
            documents = []
            for i, doc in enumerate(compressed_docs):
                doc_dict = {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': None  # Compression doesn't provide scores
                }
                documents.append(doc_dict)
                
                # Log document details
                content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                logger.info(f"📄 Document {i+1}: {len(doc.page_content)} chars, preview: {content_preview}")
                if doc.metadata:
                    metadata_summary = ", ".join([f"{k}: {v}" for k, v in doc.metadata.items() if v])
                    logger.info(f"   📋 Metadata: {metadata_summary}")
            
            logger.info(f"✅ Retrieved {len(documents)} compressed documents (total: {sum(len(d['content']) for d in documents)} chars)")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Error with contextual compression: {e}")
            # Fallback to basic similarity search if compression fails
            try:
                if self.vectorstore:
                    docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=k)
                    documents = []
                    for i, (doc, score) in enumerate(docs_and_scores):
                        doc_dict = {
                            'content': doc.page_content,
                            'metadata': doc.metadata,
                            'score': score
                        }
                        documents.append(doc_dict)
                        
                        # Log document details
                        content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                        logger.info(f"📄 Fallback Document {i+1}: {len(doc.page_content)} chars, score: {score:.3f}, preview: {content_preview}")
                        if doc.metadata:
                            metadata_summary = ", ".join([f"{k}: {v}" for k, v in doc.metadata.items() if v])
                            logger.info(f"   📋 Metadata: {metadata_summary}")
                    
                    logger.info(f"✅ Fallback: Retrieved {len(documents)} documents with basic search (total: {sum(len(d['content']) for d in documents)} chars)")
                    return documents
                else:
                    logger.error("❌ Vectorstore not available for fallback")
                    return []
            except Exception as fallback_error:
                logger.error(f"❌ Fallback search also failed: {fallback_error}")
                return []

# Global instance
advanced_rag_service = None

def get_advanced_rag_service(google_api_key: str) -> AdvancedRAGService:
    """Get or create Advanced RAG service instance"""
    global advanced_rag_service
    if advanced_rag_service is None:
        advanced_rag_service = AdvancedRAGService(google_api_key)
    return advanced_rag_service 