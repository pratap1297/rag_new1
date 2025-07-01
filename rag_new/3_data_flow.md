# 3_data_flow.md - Data Flow Documentation

## Data Flow Documentation: RAG System

This document details the primary data flows within the RAG (Retrieval-Augmented Generation) System, illustrating how data is transformed, moved, and processed across different components.

### 1. Ingestion Data Flow

This flow describes how raw documents are transformed into vectorized, searchable data within the RAG system.

**Source**: Raw Document (e.g., PDF, DOCX, XLSX, TXT, JSON, Image) from User Upload or Monitored Folder.

**Destination**: Vector Store (FAISS/Qdrant) and Metadata Store.

**Flow**:

1.  **Document Input**: A raw document enters the system via:
    *   **API Upload**: User uploads a file through the `/upload` or `/upload/enhanced` endpoint of the `API` (`rag_system/src/api/main.py`). The file content and any provided metadata are received.
    *   **Folder Monitor**: The `FolderMonitor` (`rag_system/src/monitoring/folder_monitor.py`) or `EnhancedFolderMonitor` (`rag_system/src/monitoring/enhanced_folder_monitor.py`) detects a new or modified file in a configured directory. The file path is passed to the `IngestionEngine`.

2.  **Ingestion Engine Orchestration**: The `IngestionEngine` (`rag_system/src/ingestion/ingestion_engine.py`) receives the document (or its path) and orchestrates its processing.
    *   **Data**: File content (binary/text) and initial metadata.

3.  **Processor Selection & Extraction**: The `ProcessorRegistry` (`rag_system/src/ingestion/processors/base_processor.py`) identifies the appropriate specialized `BaseProcessor` (e.g., `ExcelProcessor`, `PDFProcessor`, `ServiceNowProcessor`, `TextProcessor`) based on the document's file type.
    *   **Component**: `BaseProcessor` implementations (`rag_system/src/ingestion/processors/*.py`).
    *   **Transformation**: The selected processor extracts raw text, images (which may undergo OCR via `AzureAIClient`), tables, and other structured data from the document.
    *   **Output**: Extracted text content, embedded object data, and document-specific metadata.

4.  **Chunking**: The `Chunker` (`rag_system/src/ingestion/chunker.py`) receives the extracted text content.
    *   **Component**: `Chunker` (or `MemoryEfficientSemanticChunker` for semantic chunking).
    *   **Transformation**: Splits the text into smaller, overlapping chunks, optimizing for semantic coherence and retrieval efficiency.
    *   **Output**: A list of text chunks, each with associated metadata (e.g., `chunk_index`, `page_number`, `source_type`).

5.  **Embedding**: The `Embedder` (`rag_system/src/ingestion/embedder.py`) receives the text content of each chunk.
    *   **Component**: `Embedder` (integrating with providers like Cohere, Azure, or Sentence Transformers).
    *   **Transformation**: Converts each text chunk into a high-dimensional numerical vector (embedding) that captures its semantic meaning.
    *   **Output**: A list of vector embeddings (float arrays).

6.  **Vector Storage**: The `FAISSStore` (`rag_system/src/storage/faiss_store.py`) or `QdrantVectorStore` (`rag_system/src/storage/qdrant_store.py`) receives the vector embeddings and their corresponding metadata.
    *   **Component**: `FAISSStore` or `QdrantVectorStore`.
    *   **Transformation**: Stores the vectors in an optimized index for fast similarity search. Each vector is linked to its metadata.
    *   **Output**: Stored vectors, accessible by internal IDs.

7.  **Metadata Storage**: The `PersistentJSONMetadataStore` (`rag_system/src/storage/persistent_metadata_store.py`) receives comprehensive metadata for the original file and each generated chunk.
    *   **Component**: `PersistentJSONMetadataStore`.
    *   **Transformation**: Persists metadata (e.g., `file_path`, `doc_id`, `chunk_index`, `source_type`, `author`, `title`) in JSON files on disk.
    *   **Output**: Stored metadata, enabling rich filtering and context for retrieval.

8.  **Progress Tracking**: Throughout the ingestion process, the `ProgressTracker` (`rag_system/src/core/progress_tracker.py`) receives updates on the status of each file and processing stage.
    *   **Component**: `ProgressTracker`.
    *   **Output**: Real-time progress metrics, visible via the `ProgressMonitor` UI (`rag_system/src/ui/progress_monitor.py`).

### 2. Query Data Flow

This flow describes how a user query is processed to retrieve relevant information and generate a response.

**Source**: User Query (text string) from Conversational Interface or Direct Query Interface.

**Destination**: User Response (text string) and Source Documents.

**Flow**:

1.  **Query Input**: A user query enters the system via:
    *   **Conversational Interface**: User types a message into the `GradioApp` (`rag_system/src/ui/gradio_app.py`). The `ConversationManager` (`rag_system/src/conversation/conversation_manager.py`) receives the message and updates the `ConversationState`.
    *   **Direct Query API**: User submits a query to the `/query` endpoint of the `API` (`rag_system/src/api/main.py`).

2.  **Query Engine Orchestration**: The `QueryEngine` (`rag_system/src/retrieval/query_engine.py`) receives the query and orchestrates the retrieval and generation process.
    *   **Data**: User query, optional filters, and (for conversational flow) `ConversationContext`.

3.  **Query Enhancement**: The `QueryEnhancer` (`rag_system/src/retrieval/query_enhancer.py`) receives the user query.
    *   **Transformation**: Reformulates, expands, and generates semantic variants of the query to improve search recall.
    *   **Output**: Multiple query variants with confidence scores.

4.  **Query Embedding**: The `Embedder` (`rag_system/src/ingestion/embedder.py`) receives the (enhanced) query.
    *   **Transformation**: Converts the query into a vector embedding.
    *   **Output**: Query vector (float array).

5.  **Vector Search**: The query vector is used to search the `FAISSStore` (or `QdrantVectorStore`).
    *   **Component**: `FAISSStore` or `QdrantVectorStore`.
    *   **Transformation**: Performs a similarity search to find the most relevant document chunks (vectors) in the knowledge base.
    *   **Output**: A list of retrieved document chunks, each with its similarity score and associated metadata.

6.  **Reranking (Optional)**: The `Reranker` (`rag_system/src/retrieval/reranker.py`) receives the initial search results.
    *   **Transformation**: Re-orders the retrieved documents based on a more sophisticated relevance model (e.g., cross-encoder) to improve precision.
    *   **Output**: A refined list of top-ranked document chunks.

7.  **Context Formulation**: The top-ranked document chunks are assembled into a coherent context for the LLM.
    *   **Transformation**: Concatenates text content from selected chunks, potentially adding source attribution.
    *   **Output**: A formatted text string representing the relevant context.

8.  **LLM Response Generation**: The `LLMClient` (`rag_system/src/retrieval/llm_client.py`) receives the user query and the formulated context.
    *   **Component**: `LLMClient` (integrating with Groq, OpenAI, or Azure AI).
    *   **Transformation**: Generates a natural language response based on the query and the provided context. For conversational flows, it also considers `ConversationHistory`.
    *   **Output**: A generated text response.

9.  **Response Output**: The generated response and the source documents are returned to the user.
    *   **Destination**: Conversational Interface (`GradioApp`) or Direct Query API response.
    *   **Data**: Response text, list of source documents (with metadata and similarity scores), and (for conversational flow) updated `ConversationState`.

### 3. ServiceNow Integration Data Flow

This flow describes how ServiceNow incident data is fetched, processed, and ingested into the RAG system.

**Source**: ServiceNow Instance (API).

**Destination**: Vector Store and Metadata Store.

**Flow**:

1.  **Scheduled Fetch**: The `ServiceNowScheduler` (`rag_system/src/integrations/servicenow/scheduler.py`) periodically initiates a fetch operation.
    *   **Component**: `ServiceNowScheduler`.
    *   **Data**: Configuration for filters (e.g., priority, state, days back).

2.  **Connect & Fetch Incidents**: The `ServiceNowConnector` (`rag_system/src/integrations/servicenow/connector.py`) establishes a connection to the ServiceNow instance and fetches incident data.
    *   **Component**: `ServiceNowConnector`.
    *   **Transformation**: Authenticates with ServiceNow and makes API calls to retrieve incident records.
    *   **Output**: Raw JSON data of ServiceNow incidents.

3.  **Incident Processing**: The `ServiceNowTicketProcessor` (`rag_system/src/integrations/servicenow/processor.py`) receives the raw incident JSON data.
    *   **Component**: `ServiceNowTicketProcessor`.
    *   **Transformation**: Parses the raw JSON, extracts relevant fields (e.g., `short_description`, `description`, `work_notes`), identifies network-related incidents, and extracts technical details (IPs, hostnames).
    *   **Output**: `ProcessedTicket` objects, containing cleaned content and structured metadata.

4.  **Ingestion**: The `ProcessedTicket` objects are then passed to the `IngestionEngine`.
    *   **Component**: `IngestionEngine`.
    *   **Transformation**: The `IngestionEngine` treats the processed ticket content as a document, chunking it, embedding it, and storing it in the `FAISSStore` (or `QdrantVectorStore`) and `PersistentJSONMetadataStore`.
    *   **Output**: ServiceNow incident data is now part of the RAG system's searchable knowledge base.

5.  **Caching & History**: The `ServiceNowScheduler` caches fetched incidents and records the sync history in an SQLite database (`servicenow_cache.db`).
    *   **Component**: `ServiceNowScheduler`.
    *   **Output**: Cached incident data (to avoid re-processing unchanged incidents) and a log of sync operations.

### 4. System Monitoring Data Flow

This flow describes how system health and performance data are collected and presented.

**Source**: Various System Components, Operating System.

**Destination**: Monitoring Dashboards, Logs.

**Flow**:

1.  **Scheduled Health Checks**: The `HeartbeatMonitor` (`rag_system/src/monitoring/heartbeat_monitor.py`) periodically initiates health checks.
    *   **Component**: `HeartbeatMonitor`.
    *   **Data**: Triggers checks across various system components.

2.  **Component Health Reporting**: Each system component (e.g., `API`, `FAISSStore`, `LLMClient`, `IngestionEngine`) provides its health status and relevant metrics.
    *   **Data**: Status (Healthy, Warning, Critical), response times, error counts, specific details (e.g., vector count, model availability).

3.  **Resource Monitoring**: The `HeartbeatMonitor` also collects system-level resource usage.
    *   **Data**: CPU utilization, memory consumption, disk usage (via `psutil`).

4.  **Aggregation & Analysis**: The `HeartbeatMonitor` aggregates data from all components and calculates overall system health.
    *   **Transformation**: Combines individual component statuses, identifies critical issues, and generates alerts.
    *   **Output**: `SystemHealth` object, containing overall status, component-level details, performance metrics, and alerts.

5.  **Logging & History**: The `SystemHealth` object is logged and stored in a historical record.
    *   **Component**: `HeartbeatMonitor`.
    *   **Output**: Health check logs (`rag_system.log`, `errors.log`) and a historical record of system health (`health_history.json`).

6.  **Dashboard Display**: The aggregated health data is exposed via API endpoints (`/health`, `/health/detailed`, `/stats`) for consumption by monitoring dashboards.
    *   **Destination**: Administrator's monitoring interface.
    *   **Data**: Real-time and historical system health metrics. 