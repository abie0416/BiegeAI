#!/usr/bin/env python3
"""
Test script to demonstrate the new chunking functionality
"""

import logging
from init_knowledge_base import create_chunks_from_documents, sample_documents, sample_metadatas

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chunking():
    """Test the chunking functionality"""
    logger.info("🧪 Testing chunking functionality...")
    
    # Test chunking
    chunks, chunk_metadatas = create_chunks_from_documents(sample_documents, sample_metadatas)
    
    logger.info(f"📊 Chunking Results:")
    logger.info(f"   Original documents: {len(sample_documents)}")
    logger.info(f"   Created chunks: {len(chunks)}")
    logger.info(f"   Average chunks per document: {len(chunks) / len(sample_documents):.1f}")
    
    # Show some example chunks
    logger.info(f"\n📝 Example chunks:")
    for i, (chunk, metadata) in enumerate(zip(chunks[:5], chunk_metadatas[:5])):
        logger.info(f"   Chunk {i+1}:")
        logger.info(f"     Content: {chunk[:100]}...")
        logger.info(f"     Metadata: {metadata}")
        logger.info("")
    
    # Show chunk distribution
    logger.info(f"📈 Chunk distribution by source:")
    source_counts = {}
    for metadata in chunk_metadatas:
        source = metadata.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    
    for source, count in source_counts.items():
        logger.info(f"   {source}: {count} chunks")
    
    logger.info("✅ Chunking test completed!")

if __name__ == "__main__":
    test_chunking() 