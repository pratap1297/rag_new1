# 4_service_ingestion_engine.md - Ingestion Engine Service Documentation

## Ingestion Engine Service Documentation

### Overview

The Ingestion Engine (`rag_system/src/ingestion/ingestion_engine.py`) is the core component responsible for processing raw documents and transforming them into a structured, vectorized format suitable for retrieval within the RAG system. It orchestrates the entire pipeline from file input to vector storage, ensuring data integrity and efficient processing.

### Key Responsibilities

*   **Document Orchestration**: Manages the end-to-end flow of document processing, coordinating various sub-components.
*   **File Type Detection**: Identifies the type of document (e.g., PDF, Excel, Word, Text) to route it to the appropriate processor.
*   **Content Extraction**: Utilizes specialized processors to extract text, images (with OCR), tables, and other structured data from diverse document formats.
*   **Text Chunking**: Breaks down extracted content into smaller, semantically meaningful chunks to optimize retrieval.
*   **Vector Embedding**: Converts text chunks into high-dimensional vector embeddings using a configured embedding model.
*   **Vector Storage**: Stores the generated vector embeddings in the chosen vector database (FAISS or Qdrant).
*   **Metadata Management**: Associates comprehensive metadata with both the original documents and individual chunks, enabling rich filtering and context during retrieval.
*   **Deduplication**: Checks for duplicate documents based on content hashes to prevent redundant ingestion.
*   **Update Handling**: Manages updates to existing documents by deleting old vectors and ingesting new versions.
*   **Progress Tracking**: Integrates with a `ProgressTracker` to provide real-time updates on the ingestion status of documents.
*   **Pipeline Verification**: Can be wrapped by a `VerifiedIngestionEngine` to perform step-by-step validation of the ingestion pipeline.

### Components

The Ingestion Engine interacts with several key components to perform its functions:

#### 1. `Chunker` (`rag_system/src/ingestion/chunker.py`)

*   **Role**: Splits raw text into smaller, manageable segments.
*   **Responsibilities**:
    *   Divides long text into chunks of a specified size with a defined overlap.
    *   Supports both simple recursive character splitting and advanced `MemoryEfficientSemanticChunker` for semantically coherent chunks.
    *   Preserves metadata during the chunking process.

#### 2. `Embedder` (`rag_system/src/ingestion/embedder.py`)

*   **Role**: Generates numerical representations (embeddings) of text.
*   **Responsibilities**:
    *   Interfaces with various embedding providers (e.g., Cohere, Azure, Sentence Transformers).
    *   Converts text chunks into high-dimensional vectors.
    *   Manages batch processing for efficiency and handles API keys and endpoints for external services.

#### 3. `FAISSStore` / `QdrantVectorStore` (`rag_system/src/storage/faiss_store.py` / `rag_system/src/storage/qdrant_store.py`)

*   **Role**: Stores and manages vector embeddings.
*   **Responsibilities**:
    *   Provides an interface for adding, searching, and deleting vector embeddings.
    *   Persists the vector index and associated metadata.
    *   Handles thread-safe operations and optimizations for efficient vector management.

#### 4. `PersistentJSONMetadataStore` (`rag_system/src/storage/persistent_metadata_store.py`)

*   **Role**: Stores and retrieves comprehensive metadata for documents and chunks.
*   **Responsibilities**:
    *   Persists metadata in JSON files on disk.
    *   Links vector IDs to their corresponding chunk and document metadata.
    *   Supports querying metadata for filtering and context.

#### 5. `ProcessorRegistry` (`rag_system/src/ingestion/processors/base_processor.py`)

*   **Role**: Manages and dispatches specialized document processors.
*   **Responsibilities**:
    *   Registers various `BaseProcessor` implementations (e.g., `ExcelProcessor`, `PDFProcessor`, `WordProcessor`, `ImageProcessor`, `ServiceNowProcessor`, `TextProcessor`).
    *   Selects the appropriate processor for a given file type based on its `can_process` method.

#### 6. `ProgressTracker` (`rag_system/src/core/progress_tracker.py`)

*   **Role**: Provides real-time monitoring of ingestion progress.
*   **Responsibilities**:
    *   Tracks the status and progress of individual files and overall batches through various ingestion stages (e.g., validating, extracting, chunking, embedding, storing).
    *   Exposes metrics and status updates for UI display.

### Data Flow within Ingestion Engine

1.  **File Input**: The `ingest_file` method receives a file path and optional metadata.
2.  **Validation**: The file is validated for existence, size, and accessibility. A content hash is calculated for deduplication.
3.  **Deduplication/Update Check**: The system checks if the document (based on its hash) already exists or if it's an update to an existing document. If it's an update, old vectors associated with the document are marked for deletion.
4.  **Content Extraction**: The `ProcessorRegistry` dispatches the file to the relevant `BaseProcessor` (e.g., `ExcelProcessor` for `.xlsx` files, `EnhancedPDFProcessor` for `.pdf` files). The processor extracts raw text, images (which may undergo OCR via `AzureAIClient`), and structured data.
5.  **Chunking**: The extracted text content is passed to the `Chunker`, which breaks it into smaller, semantically coherent chunks. Each chunk is enriched with metadata.
6.  **Embedding**: Each text chunk is then sent to the `Embedder`, which converts it into a high-dimensional vector embedding.
7.  **Vector Storage**: The generated vector embeddings, along with their associated metadata, are added to the `FAISSStore` (or `QdrantVectorStore`).
8.  **Metadata Persistence**: Comprehensive metadata for the original file and each chunk is stored in the `PersistentJSONMetadataStore`.
9.  **Progress Reporting**: Throughout these steps, the `ProgressTracker` is updated with the current stage, progress percentage, and any errors, providing real-time visibility into the ingestion process.

### API Endpoints (Indirect Interaction)

The Ingestion Engine is primarily an internal service, but its functionality is exposed through the main `API` service (`rag_system/src/api/main.py`) via endpoints like:

*   **`POST /upload`**: For file-based ingestion.
*   **`POST /ingest`**: For direct text ingestion.
*   **`DELETE /documents/{doc_path:path}`**: To trigger deletion of documents.
*   **`POST /clear`**: To clear the entire vector store.

### Error Handling

The Ingestion Engine employs robust error handling mechanisms. Failures at any stage (e.g., file not found, processing error, embedding failure) are caught, logged, and reported via the `ProgressTracker`. The `UnifiedErrorHandling` framework ensures consistent error reporting across the system.

### Scalability and Performance

Designed for scalability, the Ingestion Engine can process documents in parallel (when integrated with appropriate task queues or thread pools). Its modular design allows for easy integration of new processors and optimization of individual steps. The use of `MemoryEfficientSemanticChunker` and `ModelMemoryManager` helps in managing memory for large language models during embedding and chunking.