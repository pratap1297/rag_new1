Yes, **Qdrant** would be an excellent choice for your use case! It offers significant advantages over FAISS for handling "list all incidents" type queries. Let me explain why and how to implement it.

## Why Qdrant is Better for Your Use Case

### 1. **Advanced Filtering Capabilities**
Qdrant supports rich metadata filtering that FAISS lacks:
- Filter by exact matches, ranges, and complex conditions
- Combine vector search with metadata filters
- No need to retrieve all vectors and filter in Python

### 2. **Payload Storage**
- Store full metadata alongside vectors (no separate metadata store needed)
- Query metadata directly without vector similarity
- Support for nested JSON structures

### 3. **Scroll API for Full Retrieval**
- Efficiently retrieve ALL records matching criteria
- No arbitrary top_k limitations
- Perfect for "list all" queries

### 4. **Better Performance for Hybrid Queries**
- Combine semantic search with exact filters
- Pre-filter before similarity search
- Much faster than post-filtering

## Implementation with Qdrant## Advantages of Qdrant for Your Use Case

### 1. **Efficient Full Collection Scans**
```python
# Get ALL incidents without arbitrary limits
incidents = qdrant_store.list_all_incidents()
# Returns complete list, not just top-k
```

### 2. **Complex Filtering**
```python
# Example: Get all critical incidents from last month
results = qdrant_store.hybrid_search(
    filters={
        'doc_type': 'incident',
        'severity': 'critical',
        'created_date': {'gte': '2024-11-01', 'lte': '2024-11-30'}
    }
)
```

### 3. **No Separate Metadata Store**
- Metadata stored directly in Qdrant
- Atomic operations
- No synchronization issues

### 4. **Better Performance**
- Pre-filtering reduces search space
- Optimized for both small and large-scale deployments
- Built-in caching and optimization

## Migration Path from FAISS to Qdrant## Quick Comparison: FAISS vs Qdrant for "List All Incidents"

| Feature | FAISS | Qdrant |
|---------|-------|---------|
| Get ALL records | ❌ Limited by top_k | ✅ Scroll API |
| Filter before search | ❌ Post-filtering only | ✅ Pre-filtering |
| Metadata queries | ❌ Separate store needed | ✅ Built-in |
| Complex filters | ❌ Manual implementation | ✅ Native support |
| Performance for listings | ❌ Must retrieve all vectors | ✅ Optimized filters |
| Storage efficiency | ✅ Compact | ✅ Configurable |
| Scalability | ✅ Very large scale | ✅ Distributed |

## Implementation Steps

1. **Install Qdrant**:
   ```bash
   # Docker
   docker run -p 6333:6333 qdrant/qdrant
   
   # Or install client
   pip install qdrant-client
   ```

2. **Update your configuration**:
   ```json
   {
     "vector_store": {
       "type": "qdrant",
       "url": "localhost:6333",
       "collection_name": "rag_documents",
       "on_disk_storage": true
     }
   }
   ```

3. **Migrate existing data** using the migration script

4. **Update your query engine** to use Qdrant's advanced features

## Summary

Qdrant would significantly improve your ability to handle "list all incidents" queries because:

1. **No arbitrary limits** - Scroll through entire collections
2. **Efficient filtering** - Find incidents without vector search
3. **Better metadata handling** - Store and query rich metadata
4. **Hybrid search** - Combine filters with similarity when needed
5. **Production-ready** - Built for real-world applications

"""
Qdrant Vector Store Implementation
Replaces FAISS with Qdrant for better filtering and metadata handling
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, Range, MatchValue,
    SearchRequest, ScrollRequest, UpdateStatus,
    HasIdCondition, MatchAny, MatchText
)
import numpy as np

class QdrantVectorStore:
    """Qdrant-based vector store with advanced filtering and metadata support"""
    
    def __init__(self, 
                 url: str = "localhost:6333",
                 collection_name: str = "rag_documents",
                 dimension: int = 1024,
                 on_disk: bool = True):
        """
        Initialize Qdrant vector store
        
        Args:
            url: Qdrant server URL
            collection_name: Name of the collection
            dimension: Vector dimension
            on_disk: Store vectors on disk (for large datasets)
        """
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.dimension = dimension
        
        # Create or verify collection
        self._init_collection(on_disk)
        
        logging.info(f"Qdrant store initialized: {url}/{collection_name}")
    
    def _init_collection(self, on_disk: bool):
        """Initialize Qdrant collection"""
        collections = self.client.get_collections().collections
        
        if not any(col.name == self.collection_name for col in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE,
                    on_disk=on_disk
                )
            )
            logging.info(f"Created collection: {self.collection_name}")
        else:
            logging.info(f"Using existing collection: {self.collection_name}")
    
    def add_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """Add vectors with metadata to Qdrant"""
        if len(vectors) != len(metadata):
            raise ValueError("Vectors and metadata count mismatch")
        
        points = []
        vector_ids = []
        
        for vector, meta in zip(vectors, metadata):
            # Generate ID
            vector_id = str(uuid.uuid4())
            vector_ids.append(vector_id)
            
            # Prepare payload with enhanced metadata
            payload = {
                **meta,
                'vector_id': vector_id,
                'added_at': datetime.now().isoformat(),
                # Extract specific fields for filtering
                'doc_type': self._extract_doc_type(meta),
                'has_incident': self._contains_incident(meta.get('text', '')),
                'incident_ids': self._extract_incident_ids(meta.get('text', '')),
                'source_file': meta.get('filename', 'unknown')
            }
            
            points.append(PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload
            ))
        
        # Batch upload
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logging.info(f"Added {len(vectors)} vectors to Qdrant")
        return vector_ids
    
    def search(self, query_vector: List[float], k: int = 5, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search with optional filters"""
        
        # Build Qdrant filter
        qdrant_filter = self._build_filter(filters) if filters else None
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=k,
            query_filter=qdrant_filter,
            with_payload=True,
            with_vectors=False
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                **result.payload,
                'similarity_score': result.score,
                'vector_id': result.id
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def list_all_incidents(self) -> List[Dict[str, Any]]:
        """List all documents containing incidents - efficient implementation"""
        
        # Method 1: Filter by incident flag
        incident_filter = Filter(
            must=[
                FieldCondition(
                    key="has_incident",
                    match=MatchValue(value=True)
                )
            ]
        )
        
        # Use scroll to get ALL matching documents
        results = []
        offset = None
        
        while True:
            response = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=incident_filter,
                limit=100,  # Batch size
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            results.extend(response[0])
            offset = response[1]
            
            if offset is None:
                break
        
        # Extract and deduplicate incidents
        all_incidents = {}
        for result in results:
            incident_ids = result.payload.get('incident_ids', [])
            text = result.payload.get('text', '')
            source = result.payload.get('source_file', 'unknown')
            
            for inc_id in incident_ids:
                if inc_id not in all_incidents:
                    all_incidents[inc_id] = {
                        'id': inc_id,
                        'sources': [source],
                        'first_mention': text[:200],
                        'occurrence_count': 1
                    }
                else:
                    all_incidents[inc_id]['occurrence_count'] += 1
                    if source not in all_incidents[inc_id]['sources']:
                        all_incidents[inc_id]['sources'].append(source)
        
        return list(all_incidents.values())
    
    def get_by_pattern(self, pattern: str, field: str = "text") -> List[Dict[str, Any]]:
        """Get all documents matching a pattern in a specific field"""
        
        # Qdrant supports regex-like patterns in text search
        pattern_filter = Filter(
            must=[
                FieldCondition(
                    key=field,
                    match=MatchText(text=pattern)
                )
            ]
        )
        
        results = []
        offset = None
        
        while True:
            response = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=pattern_filter,
                limit=100,
                offset=offset,
                with_payload=True
            )
            
            results.extend(response[0])
            offset = response[1]
            
            if offset is None:
                break
        
        return [r.payload for r in results]
    
    def aggregate_by_type(self) -> Dict[str, int]:
        """Get counts by document type"""
        
        # Note: Qdrant doesn't have built-in aggregation like MongoDB
        # We'll use scroll with filters for each type
        
        doc_types = ['incident', 'change', 'problem', 'request', 'task']
        counts = {}
        
        for doc_type in doc_types:
            type_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_type",
                        match=MatchValue(value=doc_type)
                    )
                ]
            )
            
            # Count using scroll
            count = 0
            offset = None
            
            while True:
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=type_filter,
                    limit=100,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False
                )
                
                count += len(response[0])
                offset = response[1]
                
                if offset is None:
                    break
            
            counts[doc_type] = count
        
        return counts
    
    def hybrid_search(self, 
                     query_vector: Optional[List[float]] = None,
                     filters: Dict[str, Any] = None,
                     text_query: Optional[str] = None,
                     k: int = 10) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector similarity and filters
        Perfect for queries like "list all incidents about database"
        """
        
        # Build filter
        qdrant_filter = self._build_filter(filters) if filters else Filter()
        
        # Add text search to filter if provided
        if text_query:
            text_conditions = []
            for word in text_query.split():
                text_conditions.append(
                    FieldCondition(
                        key="text",
                        match=MatchText(text=word)
                    )
                )
            
            if text_conditions:
                if qdrant_filter.must:
                    qdrant_filter.must.extend(text_conditions)
                else:
                    qdrant_filter.must = text_conditions
        
        # If we have a query vector, do similarity search with filters
        if query_vector:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=k,
                query_filter=qdrant_filter,
                with_payload=True
            )
            
            return [{'score': r.score, **r.payload} for r in results]
        
        # Otherwise, just filter
        else:
            results = []
            offset = None
            
            while len(results) < k:
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=qdrant_filter,
                    limit=min(k - len(results), 100),
                    offset=offset,
                    with_payload=True
                )
                
                results.extend(response[0])
                offset = response[1]
                
                if offset is None:
                    break
            
            return [r.payload for r in results[:k]]
    
    def _extract_doc_type(self, metadata: Dict[str, Any]) -> str:
        """Extract document type from metadata"""
        text = metadata.get('text', '').upper()
        
        if 'INC' in text:
            return 'incident'
        elif 'CHG' in text:
            return 'change'
        elif 'PRB' in text:
            return 'problem'
        elif 'REQ' in text:
            return 'request'
        elif 'TASK' in text:
            return 'task'
        else:
            return 'other'
    
    def _contains_incident(self, text: str) -> bool:
        """Check if text contains incident reference"""
        import re
        return bool(re.search(r'INC\d{6}', text, re.IGNORECASE))
    
    def _extract_incident_ids(self, text: str) -> List[str]:
        """Extract all incident IDs from text"""
        import re
        return re.findall(r'INC\d{6}', text, re.IGNORECASE)
    
    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from dictionary"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, list):
                # Match any of the values
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchAny(any=value)
                    )
                )
            elif isinstance(value, dict):
                # Range query
                if 'gte' in value or 'lte' in value:
                    conditions.append(
                        FieldCondition(
                            key=key,
                            range=Range(
                                gte=value.get('gte'),
                                lte=value.get('lte')
                            )
                        )
                    )
            else:
                # Exact match
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
        
        return Filter(must=conditions) if conditions else None
    
    def delete_by_filter(self, filters: Dict[str, Any]) -> int:
        """Delete vectors matching filters"""
        qdrant_filter = self._build_filter(filters)
        
        result = self.client.delete(
            collection_name=self.collection_name,
            points_selector=qdrant_filter
        )
        
        return result.status == UpdateStatus.COMPLETED
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics"""
        info = self.client.get_collection(self.collection_name)
        
        return {
            'vectors_count': info.vectors_count,
            'indexed_vectors_count': info.indexed_vectors_count,
            'points_count': info.points_count,
            'segments_count': info.segments_count,
            'status': info.status,
            'config': {
                'dimension': info.config.params.vectors.size,
                'distance': info.config.params.vectors.distance,
                'on_disk': info.config.params.vectors.on_disk
            }
        }


"""
Enhanced Query Engine with Qdrant
Handles both semantic search and structured queries efficiently
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

class QdrantQueryEngine:
    """Query engine optimized for Qdrant's capabilities"""
    
    def __init__(self, qdrant_store, embedder, llm_client, config):
        self.qdrant_store = qdrant_store
        self.embedder = embedder
        self.llm_client = llm_client
        self.config = config
        
    def process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """Process query with intelligent routing"""
        
        # Detect query type
        query_type = self._detect_query_type(query)
        logging.info(f"Query type detected: {query_type}")
        
        if query_type == "listing":
            return self._handle_listing_query(query)
        elif query_type == "filtered_search":
            return self._handle_filtered_search(query)
        elif query_type == "aggregation":
            return self._handle_aggregation_query(query)
        else:
            return self._handle_semantic_search(query, **kwargs)
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query"""
        query_lower = query.lower()
        
        # Listing patterns
        listing_patterns = [
            r'\b(list all|show all|get all|display all)\b',
            r'\ball\s+(incidents?|changes?|problems?|requests?|tasks?)\b',
            r'\b(complete list|full list|entire list)\b'
        ]
        
        for pattern in listing_patterns:
            if re.search(pattern, query_lower):
                return "listing"
        
        # Filtered search patterns
        filter_patterns = [
            r'\b(incidents?|changes?|problems?).*about\b',
            r'\b(related to|concerning|regarding)\b',
            r'\b(with status|in state|assigned to)\b',
            r'\b(created|modified|updated)\s+(before|after|between)\b'
        ]
        
        for pattern in filter_patterns:
            if re.search(pattern, query_lower):
                return "filtered_search"
        
        # Aggregation patterns
        agg_patterns = [
            r'\b(how many|count|number of|total)\b',
            r'\b(statistics|stats|summary)\b',
            r'\b(group by|per|by category)\b'
        ]
        
        for pattern in agg_patterns:
            if re.search(pattern, query_lower):
                return "aggregation"
        
        return "semantic_search"
    
    def _handle_listing_query(self, query: str) -> Dict[str, Any]:
        """Handle listing queries using Qdrant's scroll API"""
        
        # Extract item type
        item_type = self._extract_item_type(query)
        
        if item_type == "incidents":
            # Get all incidents efficiently
            incidents = self.qdrant_store.list_all_incidents()
            
            # Format response
            response = self._format_listing_response(incidents, "incidents")
            
            return {
                'query': query,
                'response': response,
                'confidence_score': 1.0,
                'confidence_level': 'high',
                'sources': incidents,
                'total_sources': len(incidents),
                'query_type': 'listing',
                'method': 'qdrant_scroll',
                'timestamp': datetime.now().isoformat()
            }
        
        # Handle other item types similarly
        filters = self._get_filters_for_item_type(item_type)
        results = self._get_all_by_filter(filters)
        
        response = self._format_listing_response(results, item_type)
        
        return {
            'query': query,
            'response': response,
            'confidence_score': 1.0,
            'confidence_level': 'high',
            'sources': results,
            'total_sources': len(results),
            'query_type': 'listing',
            'method': 'qdrant_filter',
            'timestamp': datetime.now().isoformat()
        }
    
    def _handle_filtered_search(self, query: str) -> Dict[str, Any]:
        """Handle queries with specific filters"""
        
        # Extract filters from query
        filters = self._extract_filters_from_query(query)
        
        # Extract search terms
        search_terms = self._extract_search_terms(query)
        
        # Perform hybrid search
        if search_terms:
            # Embed search terms for similarity
            query_vector = self.embedder.embed_text(" ".join(search_terms))
            
            results = self.qdrant_store.hybrid_search(
                query_vector=query_vector,
                filters=filters,
                text_query=" ".join(search_terms),
                k=50  # Get more results for filtered queries
            )
        else:
            # Just use filters
            results = self.qdrant_store.hybrid_search(
                filters=filters,
                k=100
            )
        
        # Generate response
        response = self._generate_filtered_response(query, results, filters)
        
        return {
            'query': query,
            'response': response,
            'confidence_score': 0.9,
            'confidence_level': 'high',
            'sources': results[:20],  # Limit sources in response
            'total_sources': len(results),
            'filters_applied': filters,
            'query_type': 'filtered_search',
            'method': 'qdrant_hybrid',
            'timestamp': datetime.now().isoformat()
        }
    
    def _handle_aggregation_query(self, query: str) -> Dict[str, Any]:
        """Handle aggregation queries"""
        
        # Get aggregated data
        counts = self.qdrant_store.aggregate_by_type()
        
        # Format response
        response = self._format_aggregation_response(query, counts)
        
        return {
            'query': query,
            'response': response,
            'confidence_score': 1.0,
            'confidence_level': 'high',
            'aggregation_results': counts,
            'query_type': 'aggregation',
            'method': 'qdrant_aggregation',
            'timestamp': datetime.now().isoformat()
        }
    
    def _handle_semantic_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Handle standard semantic search queries"""
        
        # Embed query
        query_vector = self.embedder.embed_text(query)
        
        # Search
        results = self.qdrant_store.search(
            query_vector=query_vector,
            k=kwargs.get('top_k', 20)
        )
        
        # Generate response using LLM
        response = self._generate_llm_response(query, results)
        
        return {
            'query': query,
            'response': response,
            'confidence_score': self._calculate_confidence(results),
            'confidence_level': 'high' if len(results) > 5 else 'medium',
            'sources': results,
            'total_sources': len(results),
            'query_type': 'semantic_search',
            'method': 'qdrant_similarity',
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_filters_from_query(self, query: str) -> Dict[str, Any]:
        """Extract filters from natural language query"""
        filters = {}
        
        # Extract item type filters
        if 'incident' in query.lower():
            filters['doc_type'] = 'incident'
        elif 'change' in query.lower():
            filters['doc_type'] = 'change'
        
        # Extract text filters
        about_match = re.search(r'about\s+([^.?,]+)', query.lower())
        if about_match:
            filters['text_contains'] = about_match.group(1).strip()
        
        # Extract status filters
        status_match = re.search(r'with status\s+(\w+)', query.lower())
        if status_match:
            filters['status'] = status_match.group(1)
        
        return filters
    
    def _format_listing_response(self, items: List[Dict], item_type: str) -> str:
        """Format listing response"""
        if not items:
            return f"No {item_type} found in the system."
        
        response_parts = [f"Found {len(items)} {item_type} in the system:\n"]
        
        # Group by source if many items
        if len(items) > 20:
            by_source = {}
            for item in items:
                sources = item.get('sources', ['Unknown'])
                for source in sources:
                    if source not in by_source:
                        by_source[source] = []
                    by_source[source].append(item['id'])
            
            for source, ids in sorted(by_source.items()):
                response_parts.append(f"\nFrom {source}:")
                response_parts.append(f"  {', '.join(sorted(ids[:10]))}")
                if len(ids) > 10:
                    response_parts.append(f"  ... and {len(ids) - 10} more")
        else:
            # List all items
            for item in sorted(items, key=lambda x: x['id']):
                response_parts.append(f"\n• {item['id']}")
                if item.get('first_mention'):
                    desc = item['first_mention'][:100] + "..."
                    response_parts.append(f"  {desc}")
                response_parts.append(f"  Sources: {', '.join(item.get('sources', ['Unknown']))}")
                response_parts.append(f"  Occurrences: {item.get('occurrence_count', 1)}")
        
        return "\n".join(response_parts)
    
    def _get_all_by_filter(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all items matching filters using scroll"""
        results = []
        offset = None
        
        qdrant_filter = self.qdrant_store._build_filter(filters)
        
        while True:
            response = self.qdrant_store.client.scroll(
                collection_name=self.qdrant_store.collection_name,
                scroll_filter=qdrant_filter,
                limit=100,
                offset=offset,
                with_payload=True
            )
            
            results.extend([r.payload for r in response[0]])
            offset = response[1]
            
            if offset is None:
                break
        
        return results
    
    def _extract_item_type(self, query: str) -> str:
        """Extract item type from query"""
        query_lower = query.lower()
        
        types = {
            'incidents': ['incident', 'incidents'],
            'changes': ['change', 'changes'],
            'problems': ['problem', 'problems'],
            'requests': ['request', 'requests'],
            'tasks': ['task', 'tasks']
        }
        
        for item_type, keywords in types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return item_type
        
        return 'items'


"""
Migration script from FAISS to Qdrant
"""
import logging
from tqdm import tqdm
import numpy as np

class FAISSToQdrantMigration:
    """Migrate existing FAISS index to Qdrant"""
    
    def __init__(self, faiss_store, qdrant_store):
        self.faiss_store = faiss_store
        self.qdrant_store = qdrant_store
        
    def migrate(self, batch_size: int = 100):
        """Migrate all vectors and metadata from FAISS to Qdrant"""
        
        logging.info("Starting migration from FAISS to Qdrant...")
        
        # Get total vectors
        total_vectors = self.faiss_store.optimized_index.index.ntotal
        logging.info(f"Total vectors to migrate: {total_vectors}")
        
        # Migrate in batches
        migrated = 0
        failed = 0
        
        with tqdm(total=total_vectors) as pbar:
            for start_idx in range(0, total_vectors, batch_size):
                end_idx = min(start_idx + batch_size, total_vectors)
                
                try:
                    # Extract vectors from FAISS
                    vectors = []
                    metadata_list = []
                    
                    for idx in range(start_idx, end_idx):
                        # Get vector
                        vector = self.faiss_store.optimized_index.index.reconstruct(idx)
                        
                        # Get metadata
                        vector_id = self.faiss_store.index_to_id.get(idx)
                        if vector_id is not None:
                            metadata = self.faiss_store.id_to_metadata.get(vector_id)
                            if metadata and not metadata.get('deleted', False):
                                vectors.append(vector.tolist())
                                metadata_list.append(metadata)
                    
                    # Add to Qdrant
                    if vectors:
                        self.qdrant_store.add_vectors(vectors, metadata_list)
                        migrated += len(vectors)
                    
                    pbar.update(end_idx - start_idx)
                    
                except Exception as e:
                    logging.error(f"Failed to migrate batch {start_idx}-{end_idx}: {e}")
                    failed += (end_idx - start_idx)
                    pbar.update(end_idx - start_idx)
        
        logging.info(f"Migration completed: {migrated} vectors migrated, {failed} failed")
        
        # Verify migration
        qdrant_info = self.qdrant_store.get_collection_info()
        logging.info(f"Qdrant collection now has {qdrant_info['vectors_count']} vectors")
        
        return {
            'migrated': migrated,
            'failed': failed,
            'total': total_vectors,
            'success_rate': migrated / max(total_vectors, 1)
        }

# Usage example
def migrate_to_qdrant(config_path: str):
    """Main migration function"""
    
    # Load existing FAISS store
    from rag_system.src.storage.faiss_store import FAISSStore
    faiss_store = FAISSStore(
        index_path="data/vectors/faiss_index.bin",
        dimension=1024
    )
    
    # Create Qdrant store
    qdrant_store = QdrantVectorStore(
        url="localhost:6333",  # Or your Qdrant server URL
        collection_name="rag_documents",
        dimension=1024
    )
    
    # Run migration
    migration = FAISSToQdrantMigration(faiss_store, qdrant_store)
    results = migration.migrate(batch_size=100)
    
    print(f"Migration results: {results}")
    
    # Update configuration to use Qdrant
    import json
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    config['vector_store'] = {
        'type': 'qdrant',
        'url': 'localhost:6333',
        'collection_name': 'rag_documents'
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Configuration updated to use Qdrant")

if __name__ == "__main__":
    migrate_to_qdrant("system_config.json")                

