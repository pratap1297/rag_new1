"""
Migration script from FAISS to Qdrant
"""
import logging
import json
from tqdm import tqdm
import numpy as np
from typing import Dict, Any
from pathlib import Path

from .faiss_store import FAISSStore
from .qdrant_store import QdrantVectorStore

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

def migrate_to_qdrant(config_path: str = "rag_system/data/config/system_config.json"):
    """Main migration function"""
    
    # Load current config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Initialize FAISS store
    faiss_index_path = config['database']['faiss_index_path']
    dimension = config['embedding']['dimension']
    
    faiss_store = FAISSStore(
        index_path=faiss_index_path,
        dimension=dimension
    )
    
    # Initialize Qdrant store
    qdrant_store = QdrantVectorStore(
        url="localhost:6333",  # Default Qdrant URL
        collection_name="rag_documents",
        dimension=dimension
    )
    
    # Run migration
    migration = FAISSToQdrantMigration(faiss_store, qdrant_store)
    results = migration.migrate(batch_size=100)
    
    print(f"Migration results: {results}")
    
    # Update configuration to use Qdrant
    config['vector_store'] = {
        'type': 'qdrant',
        'url': 'localhost:6333',
        'collection_name': 'rag_documents',
        'dimension': dimension
    }
    
    # Backup original config
    backup_path = config_path + '.backup'
    with open(backup_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Write new config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration updated to use Qdrant (backup saved to {backup_path})")
    
    return results

if __name__ == "__main__":
    migrate_to_qdrant() 