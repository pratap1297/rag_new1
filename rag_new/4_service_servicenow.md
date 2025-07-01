# 4_service_servicenow.md - ServiceNow Integration Service Documentation

## ServiceNow Integration Service Documentation

### Overview

The ServiceNow Integration service (`rag_system/src/integrations/servicenow/`) is responsible for establishing and managing the connection with a ServiceNow instance. Its primary function is to fetch incident data, process it into a RAG-compatible format, and facilitate its ingestion into the system's knowledge base. This integration enables the RAG system to provide intelligent responses based on real-time IT service management data.

### Key Responsibilities

*   **Connection Management**: Establishes and maintains a secure connection to the ServiceNow instance using provided credentials.
*   **Incident Fetching**: Periodically or on-demand fetches incident records from ServiceNow, applying configurable filters (e.g., priority, state, age).
*   **Data Processing**: Transforms raw ServiceNow incident data (JSON) into a standardized, RAG-friendly document format, extracting key information and enriching metadata.
*   **Automated Scheduling**: Manages a scheduler to automate the fetching and ingestion process at defined intervals.
*   **Change Detection**: Identifies new or updated incidents to avoid redundant processing and ensure data freshness.
*   **Ingestion Orchestration**: Coordinates with the core `IngestionEngine` to add processed ServiceNow data to the vector store.
*   **Error Handling**: Implements robust error handling for API communication, data processing, and ingestion failures.
*   **Status and Monitoring**: Provides endpoints and internal mechanisms to report on the health, status, and statistics of the integration.

### Components

The ServiceNow Integration service is composed of several key components:

#### 1. `ServiceNowConnector` (`rag_system/src/integrations/servicenow/connector.py`)

*   **Role**: Handles direct communication with the ServiceNow REST API.
*   **Responsibilities**:
    *   Manages authentication and session cookies.
    *   Constructs and sends HTTP requests to ServiceNow endpoints (e.g., `/api/now/table/incident`).
    *   Applies query parameters and filters for data retrieval.
    *   Implements rate limiting to comply with ServiceNow API usage policies.
    *   Provides methods for testing connection and fetching incidents by various criteria (e.g., `sys_id`, `number`, recent updates).

#### 2. `ServiceNowTicketProcessor` (`rag_system/src/integrations/servicenow/processor.py`)

*   **Role**: Transforms raw ServiceNow incident data into a structured format suitable for RAG ingestion.
*   **Responsibilities**:
    *   Parses raw JSON incident records.
    *   Extracts relevant fields such as `short_description`, `description`, `work_notes`, `category`, `priority`, `state`, and assignment details.
    *   Enriches metadata, including mapping numerical codes (e.g., priority, state) to human-readable labels.
    *   Identifies and flags network-related incidents based on keyword matching.
    *   Extracts technical details like IP addresses, hostnames, and error codes from incident descriptions and notes.
    *   Generates a content hash for each processed ticket to facilitate change detection and deduplication.
    *   Outputs `ProcessedTicket` objects, which encapsulate the cleaned content and comprehensive metadata.

#### 3. `ServiceNowScheduler` (`rag_system/src/integrations/servicenow/scheduler.py`)

*   **Role**: Orchestrates the automated fetching, processing, and ingestion of ServiceNow incidents.
*   **Responsibilities**:
    *   Manages the scheduling of periodic sync jobs (e.g., every 15 minutes).
    *   Utilizes an SQLite database (`servicenow_cache.db`) for caching fetched incidents and tracking sync history.
    *   Compares fetched incidents with cached data to identify new or updated records, preventing redundant processing.
    *   Coordinates with the `IngestionEngine` to ingest processed tickets into the RAG system.
    *   Records detailed statistics for each fetch operation, including fetched, processed, and ingested counts.
    *   Provides methods for starting, stopping, and getting the status of the automated sync process.

#### 4. `ServiceNowIntegration` (`rag_system/src/integrations/servicenow/integration.py`)

*   **Role**: The main entry point and orchestrator for the entire ServiceNow integration.
*   **Responsibilities**:
    *   Initializes and manages instances of `ServiceNowConnector`, `ServiceNowTicketProcessor`, and `ServiceNowScheduler`.
    *   Provides high-level methods for initializing the integration, starting/stopping automated sync, and triggering manual syncs.
    *   Exposes status information about the integration's health and activity.
    *   Handles overall error management for the integration, ensuring graceful degradation or failure reporting.

### Data Flow within ServiceNow Integration

1.  **Configuration**: `ConfigManager` provides ServiceNow-specific settings (instance URL, credentials, fetch intervals, filters) to the `ServiceNowIntegration`.
2.  **Fetch**: `ServiceNowScheduler` (via `ServiceNowIntegration`) instructs `ServiceNowConnector` to fetch raw incident data from ServiceNow API.
3.  **Process**: Raw incident data is passed to `ServiceNowTicketProcessor`, which cleans, extracts, and enriches the data into `ProcessedTicket` objects.
4.  **Cache & Deduplicate**: `ServiceNowScheduler` caches the `ProcessedTicket` data in `servicenow_cache.db` and checks for changes against previous versions.
5.  **Ingest**: New or updated `ProcessedTicket` objects are sent to the `IngestionEngine` for chunking, embedding, and storage in the main RAG vector store.
6.  **Monitor**: Status and statistics are collected by `ServiceNowScheduler` and exposed via `ServiceNowIntegration` for monitoring by the `HeartbeatMonitor` and API endpoints.

### API Endpoints (from `rag_system/src/api/routes/servicenow.py`)

*   **`GET /servicenow/status`**: Get ServiceNow integration status.
*   **`POST /servicenow/initialize`**: Initialize ServiceNow integration.
*   **`POST /servicenow/start`**: Start automated ServiceNow synchronization.
*   **`POST /servicenow/stop`**: Stop automated ServiceNow synchronization.
*   **`POST /servicenow/sync`**: Perform manual ServiceNow synchronization.
*   **`POST /servicenow/sync/incident/{incident_number}`**: Sync a specific incident by number.
*   **`GET /servicenow/tickets/recent`**: Get recently processed ServiceNow tickets.
*   **`GET /servicenow/history`**: Get ServiceNow synchronization history.
*   **`PUT /servicenow/config`**: Update ServiceNow integration configuration.
*   **`GET /servicenow/config`**: Get current ServiceNow integration configuration.
*   **`POST /servicenow/test`**: Test ServiceNow integration functionality.
*   **`GET /servicenow/connection/info`**: Get ServiceNow connection information.
*   **`POST /servicenow/connection/test`**: Test ServiceNow connection.

### Dependencies

The ServiceNow Integration service relies on:

*   `requests`: For HTTP communication with ServiceNow.
*   `sqlite3`: For local caching and history tracking.
*   `threading`, `asyncio`, `schedule`: For scheduling and concurrent operations.
*   `IngestionEngine`: To push processed data into the RAG system.
*   `ConfigManager`: For configuration management.
*   `logging`: For comprehensive logging and debugging.