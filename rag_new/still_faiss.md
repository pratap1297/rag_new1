Based on the search, the following non-test files are using FAISS. A number of these are related to the migration from FAISS to Qdrant, but several core components still have references to FAISS.

Key files with FAISS usage:

* **`rag_new/rag_system/src/core/dependency_container.py`**: This file is critical as it contains the logic for creating the vector store. It has a factory for the vector store that can create either a `FAISSStore` or a `Qdrant` store based on the configuration. This is the central point where the switch between the two can be made.

* **`rag_new/rag_system/src/storage/faiss_store.py`**: This is the implementation of the FAISS vector store itself.

* **`rag_new/rag_system/src/ingestion/ingestion_engine.py`** and **`rag_new/rag_system/src/retrieval/query_engine.py`**: These components are initialized with a `faiss_store` and use it for their operations.

* **`rag_new/rag_system/src/api/main.py`**: The main API file contains numerous direct calls to `faiss_store` for various operations like health checks, stats, and search.

* **`rag_new/rag_system/src/storage/qdrant_store.py`**: This file contains compatibility methods to match the FAISS interface, indicating that other parts of the code might still be expecting the FAISS API.

* **Scripts**: Files in `rag_new/rag_system/scripts/` such as `migrate_embeddings.py` and `setup.py` also contain FAISS references, mostly for migration and setup purposes.

It appears the system is in a transitional state where both FAISS and Qdrant can be used, and the selection is likely controlled by a configuration setting. Many components still hold direct references to `FAISSStore`.