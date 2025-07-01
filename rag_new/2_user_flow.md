# 2_user_flow.md - User Flow Documentation

## User Flow Documentation: RAG System

This document outlines the primary user interaction flows within the RAG (Retrieval-Augmented Generation) System, focusing on how users engage with the system to retrieve information and receive responses.

### 1. Conversational Query Flow

This is the primary and most intuitive way for users to interact with the RAG system, leveraging its LangGraph-powered conversational capabilities.

**Actor**: End User

**Goal**: Obtain information or answers through a natural language conversation.

**Steps**:

1.  **Initiate Conversation**: The user accesses the RAG system's conversational interface (e.g., Gradio UI, or an integrated chat application).
    *   **System**: Displays a greeting message (e.g., "Hello! How can I help you today?").
2.  **Submit Query**: The user types a question or statement into the chat interface and submits it.
    *   **System**: Receives the user's message.
3.  **Understand Intent**: The `ConversationManager` and `ConversationNodes` analyze the user's message to understand their intent (e.g., factual question, procedural query, follow-up, greeting, goodbye).
    *   **System**: Extracts keywords, entities, and context hints from the query.
4.  **Retrieve Information**: If the intent is information-seeking, the `QueryEngine` is invoked.
    *   **System**: The `QueryEnhancer` may reformulate or expand the query for better search results.
    *   **System**: The enhanced query is converted into a vector embedding by the `Embedder`.
    *   **System**: The vector is used to search the `FAISSStore` (or `QdrantVectorStore`) for relevant document chunks.
    *   **System**: A `Reranker` may re-order the retrieved chunks based on relevance.
5.  **Generate Response**: The retrieved relevant document chunks (context) are passed to the `LLMClient` along with the user's original query.
    *   **System**: The `LLMClient` (integrating with Groq, OpenAI, or Azure AI) synthesizes a coherent and contextually accurate response based on the provided context.
6.  **Display Response**: The generated response is displayed in the chat interface.
    *   **System**: May also display suggested follow-up questions, related topics, and source attribution (e.g., document names, page numbers) to enhance user experience.
7.  **Continue Conversation**: The user can ask follow-up questions, clarify previous responses, or change the topic.
    *   **System**: The `ConversationManager` maintains the conversation history and context, allowing for natural, multi-turn interactions.
8.  **End Conversation**: The user indicates they are finished (e.g., by typing "goodbye" or clicking an "End Conversation" button).
    *   **System**: Provides a farewell message and may offer a summary of the conversation.

**Success Criteria**: The user receives accurate, relevant, and well-attributed answers in a natural conversational style.

### 2. Direct Query Flow

This flow allows users to submit single, direct questions without engaging in a multi-turn conversation.

**Actor**: End User

**Goal**: Get a quick, direct answer to a specific question.

**Steps**:

1.  **Access Direct Query Interface**: The user navigates to the direct query section of the RAG system's UI (e.g., Gradio UI).
2.  **Submit Query**: The user types their question into a dedicated input field and submits it.
    *   **System**: Receives the query.
3.  **Process Query**: The `QueryEngine` directly processes the query (similar to step 4 in Conversational Query Flow, but without the multi-turn context management).
    *   **System**: Enhances, embeds, searches, and reranks to find relevant information.
4.  **Generate and Display Response**: The `LLMClient` generates a response based on the retrieved context, and both the response and its sources are displayed.

**Success Criteria**: The user receives a concise and accurate answer, along with clear source attribution.

### 3. Document Upload and Ingestion Flow

This flow describes how users (typically administrators or content managers) contribute new documents to the RAG system's knowledge base.

**Actor**: Administrator / Content Manager

**Goal**: Add new documents to the RAG system for future retrieval.

**Steps**:

1.  **Access Upload Interface**: The user navigates to the document upload section of the RAG system's UI (e.g., Gradio UI).
2.  **Select File(s)**: The user selects one or more documents from their local machine to upload.
3.  **Provide Metadata (Optional)**: The user may provide additional metadata (e.g., department, category, tags) to enrich the document's context.
4.  **Submit Upload**: The user initiates the upload process.
    *   **System**: The `API` receives the file and any associated metadata.
5.  **Ingest Document**: The `IngestionEngine` takes over the processing.
    *   **System**: The `ProcessorRegistry` identifies the appropriate `BaseProcessor` (e.g., `ExcelProcessor`, `PDFProcessor`, `ServiceNowProcessor`) based on the file type.
    *   **System**: The chosen processor extracts text, images (with OCR), tables, and other structured data from the document.
    *   **System**: The `Chunker` splits the extracted content into smaller, semantically meaningful chunks.
    *   **System**: The `Embedder` converts each chunk into a high-dimensional vector embedding.
    *   **System**: The `FAISSStore` (or `QdrantVectorStore`) stores these vector embeddings.
    *   **System**: The `MetadataManager` stores and links the document's metadata and chunk-level metadata.
6.  **Monitor Progress**: The user can monitor the ingestion progress in real-time via the `ProgressMonitor` interface.
    *   **System**: Updates on file validation, extraction, chunking, embedding, and storage stages are displayed.
7.  **Confirmation**: Upon successful ingestion, the system confirms the document has been added and is ready for querying.

**Success Criteria**: Documents are successfully processed, vectorized, and integrated into the knowledge base, becoming searchable and retrievable by the system.

### 4. Folder Monitoring and Automated Ingestion Flow

This flow describes how the system automatically ingests documents from designated file system folders.

**Actor**: System (Automated Process)

**Goal**: Automatically keep the knowledge base updated with new or modified documents from monitored folders.

**Steps**:

1.  **Configure Monitored Folders**: An administrator configures specific file system folders to be monitored (via API or configuration files).
2.  **Start Monitoring**: The `FolderMonitor` (or `EnhancedFolderMonitor`) service is started.
3.  **Scan for Changes**: Periodically, the `FolderMonitor` scans the configured folders for new, modified, or deleted files.
    *   **System**: Calculates file hashes and compares timestamps/sizes to detect changes.
4.  **Trigger Ingestion**: Upon detecting a new or modified file, the `FolderMonitor` queues the file for ingestion.
5.  **Ingest Document**: The `IngestionEngine` processes the document (similar to steps 5-7 in Document Upload Flow).
    *   **System**: For `EnhancedFolderMonitor`, each step of the ingestion pipeline is verified, and real-time updates are provided.
6.  **Handle Deletions**: If a file is deleted from a monitored folder, the `FolderMonitor` triggers the deletion of its corresponding vectors and metadata from the RAG system.

**Success Criteria**: The knowledge base remains up-to-date with minimal manual intervention, reflecting the latest changes in designated document repositories.

### 5. System Health Monitoring Flow

This flow describes how administrators can monitor the overall health and performance of the RAG system.

**Actor**: Administrator

**Goal**: Ensure the RAG system is operating optimally and identify any issues.

**Steps**:

1.  **Access Health Dashboard**: The administrator accesses the system's health dashboard (e.g., via API endpoints or a dedicated monitoring UI).
2.  **View Overall Status**: The dashboard displays an aggregated health status (e.g., Healthy, Warning, Critical).
    *   **System**: The `HeartbeatMonitor` periodically performs comprehensive checks on all components (API, storage, vector store, LLM, etc.).
3.  **Review Component Health**: The administrator can drill down to view the health status of individual components.
    *   **System**: Provides details on response times, error rates, and specific issues for each component.
4.  **Analyze Performance Metrics**: The dashboard presents key performance indicators (e.g., CPU usage, memory consumption, query response times, ingestion rates).
5.  **Review Alerts and Logs**: Any critical alerts or warnings are highlighted, and access to system logs is provided for deeper investigation.

**Success Criteria**: The administrator has real-time visibility into system health, enabling proactive identification and resolution of issues to maintain system availability and performance.