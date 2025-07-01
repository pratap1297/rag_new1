# 4_service_api.md - API Service Documentation

## API Service Documentation

### Overview

The API service (`rag_system/src/api/main.py`) is the primary interface for interacting with the RAG system. Built using FastAPI, it provides a comprehensive set of RESTful endpoints for querying the knowledge base, uploading documents, managing system resources, and monitoring health.

### Key Responsibilities

*   **Query Processing**: Receives user queries, orchestrates retrieval, and returns generated responses.
*   **Document Ingestion**: Handles file uploads and initiates the document ingestion pipeline.
*   **System Management**: Provides endpoints for administrative tasks such as listing documents, clearing the vector store, and updating configurations.
*   **Health Monitoring**: Exposes various health check endpoints to assess the status of different system components.
*   **Feedback Collection**: Allows users to submit feedback on query responses.
*   **Real-time Updates**: Utilizes WebSockets for real-time progress updates during long-running operations like ingestion.

### Endpoints

The API service exposes a wide range of endpoints, categorized by their functionality:

#### Core Functionality

*   **`POST /query`**: Processes a natural language query and returns a generated response with source attribution.
    *   **Request**: `QueryRequest` (query string, optional filters, top_k)
    *   **Response**: `QueryResponse` (generated response, sources, confidence)
*   **`POST /ingest`**: Ingests raw text content directly into the knowledge base.
    *   **Request**: JSON body with `text` and optional `metadata`.
    *   **Response**: Status of the ingestion operation.
*   **`POST /upload`**: Uploads and processes a file for ingestion into the knowledge base.
    *   **Request**: `UploadFile` (file content), optional `metadata` (form data).
    *   **Response**: `UploadResponse` (status, file_id, chunks_created, etc.).
*   **`POST /upload/enhanced`**: Enhanced file upload endpoint with better original path preservation.
    *   **Request**: `UploadFile`, `original_path`, `description`, `upload_source`, `additional_metadata` (form data).
    *   **Response**: `UploadResponse`.

#### Health and Monitoring

*   **`GET /health`**: Basic health check.
*   **`GET /health/detailed`**: Detailed health check with component testing.
*   **`GET /stats`**: Retrieves system-wide statistics (e.g., total vectors, documents).
*   **`GET /documents`**: Lists all documents currently in the vector store.
*   **`GET /config`**: Retrieves current system configuration information.
*   **`GET /heartbeat`**: Comprehensive system heartbeat status.
*   **`GET /health/summary`**: Health summary (no auth required).
*   **`GET /health/components`**: Detailed component health status.
*   **`GET /health/history`**: Health check history.
*   **`POST /health/check`**: Manually triggers a health check.
*   **`POST /heartbeat/start`**: Starts heartbeat monitoring.
*   **`POST /heartbeat/stop`**: Stops heartbeat monitoring.
*   **`GET /heartbeat/status`**: Gets heartbeat monitoring status.
*   **`GET /heartbeat/logs`**: Gets recent heartbeat logs.
*   **`GET /health/performance`**: Gets detailed performance metrics.

#### Folder Monitoring Endpoints

*   **`GET /folder-monitor/status`**: Gets folder monitoring status.
*   **`POST /folder-monitor/add`**: Adds a folder to monitoring.
*   **`POST /folder-monitor/remove`**: Removes a folder from monitoring.
*   **`GET /folder-monitor/folders`**: Gets list of monitored folders.
*   **`POST /folder-monitor/start`**: Starts folder monitoring.
*   **`POST /folder-monitor/stop`**: Stops folder monitoring.
*   **`POST /folder-monitor/scan`**: Forces an immediate scan of all monitored folders.
*   **`GET /folder-monitor/files`**: Gets status of all monitored files.
*   **`POST /folder-monitor/retry`**: Retries failed file ingestion.

#### Document and Vector Management

*   **`DELETE /documents/{doc_path:path}`**: Deletes a specific document and its vectors from the system.
*   **`POST /clear`**: Clears all vectors and documents from the system.
*   **`GET /vectors`**: Gets a paginated list of vectors with metadata.
*   **`GET /vectors/{vector_id}`**: Gets detailed information about a specific vector.

#### Feedback System

*   **`POST /feedback`**: Collects user feedback on responses.
*   **`GET /feedback/stats`**: Gets feedback statistics.
*   **`GET /feedback/suggestions`**: Gets system improvement suggestions based on feedback.
*   **`GET /feedback/recent`**: Gets recent feedback entries.
*   **`POST /feedback/export`**: Exports feedback data for analysis.

#### Verification Endpoints (from `verification_endpoints.py`)

*   **`POST /api/verification/validate-file`**: Validates a file before processing.
*   **`POST /api/verification/test-extraction`**: Tests content extraction without full ingestion.
*   **`POST /api/verification/test-chunking`**: Tests text chunking with different methods.
*   **`POST /api/verification/test-embedding`**: Tests embedding generation for a text sample.
*   **`GET /api/verification/verify-vectors/{vector_id}`**: Verifies a specific vector in FAISS.
*   **`POST /api/verification/ingest-with-verification`**: Ingests file with comprehensive verification and real-time updates.
*   **`GET /api/verification/session/{session_id}`**: Gets status of a verification session.
*   **`GET /api/verification/sessions`**: Lists all active verification sessions.
*   **`POST /api/verification/analyze-chunks`**: Analyzes chunks for a specific file.
*   **`POST /api/verification/test-similarity`**: Tests similarity between a query and specific vector.
*   **`GET /api/verification/performance-stats`**: Gets performance statistics for recent verifications.
*   **`GET /api/verification/debug/file-access/{file_path:path}`**: Debugs file access issues.
*   **`GET /api/verification/health`**: Health check for verification system.
*   **`GET /api/verification/dashboard`**: Serves the verification dashboard HTML.

#### Conversation Endpoints (from `routes/conversation.py`)

*   **`POST /conversation/start`**: Starts a new conversation using LangGraph state persistence.
*   **`POST /conversation/message`**: Sends a message in an existing conversation.
*   **`POST /conversation/message/stream`**: Sends a message with streaming response.
*   **`GET /conversation/history/{thread_id}`**: Gets conversation history for a thread.
*   **`POST /conversation/end/{thread_id}`**: Ends a conversation.
*   **`GET /conversation/threads`**: Gets information about active conversation threads.
*   **`GET /conversation/health`**: Health check for conversation service.

#### Power BI Endpoints (from `routes/powerbi.py`)

*   **`GET /powerbi/connection/test`**: Tests Power BI connection and authentication.
*   **`GET /powerbi/workspaces`**: Lists all accessible Power BI workspaces.
*   **`GET /powerbi/reports/{workspace_id}`**: Lists all reports in a specific workspace.
*   **`GET /powerbi/datasets/{workspace_id}`**: Lists all datasets in a specific workspace.
*   **`POST /powerbi/sync`**: Performs immediate synchronization of Power BI workspace.
*   **`GET /powerbi/status`**: Gets current synchronization status.
*   **`POST /powerbi/schedule`**: Configures scheduled synchronization for a workspace.
*   **`GET /powerbi/schedule/jobs`**: Lists all scheduled synchronization jobs.
*   **`PUT /powerbi/schedule/jobs/{job_id}`**: Updates a scheduled synchronization job.
*   **`DELETE /powerbi/schedule/jobs/{job_id}`**: Deletes a scheduled synchronization job.
*   **`POST /powerbi/schedule/jobs/{job_id}/run`**: Runs a specific sync job immediately.
*   **`GET /powerbi/sync/history`**: Gets recent synchronization history.
*   **`DELETE /powerbi/sync/history`**: Clears synchronization history.
*   **`POST /powerbi/schedule/start`**: Starts the Power BI scheduler.
*   **`POST /powerbi/schedule/stop`**: Stops the Power BI scheduler.
*   **`GET /powerbi/report/{workspace_id}/{report_id}/structure`**: Gets detailed structure of a Power BI report.
*   **`POST /powerbi/dax/execute`**: Executes a DAX query against a Power BI dataset.
*   **`POST /powerbi/extract/{report_id}`**: Extracts data from a specific Power BI report.
*   **`POST /powerbi/upload/pbix`**: Uploads and parses a Power BI Desktop (.pbix) file.

#### ServiceNow Endpoints (from `routes/servicenow.py`)

*   **`GET /servicenow/status`**: Gets ServiceNow integration status.
*   **`POST /servicenow/initialize`**: Initializes ServiceNow integration.
*   **`POST /servicenow/start`**: Starts automated ServiceNow synchronization.
*   **`POST /servicenow/stop`**: Stops automated ServiceNow synchronization.
*   **`POST /servicenow/sync`**: Performs manual ServiceNow synchronization.
*   **`POST /servicenow/sync/incident/{incident_number}`**: Syncs a specific incident by number.
*   **`GET /servicenow/tickets/recent`**: Gets recently processed ServiceNow tickets.
*   **`GET /servicenow/history`**: Gets ServiceNow synchronization history.
*   **`PUT /servicenow/config`**: Updates ServiceNow integration configuration.
*   **`GET /servicenow/config`**: Gets current ServiceNow integration configuration.
*   **`POST /servicenow/test`**: Tests ServiceNow integration functionality.
*   **`GET /servicenow/connection/info`**: Gets ServiceNow connection information.
*   **`POST /servicenow/connection/test`**: Tests ServiceNow connection.

### Dependencies

The API service relies heavily on the `DependencyContainer` to access various core components and external integrations, including:

*   `QueryEngine`: For processing user queries.
*   `IngestionEngine`: For handling document uploads.
*   `ConfigManager`: For accessing system configurations.
*   `HeartbeatMonitor`: For system health checks.
*   `FolderMonitor` / `EnhancedFolderMonitor`: For managing folder-based ingestion.
*   `FeedbackStore`: For storing and retrieving user feedback.
*   `ConversationManager`: For managing conversational interactions.
*   `ServiceNowIntegration`: For ServiceNow-specific operations.
*   `PowerBIIntegration`: For Power BI-specific operations.

### Error Handling

The API utilizes a unified error handling mechanism (`rag_system/src/core/unified_error_handling.py`) to provide consistent and informative error responses. HTTP exceptions are raised for client-side errors (4xx) and server-side errors (5xx), with detailed error codes and messages.

### Scalability and Performance

The API is designed to be scalable, leveraging FastAPI's asynchronous capabilities and Uvicorn's efficient worker management. Long-running tasks like file ingestion are offloaded to background tasks or managed thread pools to prevent blocking the main event loop. The `ResourceManager` ensures efficient allocation and cleanup of resources.