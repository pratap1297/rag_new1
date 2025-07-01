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
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract search terms from query"""
        # Simple implementation - extract words after "about", "regarding", etc.
        terms = []
        
        about_match = re.search(r'(?:about|regarding|concerning)\s+([^.?,]+)', query.lower())
        if about_match:
            terms.extend(about_match.group(1).strip().split())
        
        return terms
    
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
    
    def _generate_filtered_response(self, query: str, results: List[Dict], filters: Dict) -> str:
        """Generate response for filtered search"""
        if not results:
            return f"No results found matching your criteria."
        
        response_parts = [f"Found {len(results)} results matching your search:\n"]
        
        for i, result in enumerate(results[:10], 1):
            content = result.get('content', result.get('text', ''))[:200]
            source = result.get('filename', result.get('source_file', 'Unknown'))
            
            response_parts.append(f"\n{i}. From {source}:")
            response_parts.append(f"   {content}...")
        
        if len(results) > 10:
            response_parts.append(f"\n... and {len(results) - 10} more results")
        
        return "\n".join(response_parts)
    
    def _format_aggregation_response(self, query: str, counts: Dict[str, int]) -> str:
        """Format aggregation response"""
        total = sum(counts.values())
        
        response_parts = [f"Document statistics:\n"]
        response_parts.append(f"Total documents: {total}\n")
        
        for doc_type, count in sorted(counts.items()):
            percentage = (count / total * 100) if total > 0 else 0
            response_parts.append(f"• {doc_type.title()}: {count} ({percentage:.1f}%)")
        
        return "\n".join(response_parts)
    
    def _generate_llm_response(self, query: str, results: List[Dict]) -> str:
        """Generate LLM response using search results"""
        if not results:
            return "I couldn't find any relevant information to answer your question."
        
        # Build context from top results
        context_parts = []
        for i, result in enumerate(results[:5], 1):
            content = result.get('content', result.get('text', ''))[:300]
            source = result.get('filename', result.get('source_file', 'Unknown'))
            
            context_parts.append(f"Source {i} ({source}): {content}")
        
        context = "\n\n".join(context_parts)
        
        # Create prompt
        prompt = f"""Based on the following context, please answer the user's question:

Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to fully answer the question, please say so.

Answer:"""
        
        try:
            # Generate response using LLM
            response = self.llm_client.generate(prompt)
            return response
        except Exception as e:
            logging.error(f"LLM generation failed: {e}")
            return f"I found relevant information but couldn't generate a proper response. Error: {e}"
    
    def _calculate_confidence(self, results: List[Dict]) -> float:
        """Calculate confidence score based on results"""
        if not results:
            return 0.0
        
        # Simple confidence calculation based on number and quality of results
        avg_score = sum(r.get('similarity_score', 0) for r in results) / len(results)
        count_factor = min(len(results) / 10, 1.0)  # Normalize by expected result count
        
        return min(avg_score * count_factor, 1.0)
    
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
    
    def _get_filters_for_item_type(self, item_type: str) -> Dict[str, Any]:
        """Get filters for specific item type"""
        type_mapping = {
            'incidents': {'doc_type': 'incident'},
            'changes': {'doc_type': 'change'},
            'problems': {'doc_type': 'problem'},
            'requests': {'doc_type': 'request'},
            'tasks': {'doc_type': 'task'}
        }
        
        return type_mapping.get(item_type, {})
    
    def _get_all_by_filter(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all items matching filters using scroll"""
        results = []
        offset = None
        
        qdrant_filter = self.qdrant_store._build_filter(filters) if filters else None
        
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