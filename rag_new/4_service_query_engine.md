# 4_service_query_engine.md - Query Engine Service Documentation

## Query Engine Service Documentation

### Overview

The Query Engine (`rag_system/src/retrieval/query_engine.py`) is a critical component of the RAG system, responsible for processing user queries, retrieving relevant information from the knowledge base, and orchestrating the generation of coherent responses. It acts as the central intelligence unit for information retrieval, leveraging advanced techniques to ensure accuracy and relevance.

### Key Responsibilities

*   **Query Processing**: Receives user queries and prepares them for search.
*   **Query Enhancement**: Utilizes a `QueryEnhancer` to reformulate, expand, and generate semantic variants of the query to improve search recall.
*   **Query Embedding**: Converts the processed query into a vector embedding using the `Embedder`.
*   **Vector Search**: Performs similarity searches against the vector store (`FAISSStore` or `QdrantVectorStore`) to identify relevant document chunks.
*   **Reranking**: Applies a `Reranker` to re-order initial search results, improving precision and relevance.
*   **Source Diversity**: Implements logic to select a diverse set of sources, ensuring comprehensive coverage and preventing over-reliance on a single document.
*   **Context Formulation**: Assembles the retrieved and reranked document chunks into a coherent context for the Large Language Model (LLM).
*   **LLM Response Generation**: Passes the query and context to the `LLMClient` to generate a natural language response.
*   **Confidence Scoring**: Calculates a confidence score for the generated response based on the quality and diversity of retrieved sources.
*   **Conversation Awareness**: Integrates with conversation context to provide more relevant and natural responses in multi-turn interactions.

### Components

The Query Engine interacts with several key components to perform its functions:

#### 1. `Embedder` (`rag_system/src/ingestion/embedder.py`)

*   **Role**: Converts text into numerical vector embeddings.
*   **Interaction**: The Query Engine sends the user's query to the `Embedder` to obtain a query vector, which is then used for similarity search in the vector store.

#### 2. `FAISSStore` / `QdrantVectorStore` (`rag_system/src/storage/faiss_store.py` / `rag_system/src/storage/qdrant_store.py`)

*   **Role**: Stores and retrieves vector embeddings.
*   **Interaction**: The Query Engine performs similarity searches against the `FAISSStore` (or `QdrantVectorStore`) using the query vector to find the most relevant document chunks. It also retrieves the associated metadata for these chunks.

#### 3. `LLMClient` (`rag_system/src/retrieval/llm_client.py`)

*   **Role**: Interfaces with various Large Language Models (LLMs) for text generation.
*   **Interaction**: The Query Engine sends the user's query and the retrieved context to the `LLMClient`. The `LLMClient` then generates a natural language response based on this input.

#### 4. `PersistentJSONMetadataStore` (`rag_system/src/storage/persistent_metadata_store.py`)

*   **Role**: Provides access to detailed metadata for documents and chunks.
*   **Interaction**: The Query Engine uses the `MetadataStore` to retrieve additional metadata for the retrieved chunks, enriching the context provided to the LLM and for source attribution.

#### 5. `QueryEnhancer` (`rag_system/src/retrieval/query_enhancer.py`)

*   **Role**: Improves the effectiveness of the search by transforming the user's query.
*   **Interaction**: The Query Engine sends the original query to the `QueryEnhancer`, which returns expanded, reformulated, and semantic variants of the query. This helps in covering more relevant search space.

#### 6. `Reranker` (`rag_system/src/retrieval/reranker.py`)

*   **Role**: Refines the relevance of search results.
*   **Interaction**: After the initial vector search, the Query Engine sends the retrieved documents to the `Reranker`. The `Reranker` uses a cross-encoder model to re-score and re-order the documents, providing a more precise set of top results.

### Data Flow within Query Engine

1.  **Query Reception**: The `process_query` method receives the user's query, optional filters, and (for conversational flows) conversation context.
2.  **Query Enhancement**: The query is sent to the `QueryEnhancer` to generate multiple query variants (expansions, reformulations, semantic variants). This step also involves intent detection and keyword/entity extraction.
3.  **Query Embedding**: Each query variant is converted into a vector embedding by the `Embedder`.
4.  **Vector Search**: The query embeddings are used to perform similarity searches in the `FAISSStore` (or `QdrantVectorStore`). This returns a set of candidate document chunks with their similarity scores.
5.  **Result Merging & Filtering**: Results from multiple query variants are merged and deduplicated. Filters (if provided) are applied to narrow down the results. A similarity threshold is used to ensure only sufficiently relevant chunks are considered.
6.  **Reranking (Optional)**: The filtered results are passed to the `Reranker`, which re-scores them based on a deeper understanding of relevance, producing a refined list of top documents.
7.  **Source Diversity Selection**: From the reranked results, a diverse set of top `k` documents is selected. This involves scoring documents not just on relevance but also on their uniqueness across various metadata fields (e.g., `doc_id`, `source_type`, `author`).
8.  **Context Formulation**: The text content of the selected top documents is extracted and combined to form a coherent context string. This context is enriched with source labels for attribution.
9.  **LLM Response Generation**: The formulated context and the user's original query (or the best enhanced variant) are sent to the `LLMClient`. For conversational queries, the `ConversationHistory` is also included in the prompt.
10. **Response Output**: The LLM's generated response, along with the list of source documents (including their metadata and scores), is returned to the caller.

### API Endpoints (Indirect Interaction)

The Query Engine is primarily an internal service, but its functionality is exposed through the main `API` service (`rag_system/src/api/main.py`) via endpoints like:

*   **`POST /query`**: The main endpoint for submitting user queries.

### Error Handling

The Query Engine implements robust error handling. Failures at any stage (e.g., embedding failure, vector store errors, LLM generation issues) are caught, logged, and result in informative error messages being returned to the user. The `UnifiedErrorHandling` framework ensures consistency.

### Scalability and Performance

The Query Engine is designed for high performance and scalability. It leverages:

*   **Efficient Vector Stores**: `FAISS` and `Qdrant` provide sub-millisecond search capabilities.
*   **Optimized Embedding**: The `Embedder` supports batch processing and can utilize GPUs for faster embedding generation.
*   **Reranking**: Improves precision, reducing the amount of irrelevant data sent to the LLM.
*   **Query Enhancement**: Improves recall, ensuring more relevant documents are found initially.
*   **Asynchronous Operations**: Integrates with FastAPI's asynchronous nature for non-blocking I/O operations.
*   **Managed Resources**: Relies on the `ResourceManager` and `ModelMemoryManager` for efficient handling of compute-intensive models.