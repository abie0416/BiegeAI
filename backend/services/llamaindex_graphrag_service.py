"""
LlamaIndex GraphRAG service using optimized graph-based retrieval
Updated for Railway deployment with GCP Cloud Storage persistence
"""
import logging
import os
import traceback
import tempfile
import shutil
from typing import List, Dict, Optional, Any
from llama_index.core import (
    VectorStoreIndex, 
    Document, 
    Settings,
    StorageContext,
    load_index_from_storage
)
from llama_index.core.indices.knowledge_graph import KnowledgeGraphIndex
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.google import GeminiEmbedding
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.llms import LLM
from agent.gemini_client import GeminiClient
from services.document_preprocessor import DocumentPreprocessor
from concurrent.futures import ThreadPoolExecutor

# GCP Cloud Storage imports
try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logging.warning("Google Cloud Storage not available. Install google-cloud-storage for GCP integration.")

# Get logger for this module
logger = logging.getLogger(__name__)

class LlamaIndexLLMWrapper(LLM):
    """Wrapper to make GeminiClient compatible with LlamaIndex LLM interface"""
    gemini_client: Any  # Define as a field
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client=gemini_client)
    
    def complete(self, prompt: str, **kwargs):
        """Complete a prompt using the Gemini client"""
        logger.info(f"🤖 Sending prompt to Gemini model:")
        logger.info(f"   - Prompt length: {len(prompt)} characters")
        logger.info(f"   - Prompt content: {prompt}")
        logger.info(f"   - Additional kwargs: {kwargs}")
        
        response = self.gemini_client.generate(prompt)
        
        logger.info(f"✅ Received response from Gemini model:")
        logger.info(f"   - Response length: {len(response)} characters")
        logger.info(f"   - Response content: {response}")
        
        # Return a response object that LlamaIndex expects
        return type('Response', (), {
            'text': response,
            'message': type('Message', (), {'content': response})()
        })()
    
    def chat(self, messages, **kwargs):
        """Chat completion"""
        # Convert messages to a single prompt
        prompt = "\n".join([msg.content for msg in messages])
        
        logger.info(f"💬 Sending chat messages to Gemini model:")
        logger.info(f"   - Number of messages: {len(messages)}")
        logger.info(f"   - Combined prompt length: {len(prompt)} characters")
        logger.info(f"   - Combined prompt content: {prompt}")
        logger.info(f"   - Additional kwargs: {kwargs}")
        
        response = self.gemini_client.generate(prompt)
        
        logger.info(f"✅ Received chat response from Gemini model:")
        logger.info(f"   - Response length: {len(response)} characters")
        logger.info(f"   - Response content: {response}")
        
        return type('Response', (), {
            'text': response,
            'message': type('Message', (), {'content': response})()
        })()
    
    def stream_complete(self, prompt: str, **kwargs):
        """Stream completion"""
        response = self.gemini_client.generate(prompt)
        yield type('Response', (), {'text': response})()
    
    def stream_chat(self, messages, **kwargs):
        """Stream chat completion"""
        prompt = "\n".join([msg.content for msg in messages])
        response = self.gemini_client.generate(prompt)
        yield type('Response', (), {'text': response})()
    
    async def acomplete(self, prompt: str, **kwargs):
        """Async complete (not implemented, falls back to sync)"""
        return self.complete(prompt, **kwargs)
    
    async def achat(self, messages, **kwargs):
        """Async chat (not implemented, falls back to sync)"""
        return self.chat(messages, **kwargs)
    
    async def astream_complete(self, prompt: str, **kwargs):
        """Async stream complete (not implemented, falls back to sync)"""
        for response in self.stream_complete(prompt, **kwargs):
            yield response
    
    async def astream_chat(self, messages, **kwargs):
        """Async stream chat (not implemented, falls back to sync)"""
        for response in self.stream_chat(messages, **kwargs):
            yield response
    
    @property
    def metadata(self):
        """Return metadata about the LLM"""
        # Return a proper object instead of a dict
        return type('Metadata', (), {
            "model_name": "gemini-1.5-pro",
            "temperature": 0.7,
            "max_tokens": None,
            "is_chat_model": True,
            "context_window": 8192,
            "num_output": 4096
        })()
    
    @property
    def is_chat_model(self) -> bool:
        """Return whether this is a chat model"""
        return True

class LlamaIndexGraphRAGService:
    def __init__(self, google_api_key: str, gcp_bucket_name: str = None, gcp_project_id: str = None):
        self.google_api_key = google_api_key
        self.gcp_bucket_name = gcp_bucket_name
        self.gcp_project_id = gcp_project_id
        self.storage_path = "./graphrag_storage"
        self.llm = None
        self.embed_model = None
        self.graph_store = None
        self.knowledge_graph_index = None
        self.vector_index = None
        self.retriever = None
        self.query_engine = None
        self.storage_context = None
        self.document_preprocessor = DocumentPreprocessor(google_api_key)
        
        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize GCP client if available
        self.gcp_client = None
        if GCP_AVAILABLE and gcp_bucket_name:
            try:
                # Check if we have service account JSON in environment
                service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
                if service_account_json:
                    # Create temporary credentials file from environment variable
                    import tempfile
                    import json
                    
                    # Parse the JSON to validate it
                    service_account_data = json.loads(service_account_json)
                    
                    # Create temporary file with credentials
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        json.dump(service_account_data, f)
                        temp_credentials_path = f.name
                    
                    # Set environment variable for Google Cloud client
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_credentials_path
                    
                    self.gcp_client = storage.Client(project=gcp_project_id)
                    logger.info(f"✅ GCP Cloud Storage client initialized for bucket: {gcp_bucket_name}")
                else:
                    logger.warning("⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not found in environment variables")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize GCP client: {e}")
                self.gcp_client = None
        
    def setup_components(self):
        """Setup LlamaIndex GraphRAG components"""
        try:
            # Set API key
            os.environ["GOOGLE_API_KEY"] = self.google_api_key
            
            # Initialize LLM for graph construction
            gemini_client = GeminiClient(self.google_api_key)
            self.llm = LlamaIndexLLMWrapper(gemini_client)
            
            # Initialize embedding model
            self.embed_model = GeminiEmbedding(
                model_name="models/embedding-001",
                api_key=self.google_api_key
            )
            
            # Set global settings
            Settings.llm = self.llm
            Settings.embed_model = self.embed_model
            Settings.chunk_size = 512
            Settings.chunk_overlap = 50
            
            # Initialize graph store
            self.graph_store = SimpleGraphStore()
            
            # Initialize storage context
            self.storage_context = StorageContext.from_defaults(
                graph_store=self.graph_store
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up LlamaIndex GraphRAG components: {e}")
            traceback.print_exc()  # Print full traceback
            print("Exception details:", e)  # Print exception details
            return False
    
    def build_knowledge_graph(self, documents: List[Dict]):
        """Build knowledge graph using LlamaIndex with entity extraction"""
        try:
            logger.info("🔨 Building LlamaIndex knowledge graph...")
            
            # Setup components
            if not self.setup_components():
                raise Exception("Failed to setup components")
            
            # Preprocess documents using AI
            logger.info("🧹 Preprocessing documents with AI...")
            preprocessed_docs = self.document_preprocessor.preprocess_documents(documents)
            
            # Parallelize conversion to LlamaIndex Document objects
            def to_llama_doc(args):
                i, doc = args
                content = doc.get('content', '')
                if content.strip():
                    doc_metadata = {
                        "source": "google_sheets",
                        "document_id": i,
                        "content_length": len(content),
                        "original_length": doc.get('original_length', len(content)),
                        "processed_length": doc.get('processed_length', len(content)),
                        "compression_ratio": doc.get('compression_ratio', 1.0),
                        "preprocessed": True
                    }
                    return Document(
                        text=content.strip(),
                        metadata=doc_metadata
                    )
                return None
            with ThreadPoolExecutor(max_workers=8) as executor:
                llama_docs = list(executor.map(to_llama_doc, enumerate(preprocessed_docs)))
            llama_docs = [doc for doc in llama_docs if doc]
            
            if not llama_docs:
                raise Exception("No valid documents to process")
            
            logger.info(f"📚 Processing {len(llama_docs)} documents...")
            
            # Create knowledge graph index with entity extraction
            self.knowledge_graph_index = KnowledgeGraphIndex.from_documents(
                documents=llama_docs,
                storage_context=self.storage_context,
                max_triplets_per_chunk=10,
                include_embeddings=True,
                show_progress=True
            )
            
            # Create vector index for hybrid retrieval
            self.vector_index = VectorStoreIndex.from_documents(
                documents=llama_docs,
                storage_context=self.storage_context,
                show_progress=True
            )
            
            # Create retriever from knowledge graph index
            self.retriever = self.knowledge_graph_index.as_retriever(
                similarity_top_k=5
            )
            
            # Create query engine
            self.query_engine = RetrieverQueryEngine.from_args(
                retriever=self.retriever,
                llm=self.llm
            )
            
            logger.info("✅ LlamaIndex knowledge graph built successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error building LlamaIndex knowledge graph: {e}")
            return False
    
    def save_index(self, persist_dir: str = None):
        """Save the index to disk and optionally upload to GCP"""
        try:
            persist_dir = persist_dir or self.storage_path
            
            if self.storage_context:
                # Save locally
                self.storage_context.persist(persist_dir=persist_dir)
                logger.info(f"✅ Index saved locally to {persist_dir}")
                
                # Upload to GCP if configured
                if self.gcp_client and self.gcp_bucket_name:
                    self._upload_to_gcp(persist_dir)
                
                return True
            else:
                logger.warning("⚠️ No storage context to save")
                return False
        except Exception as e:
            logger.error(f"❌ Error saving index: {e}")
            return False
    
    def _upload_to_gcp(self, local_path: str):
        """Upload RAG index files to GCP Cloud Storage"""
        try:
            bucket = self.gcp_client.bucket(self.gcp_bucket_name)
            
            # Upload all files in the directory
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    # Create GCP blob path relative to local_path
                    relative_path = os.path.relpath(local_file_path, local_path)
                    blob_path = f"rag_index/{relative_path}"
                    
                    blob = bucket.blob(blob_path)
                    blob.upload_from_filename(local_file_path)
                    logger.info(f"📤 Uploaded to GCP: {blob_path}")
            
            logger.info(f"✅ Successfully uploaded RAG index to GCP bucket: {self.gcp_bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error uploading to GCP: {e}")
            return False
    
    def download_from_gcp(self) -> bool:
        """Download RAG index from GCP Cloud Storage to local storage"""
        try:
            if not self.gcp_client or not self.gcp_bucket_name:
                logger.warning("⚠️ GCP client not configured, skipping download")
                return False
            
            bucket = self.gcp_client.bucket(self.gcp_bucket_name)
            
            # List all blobs with rag_index/ prefix
            blobs = bucket.list_blobs(prefix="rag_index/")
            
            files_downloaded = 0
            for blob in blobs:
                # Skip if it's a directory marker
                if blob.name.endswith('/'):
                    continue
                
                # Create local file path
                relative_path = blob.name.replace("rag_index/", "")
                local_file_path = os.path.join(self.storage_path, relative_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # Download file
                blob.download_to_filename(local_file_path)
                files_downloaded += 1
                logger.info(f"📥 Downloaded from GCP: {blob.name} -> {local_file_path}")
            
            if files_downloaded > 0:
                logger.info(f"✅ Successfully downloaded {files_downloaded} files from GCP")
                return True
            else:
                logger.warning("⚠️ No files found in GCP bucket")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error downloading from GCP: {e}")
            return False
    
    def load_index(self, persist_dir: str = None):
        """Load the index from disk"""
        import json
        import os
        
        try:
            persist_dir = persist_dir or self.storage_path
            
            if os.path.exists(persist_dir):
                self.storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
                
                # Get available index IDs by reading the index store JSON file directly
                try:
                    
                    # Read the index store JSON file directly
                    index_store_path = os.path.join(persist_dir, "index_store.json")
                    if os.path.exists(index_store_path):
                        with open(index_store_path, 'r') as f:
                            index_store_data = json.load(f)
                        
                        logger.info(f"📋 Available index store keys: {list(index_store_data.keys())}")
                        
                        # Find knowledge graph index (look for one with type 'kg')
                        knowledge_graph_id = None
                        vector_index_id = None
                        
                        # The data is nested under 'index_store/data'
                        if 'index_store/data' in index_store_data:
                            data_dict = index_store_data['index_store/data']
                            logger.info(f"📋 Index data keys: {list(data_dict.keys())}")
                            
                            for key, value in data_dict.items():
                                if isinstance(value, dict) and value.get('__type__') == 'kg':
                                    knowledge_graph_id = key
                                    logger.info(f"🔍 Found knowledge graph index with ID: {knowledge_graph_id}")
                                elif isinstance(value, dict) and value.get('__type__') == 'vector_store':
                                    vector_index_id = key
                                    logger.info(f"🔍 Found vector index with ID: {vector_index_id}")
                        
                        if not knowledge_graph_id:
                            logger.warning("⚠️ No knowledge graph index found in storage")
                            return False
                            
                        if not vector_index_id:
                            logger.warning("⚠️ No vector index found in storage")
                            return False
                    else:
                        logger.warning(f"⚠️ Index store file not found: {index_store_path}")
                        return False
                            
                except Exception as e:
                    logger.error(f"❌ Error getting index IDs: {e}")
                    return False
                
                if not knowledge_graph_id:
                    logger.error("❌ No knowledge graph index found")
                    return False
                
                # Load the knowledge graph index
                self.knowledge_graph_index = load_index_from_storage(
                    storage_context=self.storage_context,
                    index_id=knowledge_graph_id
                )
                
                # Load vector index if available
                if vector_index_id:
                    self.vector_index = load_index_from_storage(
                        storage_context=self.storage_context,
                        index_id=vector_index_id
                    )
                else:
                    # Create a new vector index if none exists
                    logger.info("📝 Creating new vector index...")
                    self.vector_index = VectorStoreIndex.from_documents(
                        documents=[],  # Empty for now, will be populated when needed
                        storage_context=self.storage_context
                    )
                
                # Recreate retriever and query engine
                self.retriever = self.knowledge_graph_index.as_retriever(
                    similarity_top_k=5
                )
                
                self.query_engine = RetrieverQueryEngine.from_args(
                    retriever=self.retriever,
                    llm=self.llm
                )
                
                logger.info(f"✅ Index loaded from {persist_dir}")
                return True
            else:
                logger.warning(f"⚠️ Index directory {persist_dir} not found")
                return False
        except Exception as e:
            logger.error(f"❌ Error loading index: {e}")
            return False
    
    def initialize_from_gcp(self) -> bool:
        """Initialize the service by downloading index from GCP and loading it"""
        try:
            logger.info("🔄 Initializing RAG service from GCP...")
            
            # Setup components first
            if not self.setup_components():
                logger.error("❌ Failed to setup components")
                return False
            
            # Try to download from GCP
            if self.download_from_gcp():
                # Load the downloaded index
                if self.load_index():
                    logger.info("✅ Successfully initialized RAG service from GCP")
                    return True
                else:
                    logger.warning("⚠️ Downloaded from GCP but failed to load index")
                    return False
            else:
                logger.warning("⚠️ No index found in GCP, service will need to be built")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing from GCP: {e}")
            return False
    
    def hybrid_search(self, query: str, k: int = 5) -> List[Dict]:
        """Perform hybrid search using LlamaIndex GraphRAG"""
        try:
            logger.info(f"🔍 Performing LlamaIndex GraphRAG search for: {query}")
            
            if not self.retriever:
                logger.error("❌ Retriever not initialized")
                return []
            
            # Get retrieved nodes
            retrieved_nodes = self.retriever.retrieve(query)
            logger.info(f"📊 Retrieved {len(retrieved_nodes)} nodes from LlamaIndex vector storage")
            
            # Convert to result format
            results = []
            for i, node in enumerate(retrieved_nodes[:k]):
                result = {
                    "content": node.text,
                    "metadata": node.metadata,
                    "score": node.score if hasattr(node, 'score') else 1.0,
                    "source": "llamaindex_graphrag",
                    "node_id": node.node_id
                }
                results.append(result)
                
                # Enhanced logging for retrieved data
                logger.info(f"📄 Retrieved Node {i+1}:")
                logger.info(f"   - Node ID: {node.node_id}")
                logger.info(f"   - Content: {node.text}")
                logger.info(f"   - Score: {node.score if hasattr(node, 'score') else 'N/A'}")
                logger.info(f"   - Metadata: {node.metadata}")
                logger.info(f"   - Content Length: {len(node.text)} characters")
                
                # Log content preview for quick reference
                content_preview = node.text[:150] + "..." if len(node.text) > 150 else node.text
                logger.info(f"   - Preview: {content_preview}")
            
            logger.info(f"✅ LlamaIndex GraphRAG search returned {len(results)} results")
            logger.info(f"📈 Total content retrieved: {sum(len(r['content']) for r in results)} characters")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in LlamaIndex GraphRAG search: {e}")
            return []
    
    def query_with_rag(self, query: str) -> str:
        """Query with RAG using LlamaIndex GraphRAG"""
        try:
            logger.info(f"🤖 Querying with LlamaIndex GraphRAG: {query}")
            
            if not self.query_engine:
                logger.error("❌ Query engine not initialized")
                return "Query engine not available"
            
            # Get response from query engine
            response = self.query_engine.query(query)
            
            logger.info(f"✅ LlamaIndex GraphRAG query completed")
            return str(response)
            
        except Exception as e:
            logger.error(f"❌ Error in LlamaIndex GraphRAG query: {e}")
            return f"Error: {str(e)}"
    
    def get_graph_statistics(self) -> Dict:
        """Get knowledge graph statistics"""
        try:
            if not self.knowledge_graph_index:
                return {"error": "Knowledge graph index not initialized"}
            
            # Get graph store statistics
            graph_store = self.knowledge_graph_index.graph_store
            
            stats = {
                "total_nodes": len(graph_store.get_nodes()) if hasattr(graph_store, 'get_nodes') else 0,
                "total_edges": len(graph_store.get_edges()) if hasattr(graph_store, 'get_edges') else 0,
                "index_type": "llamaindex_graphrag",
                "storage_context": "initialized" if self.storage_context else "not_initialized",
                "retriever_initialized": self.retriever is not None,
                "query_engine_initialized": self.query_engine is not None
            }
            
            # Try to get more detailed stats
            try:
                if hasattr(graph_store, 'get_all_nodes'):
                    all_nodes = graph_store.get_all_nodes()
                    stats["node_types"] = {}
                    for node in all_nodes:
                        node_type = node.get("type", "unknown")
                        stats["node_types"][node_type] = stats["node_types"].get(node_type, 0) + 1
            except:
                stats["node_types"] = {"unknown": 0}
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting graph statistics: {e}")
            return {"error": str(e)}
    
    def get_entity_relationships(self, entity_name: str) -> List[Dict]:
        """Get relationships for a specific entity"""
        try:
            if not self.knowledge_graph_index:
                return []
            
            # Query the graph for entity relationships
            query = f"What are the relationships involving {entity_name}?"
            response = self.query_engine.query(query)
            
            # Extract relationships from response
            relationships = []
            response_text = str(response)
            
            # Simple parsing - in a real implementation, you'd want more sophisticated parsing
            if "relationship" in response_text.lower():
                relationships.append({
                    "entity": entity_name,
                    "relationships": response_text,
                    "source": "llamaindex_graphrag"
                })
            
            return relationships
            
        except Exception as e:
            logger.error(f"❌ Error getting entity relationships: {e}")
            return []
    
    def explore_graph_structure(self) -> Dict:
        """Explore the knowledge graph structure"""
        try:
            if not self.knowledge_graph_index:
                return {"error": "Knowledge graph not initialized"}
            
            graph_store = self.knowledge_graph_index.graph_store
            
            # Get sample nodes and edges
            nodes = graph_store.get_nodes()[:10] if hasattr(graph_store, 'get_nodes') else []
            edges = graph_store.get_edges()[:10] if hasattr(graph_store, 'get_edges') else []
            
            structure = {
                "sample_nodes": nodes,
                "sample_edges": edges,
                "total_nodes": len(graph_store.get_nodes()) if hasattr(graph_store, 'get_nodes') else 0,
                "total_edges": len(graph_store.get_edges()) if hasattr(graph_store, 'get_edges') else 0
            }
            
            return structure
            
        except Exception as e:
            logger.error(f"❌ Error exploring graph structure: {e}")
            return {"error": str(e)}

# Global instance
llamaindex_graphrag_service = None

def get_llamaindex_graphrag_service(google_api_key: str, gcp_bucket_name: str = None, gcp_project_id: str = None) -> LlamaIndexGraphRAGService:
    """Get or create LlamaIndex GraphRAG service instance"""
    global llamaindex_graphrag_service
    if llamaindex_graphrag_service is None:
        llamaindex_graphrag_service = LlamaIndexGraphRAGService(
            google_api_key=google_api_key,
            gcp_bucket_name=gcp_bucket_name,
            gcp_project_id=gcp_project_id
        )
    return llamaindex_graphrag_service 