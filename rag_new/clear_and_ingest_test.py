#!/usr/bin/env python3
"""
Clear Qdrant store and ingest test data, then run various query tests
"""
import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Add the rag_system to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

from storage.qdrant_store import QdrantVectorStore
from core.dependency_container import DependencyContainer
from core.config_manager import ConfigManager
from retrieval.qdrant_query_engine import QdrantQueryEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_qdrant_store():
    """Clear the Qdrant store completely"""
    logger.info("=== Clearing Qdrant Store ===")
    
    try:
        # Initialize Qdrant store directly
        qdrant_store = QdrantVectorStore(
            url="localhost:6333",
            collection_name="rag_documents",
            dimension=1024
        )
        
        # Clear the collection
        qdrant_store.clear_index()
        
        # Verify it's empty
        info = qdrant_store.get_collection_info()
        logger.info(f"Qdrant store cleared. Current vectors: {info['vectors_count']}")
        
        # Also clear metadata store to remove duplicate detection
        try:
            import shutil
            from pathlib import Path
            metadata_dir = Path("data/metadata")
            if metadata_dir.exists():
                shutil.rmtree(metadata_dir)
                logger.info("Metadata store cleared")
        except Exception as e:
            logger.warning(f"Failed to clear metadata store: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear Qdrant store: {e}")
        return False

def ingest_test_data():
    """Ingest test data from document_generator/test_data"""
    logger.info("=== Ingesting Test Data ===")
    
    try:
        # Initialize the system
        from core.dependency_container import register_core_services, DependencyContainer
        
        container = DependencyContainer()
        register_core_services(container)
        
        # Get the ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        
        # Test data directory
        test_data_dir = Path("document_generator/test_data")
        if not test_data_dir.exists():
            logger.error(f"Test data directory not found at {test_data_dir}")
            return False
        

        
        logger.info(f"Using test data directory: {test_data_dir}")
        
        # List available files
        test_files = list(test_data_dir.glob("*"))
        logger.info(f"Found {len(test_files)} test files:")
        for file in test_files:
            logger.info(f"  - {file.name} ({file.stat().st_size} bytes)")
        
        # Ingest each file
        ingestion_results = []
        for file_path in test_files:
            if file_path.is_file():
                logger.info(f"\nIngesting: {file_path.name}")
                try:
                    result = ingestion_engine.ingest_file(str(file_path))
                    ingestion_results.append({
                        'file': file_path.name,
                        'success': True,
                        'chunks': result.get('chunks_added', 0),
                        'vectors': result.get('vectors_added', 0)
                    })
                    logger.info(f"✓ Successfully ingested {file_path.name}: {result.get('chunks_added', 0)} chunks")
                    
                except Exception as e:
                    logger.error(f"✗ Failed to ingest {file_path.name}: {e}")
                    ingestion_results.append({
                        'file': file_path.name,
                        'success': False,
                        'error': str(e)
                    })
        
        # Summary
        successful = [r for r in ingestion_results if r['success']]
        failed = [r for r in ingestion_results if not r['success']]
        
        logger.info(f"\n=== Ingestion Summary ===")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")
        
        total_chunks = sum(r.get('chunks', 0) for r in successful)
        total_vectors = sum(r.get('vectors', 0) for r in successful)
        logger.info(f"Total chunks added: {total_chunks}")
        logger.info(f"Total vectors added: {total_vectors}")
        
        if failed:
            logger.info("\nFailed files:")
            for failure in failed:
                logger.info(f"  - {failure['file']}: {failure['error']}")
        
        return len(successful) > 0
        
    except Exception as e:
        logger.error(f"Failed to ingest test data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_queries():
    """Test various query types with the ingested data"""
    logger.info("\n=== Testing Queries ===")
    
    try:
        # Initialize the system
        from core.dependency_container import register_core_services, DependencyContainer
        
        container = DependencyContainer()
        register_core_services(container)
        
        # Get components
        vector_store = container.get('vector_store')
        query_engine = container.get('query_engine')
        
        # Check data exists
        info = vector_store.get_collection_info()
        logger.info(f"Collection status: {info['status']}")
        logger.info(f"Total vectors: {info['vectors_count']}")
        
        if info['vectors_count'] == 0:
            logger.warning("No vectors found in collection - cannot test queries")
            return False
        
        # Test queries
        test_queries = [
            "List all incidents",
            "Show me network layout information", 
            "What facility managers are available?",
            "Tell me about building network configurations",
            "List all changes from ServiceNow",
            "How many documents do we have?",
            "Show me incident INC001234"
        ]
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n--- Query {i}: {query} ---")
            
            try:
                # Process query
                result = query_engine.process_query(query)
                
                # Log results
                logger.info(f"Query type: {result.get('query_type', 'unknown')}")
                logger.info(f"Method used: {result.get('method', 'unknown')}")
                logger.info(f"Sources found: {result.get('total_sources', 0)}")
                logger.info(f"Confidence: {result.get('confidence_level', 'unknown')}")
                
                # Show response preview
                response = result.get('response', '')
                if len(response) > 200:
                    response_preview = response[:200] + "..."
                else:
                    response_preview = response
                
                logger.info(f"Response preview: {response_preview}")
                
                results.append({
                    'query': query,
                    'success': True,
                    'type': result.get('query_type'),
                    'sources': result.get('total_sources', 0),
                    'method': result.get('method')
                })
                
            except Exception as e:
                logger.error(f"Query failed: {e}")
                results.append({
                    'query': query,
                    'success': False,
                    'error': str(e)
                })
        
        # Summary
        successful_queries = [r for r in results if r['success']]
        failed_queries = [r for r in results if not r['success']]
        
        logger.info(f"\n=== Query Test Summary ===")
        logger.info(f"Successful queries: {len(successful_queries)}/{len(test_queries)}")
        
        if successful_queries:
            logger.info("\nQuery methods used:")
            methods = {}
            for result in successful_queries:
                method = result.get('method', 'unknown')
                methods[method] = methods.get(method, 0) + 1
            
            for method, count in methods.items():
                logger.info(f"  - {method}: {count} queries")
        
        if failed_queries:
            logger.info("\nFailed queries:")
            for failure in failed_queries:
                logger.info(f"  - '{failure['query']}': {failure['error']}")
        
        return len(successful_queries) == len(test_queries)
        
    except Exception as e:
        logger.error(f"Failed to test queries: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_advanced_features():
    """Test advanced Qdrant features"""
    logger.info("\n=== Testing Advanced Features ===")
    
    try:
        # Initialize the system
        from core.dependency_container import register_core_services, DependencyContainer
        
        container = DependencyContainer()
        register_core_services(container)
        vector_store = container.get('vector_store')
        
        # Test 1: List all incidents
        logger.info("\n1. Testing list_all_incidents():")
        incidents = vector_store.list_all_incidents()
        logger.info(f"Found {len(incidents)} incidents")
        for incident in incidents[:3]:  # Show first 3
            logger.info(f"  - {incident.get('id', 'Unknown')}: {incident.get('first_mention', '')[:50]}...")
        
        # Test 2: Aggregation by type
        logger.info("\n2. Testing aggregate_by_type():")
        counts = vector_store.aggregate_by_type()
        logger.info("Document type counts:")
        for doc_type, count in counts.items():
            logger.info(f"  - {doc_type}: {count}")
        
        # Test 3: Pattern search
        logger.info("\n3. Testing pattern search:")
        pattern_results = vector_store.get_by_pattern("network", "text")
        logger.info(f"Found {len(pattern_results)} documents mentioning 'network'")
        
        # Test 4: Hybrid search
        logger.info("\n4. Testing hybrid search:")
        hybrid_results = vector_store.hybrid_search(
            filters={'doc_type': 'incident'},
            text_query="network problem",
            k=5
        )
        logger.info(f"Found {len(hybrid_results)} results for network incident search")
        
        # Test 5: Collection info
        logger.info("\n5. Collection information:")
        info = vector_store.get_collection_info()
        logger.info(f"  - Status: {info['status']}")
        logger.info(f"  - Vectors: {info['vectors_count']}")
        logger.info(f"  - Segments: {info['segments_count']}")
        logger.info(f"  - Dimension: {info['config']['dimension']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to test advanced features: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main execution function"""
    logger.info("Starting Qdrant clear and ingest test")
    
    # Step 1: Clear the store
    if not clear_qdrant_store():
        logger.error("Failed to clear Qdrant store")
        return False
    
    # Step 2: Ingest test data
    if not ingest_test_data():
        logger.error("Failed to ingest test data")
        return False
    
    # Step 3: Test queries
    if not test_queries():
        logger.warning("Some queries failed")
    
    # Step 4: Test advanced features
    if not test_advanced_features():
        logger.warning("Advanced features test failed")
    
    logger.info("\n=== Test Complete ===")
    logger.info("Qdrant store has been cleared, test data ingested, and queries tested")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 