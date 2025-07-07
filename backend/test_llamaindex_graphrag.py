#!/usr/bin/env python3
"""
Test script for LlamaIndex GraphRAG implementation
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_llamaindex_graphrag():
    """Test LlamaIndex GraphRAG functionality"""
    try:
        from services.llamaindex_graphrag_service import get_llamaindex_graphrag_service
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("❌ GEMINI_API_KEY not set")
            return False
        
        # Test documents
        test_documents = [
            "Eric是O孝子，他非常孝顺父母，经常帮助家里做家务。Eric在朋友中很受欢迎，大家都喜欢和他一起玩。",
            "Eric投篮还可以，但是没有zzn准。Eric在篮球场上表现不错，但是zzn的投篮技术更加精准，命中率更高。",
            "911比718牛逼，保时捷911是经典跑车，性能卓越。718虽然也不错，但在很多方面都不如911出色。",
            "马棚是老司机，开车技术很好，经验丰富。他经常开车带大家出去玩，大家都觉得坐他的车很安全。",
            "Final全能王，在游戏Final中表现非常出色，各种角色都能玩得很好。他是大家公认的游戏高手。"
        ]
        
        logger.info("🧪 Testing LlamaIndex GraphRAG implementation...")
        
        # Initialize LlamaIndex GraphRAG service
        llamaindex_graphrag = get_llamaindex_graphrag_service(api_key)
        
        # Test setup
        logger.info("🔧 Testing component setup...")
        setup_success = llamaindex_graphrag.setup_components()
        if not setup_success:
            logger.error("❌ Component setup failed")
            return False
        logger.info("✅ Component setup successful")
        
        # Test knowledge graph building
        logger.info("🔨 Testing knowledge graph building...")
        build_success = llamaindex_graphrag.build_knowledge_graph(test_documents)
        if not build_success:
            logger.error("❌ Knowledge graph building failed")
            return False
        logger.info("✅ Knowledge graph building successful")
        
        # Test graph statistics
        logger.info("📊 Testing graph statistics...")
        stats = llamaindex_graphrag.get_graph_statistics()
        logger.info(f"📈 Graph stats: {stats}")
        
        # Test hybrid search
        logger.info("🔍 Testing hybrid search...")
        search_results = llamaindex_graphrag.hybrid_search("Eric", k=3)
        logger.info(f"📄 Hybrid search found {len(search_results)} results")
        for i, result in enumerate(search_results):
            source = result.get('source', 'unknown')
            score = result.get('score', 0)
            logger.info(f"  Result {i+1}: {result['content'][:50]}... (source: {source}, score: {score:.3f})")
        
        # Test RAG query
        logger.info("🤖 Testing RAG query...")
        rag_response = llamaindex_graphrag.query_with_rag("Who is Eric?")
        logger.info(f"📝 RAG Response: {rag_response[:200]}...")
        
        # Test entity relationships
        logger.info("🔗 Testing entity relationships...")
        relationships = llamaindex_graphrag.get_entity_relationships("Eric")
        logger.info(f"📋 Entity relationships: {relationships}")
        
        logger.info("✅ All LlamaIndex GraphRAG tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ LlamaIndex GraphRAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llamaindex_graphrag()
    sys.exit(0 if success else 1) 