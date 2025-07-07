# FAISS to Qdrant Migration Plan

## Overview

This document outlines the comprehensive plan to migrate the RAG system from FAISS to Qdrant vector store. The system is currently in a transitional state where both FAISS and Qdrant can be used, but many components still have direct references to FAISS.

## Current State Analysis

### Configuration Status
- **Default Configuration**: The system is configured to use Qdrant by default (`VectorStoreConfig.type = "qdrant"`)
- **Dependency Container**: Has logic to choose between FAISS and Qdrant based on configuration
- **Qdrant Store**: Implements compatibility methods to match FAISS interface
- **Missing Config File**: `system_config.json` was deleted, system will use defaults

### Components Still Using FAISS

1. **Core Components**:
   - `IngestionEngine` - Constructor parameter `faiss_store`
   - `QueryEngine` - Constructor parameter `faiss_store`
   - API endpoints - Multiple direct calls to `faiss_store`

2. **Test Files**: 
   - 20+ test files directly importing and using `FAISSStore`
   - Test constructors expecting `faiss_store` parameter

3. **Legacy References**:
   - Multiple scripts and utilities still reference FAISS
   - Some components have both `faiss_store` and `vector_store` attributes

## Migration Strategy

### Phase 1: Configuration and Service Setup

#### Task 1.1: Verify Qdrant Service
```bash
# Check if Qdrant is running
curl http://localhost:6333/health
```

#### Task 1.2: Create System Configuration
Create `rag_new/data/config/system_config.json`:
```json
{
  "environment": "development",
  "debug": false,
  "vector_store": {
    "type": "qdrant",
    "url": "localhost:6333",
    "collection_name": "rag_documents",
    "dimension": 1024,
    "on_disk_storage": true,
    "distance": "cosine"
  },
  "embedding": {
    "provider": "azure",
    "model_name": "Cohere-embed-v3-english",
    "dimension": 1024
  }
}
```

### Phase 2: Core Component Updates

#### Task 2.1: Update IngestionEngine
**File**: `rag_new/rag_system/src/ingestion/ingestion_engine.py`
- Change constructor parameter from `faiss_store` to `vector_store`
- Update all internal references
- Update dependency injection calls

#### Task 2.2: Update QueryEngine
**File**: `rag_new/rag_system/src/retrieval/query_engine.py`
- Change constructor parameter from `faiss_store` to `vector_store`
- Update all internal references
- Update dependency injection calls

#### Task 2.3: Update Dependency Container
**File**: `rag_new/rag_system/src/core/dependency_container.py`
- Update factory functions to use consistent `vector_store` naming
- Remove legacy `create_faiss_store` function or make it an alias

### Phase 3: API and Interface Updates

#### Task 3.1: Update API Endpoints
**Files**: 
- `rag_new/rag_system/src/api/main.py`
- `rag_new/rag_system/src/api/management_api.py`

Changes needed:
- Replace `faiss_store` references with `vector_store`
- Update dependency injection calls
- Ensure all vector store operations use the generic interface

#### Task 3.2: Update Management Endpoints
Ensure all management API endpoints work with both FAISS and Qdrant through the generic interface.

### Phase 4: Test Suite Updates

#### Task 4.1: Update Test Files
**Files to update** (20+ files):
- All files in `rag_new/rag_system/tests/` that import `FAISSStore`
- Change imports to use `QdrantVectorStore` or generic `vector_store`
- Update constructor calls and parameter names

#### Task 4.2: Create Qdrant Test Utilities
Create helper functions for tests that work with both FAISS and Qdrant.

### Phase 5: Verification and Testing

#### Task 5.1: Qdrant Interface Verification
Verify that `QdrantVectorStore` implements all required methods:
- `add_vectors()`
- `search()`
- `search_with_metadata()`
- `get_stats()`
- `delete_vectors()`
- `get_vector_metadata()`
- `find_vectors_by_doc_path()`
- `delete_vectors_by_doc_path()`
- `clear_index()`
- `backup_index()`
- `restore_index()`
- `id_to_metadata` property

#### Task 5.2: Data Migration (if needed)
If existing FAISS data needs to be migrated:
1. Export vectors and metadata from FAISS
2. Import into Qdrant collection
3. Verify data integrity

### Phase 6: Cleanup and Optimization

#### Task 6.1: Remove FAISS Dependencies
- Remove unused FAISS imports
- Update requirements.txt to remove FAISS if not needed
- Clean up legacy code paths

#### Task 6.2: Documentation Updates
- Update README files
- Update configuration documentation
- Update deployment guides

## Implementation Details

### Qdrant Service Requirements

1. **Installation**:
   ```bash
   # Using Docker
   docker run -p 6333:6333 qdrant/qdrant
   
   # Or using pip
   pip install qdrant-client
   ```

2. **Configuration**:
   - Default URL: `localhost:6333`
   - Collection name: `rag_documents`
   - Vector dimension: 1024 (matching current embedding model)
   - Distance metric: Cosine

### Interface Compatibility

The `QdrantVectorStore` class already implements compatibility methods:

```python
# FAISS-compatible methods
def add_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]
def search_with_metadata(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]
def get_vector_metadata(self, vector_id) -> Optional[Dict[str, Any]]
def delete_vectors(self, vector_ids: List[str]) -> bool

# Property compatibility
@property
def id_to_metadata(self) -> Dict[str, Any]
```

### Configuration Migration

The system already supports configuration-based vector store selection:

```python
# In dependency_container.py
vector_store_type = vector_store_config.type  # "qdrant" or "faiss"

if vector_store_type.lower() == 'qdrant':
    vector_store = QdrantVectorStore(...)
else:
    vector_store = FAISSStore(...)
```

## Risk Assessment

### Low Risk
- Configuration changes (reversible)
- Parameter name changes (straightforward)
- Test file updates (isolated)

### Medium Risk
- API endpoint changes (requires testing)
- Data migration (if existing data present)
- Interface compatibility (already implemented)

### High Risk
- Production deployment (requires backup strategy)
- Performance differences (needs benchmarking)

## Rollback Plan

1. **Configuration Rollback**: Change `vector_store.type` back to `"faiss"`
2. **Code Rollback**: Revert parameter names if needed
3. **Data Rollback**: Restore FAISS index from backup if migration was performed

## Success Criteria

1. ✅ All API endpoints work with Qdrant
2. ✅ All tests pass with Qdrant
3. ✅ Query performance is comparable or better
4. ✅ Data integrity is maintained
5. ✅ System is stable under load
6. ✅ No FAISS references remain in active code paths

## Timeline

- **Phase 1**: 1-2 hours (Configuration and setup)
- **Phase 2**: 2-3 hours (Core component updates)
- **Phase 3**: 2-3 hours (API updates)
- **Phase 4**: 3-4 hours (Test suite updates)
- **Phase 5**: 2-3 hours (Verification and testing)
- **Phase 6**: 1-2 hours (Cleanup)

**Total Estimated Time**: 11-17 hours

## Next Steps

1. Start with Phase 1: Verify Qdrant service and create configuration
2. Update core components (IngestionEngine, QueryEngine)
3. Update API endpoints systematically
4. Run comprehensive tests
5. Perform cleanup and optimization

This migration plan ensures a systematic transition from FAISS to Qdrant while maintaining system stability and functionality. 