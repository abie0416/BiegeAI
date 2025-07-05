#!/usr/bin/env python3
"""
Initialize the knowledge base with sample data for testing RAG functionality.
"""

from db.chroma_client import add_documents_to_vectorstore

# Sample knowledge base data
sample_documents = [
    "Eric是O孝子",
    "Eric投篮还可以，但是没有zzn准",
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
    print("Initializing knowledge base with sample data...")
    
    try:
        add_documents_to_vectorstore(sample_documents)
        print("✅ Knowledge base initialized successfully!")
        print(f"Added {len(sample_documents)} documents to the vectorstore.")
    except Exception as e:
        print(f"❌ Error initializing knowledge base: {e}")

if __name__ == "__main__":
    init_knowledge_base() 