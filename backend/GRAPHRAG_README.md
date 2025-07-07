# GraphRAG Implementation

This document explains the GraphRAG (Graph-based Retrieval Augmented Generation) implementation that replaces traditional vector-based RAG with a more sophisticated graph-based approach.

## What is GraphRAG?

GraphRAG uses knowledge graphs to represent relationships between entities, concepts, and documents. Instead of just finding similar vectors, it:

1. **Extracts entities and relationships** from documents using AI
2. **Builds a knowledge graph** with nodes (entities, documents) and edges (relationships)
3. **Performs graph-based search** that considers both semantic similarity and graph connectivity
4. **Combines graph and vector search** for hybrid retrieval

## Key Components

### 1. GraphRAGService (`services/graph_rag_service.py`)

The main service that handles:
- **Entity extraction**: Uses AI to identify people, places, concepts, etc.
- **Relationship extraction**: Discovers connections between entities
- **Knowledge graph building**: Creates a NetworkX graph structure
- **Graph search**: Finds relevant nodes using embeddings and graph traversal
- **Hybrid search**: Combines graph and vector search results

### 2. Graph Structure

- **Nodes**: Documents, entities (people, places, concepts), relationships
- **Edges**: Connections between entities with relationship types and weights
- **Embeddings**: Vector representations for semantic similarity
- **Metadata**: Rich information about nodes and relationships

### 3. Search Methods

- **Graph Search**: Uses embeddings + graph connectivity
- **Vector Search**: Traditional similarity search (fallback)
- **Hybrid Search**: Combines both approaches for best results

## Installation

Add the required dependencies to `requirements.txt`:

```txt
networkx
numpy
pydantic
langchain-experimental
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Basic Setup

```python
from services.graph_rag_service import get_graph_rag_service

# Initialize service
graph_rag = get_graph_rag_service(google_api_key)

# Setup components
graph_rag.setup_components()

# Build knowledge graph from documents
documents = ["Document 1", "Document 2", ...]
success = graph_rag.build_knowledge_graph(documents)
```

### 2. Search Operations

```python
# Graph-based search
results = graph_rag.graph_search("Eric", max_nodes=10)

# Hybrid search (recommended)
results = graph_rag.hybrid_search("Eric", k=5)

# Get graph statistics
stats = graph_rag.get_graph_statistics()
```

### 3. API Endpoints

The implementation adds several new endpoints:

- `POST /rebuild-rag`: Rebuilds both Advanced RAG and GraphRAG
- `GET /graph-stats`: Returns knowledge graph statistics
- `POST /graph-search`: Performs GraphRAG search

### 4. Integration with Main App

The main application automatically uses GraphRAG with fallback to Advanced RAG:

```python
# In main.py, the get_rag_context function now:
# 1. Tries GraphRAG first
# 2. Falls back to Advanced RAG if GraphRAG fails
# 3. Returns combined results
```

## Architecture

```
Documents → Entity Extraction → Relationship Extraction → Knowledge Graph
     ↓              ↓                    ↓                    ↓
Vector Store ← Embeddings ← Graph Search ← Hybrid Search ← Query
```

### Entity Extraction Process

1. **AI Analysis**: Uses Gemini to identify entities in text
2. **Entity Types**: People, places, organizations, concepts, skills, games, events
3. **Metadata**: Descriptions, attributes, source documents

### Relationship Extraction Process

1. **AI Analysis**: Identifies connections between entities
2. **Relationship Types**: knows, works_at, plays, likes, has_skill, etc.
3. **Weights**: Relationship strength (0.1 to 1.0)

### Search Process

1. **Query Embedding**: Convert query to vector
2. **Graph Search**: Find similar nodes + connected neighbors
3. **Vector Search**: Traditional similarity search
4. **Hybrid Ranking**: Combine and rank results
5. **Deduplication**: Remove duplicate content

## Advantages over Traditional RAG

### 1. Better Context Understanding
- **Relationships**: Understands connections between entities
- **Context**: Considers graph structure, not just similarity
- **Reasoning**: Can follow relationship chains

### 2. More Accurate Retrieval
- **Entity-aware**: Finds related entities even with different terms
- **Relationship-aware**: Understands "Eric's friend" vs "Eric"
- **Graph traversal**: Can find indirectly related information

### 3. Richer Metadata
- **Entity types**: Knows if something is a person, place, concept
- **Relationships**: Understands how entities are connected
- **Attributes**: Stores additional information about entities

### 4. Hybrid Approach
- **Best of both**: Combines graph and vector search
- **Fallback**: Works even if graph building fails
- **Flexibility**: Can adjust search strategy based on query

## Example Use Cases

### 1. Personal Knowledge Base
```
Query: "Who is Eric's friend?"
GraphRAG: Finds Eric → follows "knows" relationships → finds friends
Traditional RAG: Might miss if "friend" isn't mentioned explicitly
```

### 2. Skill Discovery
```
Query: "Who is good at basketball?"
GraphRAG: Finds basketball → follows "has_skill" relationships → finds players
Traditional RAG: Relies on exact text matching
```

### 3. Relationship Queries
```
Query: "Compare Eric and zzn in basketball"
GraphRAG: Finds both entities → follows basketball relationships → compares
Traditional RAG: Might not understand the comparison context
```

## Testing

Run the test script to verify the implementation:

```bash
cd backend
python test_graphrag.py
```

This will test:
- Component setup
- Knowledge graph building
- Entity and relationship extraction
- Graph search functionality
- Hybrid search functionality

## Configuration

### Environment Variables
- `GEMINI_API_KEY`: Required for AI-powered extraction

### Graph Parameters
- `chunk_size`: 500 characters (configurable)
- `chunk_overlap`: 100 characters (configurable)
- `max_nodes`: 10 for graph search (configurable)
- `k`: 5 for hybrid search (configurable)

### Entity Extraction
- Entity types: person, place, organization, concept, skill, game, event
- Relationship types: knows, works_at, plays, likes, has_skill, etc.
- Weight range: 0.1 to 1.0 for relationship strength

## Performance Considerations

### Memory Usage
- Knowledge graph stored in memory (NetworkX)
- Embeddings cached for nodes
- Vector store for hybrid retrieval

### Processing Time
- Entity extraction: ~1-2 seconds per document
- Relationship extraction: ~1-2 seconds per document
- Graph building: Depends on document count
- Search: ~100-500ms per query

### Scalability
- Suitable for small to medium knowledge bases
- For large datasets, consider:
  - Graph database (Neo4j, ArangoDB)
  - Distributed graph processing
  - Incremental graph updates

## Troubleshooting

### Common Issues

1. **Entity extraction fails**
   - Check API key configuration
   - Verify document content quality
   - Check network connectivity

2. **Graph building fails**
   - Ensure all dependencies installed
   - Check memory availability
   - Verify document format

3. **Search returns no results**
   - Check if knowledge graph was built
   - Verify query relevance
   - Check graph statistics

### Debug Information

Use the `/graph-stats` endpoint to check graph health:
```bash
curl http://localhost:8000/graph-stats
```

Use the `/graph-search` endpoint to test search:
```bash
curl -X POST http://localhost:8000/graph-search \
  -H "Content-Type: application/json" \
  -d '{"query": "Eric", "k": 5}'
```

## Future Enhancements

### Potential Improvements

1. **Graph Database Integration**
   - Neo4j for persistent storage
   - Cypher query language
   - Graph algorithms

2. **Advanced Graph Algorithms**
   - PageRank for importance ranking
   - Community detection
   - Path finding algorithms

3. **Incremental Updates**
   - Add new documents without rebuilding
   - Update existing relationships
   - Remove outdated information

4. **Multi-modal Support**
   - Image entity extraction
   - Audio transcription
   - Video analysis

5. **Advanced Reasoning**
   - Multi-hop reasoning
   - Logical inference
   - Temporal relationships

## Conclusion

GraphRAG provides a significant improvement over traditional vector-based RAG by:

- Understanding relationships between entities
- Providing more accurate and contextual search results
- Supporting complex queries that require reasoning
- Maintaining rich metadata about knowledge structure

The hybrid approach ensures reliability while leveraging the power of graph-based retrieval for better user experience. 