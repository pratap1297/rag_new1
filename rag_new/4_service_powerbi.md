# 4_service_powerbi.md - Power BI Integration Service Documentation

## Power BI Integration Service Documentation

### Overview

The Power BI Integration service (`rag_system/src/api/routes/powerbi.py`) is designed to connect with Microsoft Power BI, extract report data, and integrate it into the RAG system's knowledge base. This allows the RAG system to answer questions based on structured data and insights contained within Power BI reports, enhancing its analytical capabilities.

### Key Responsibilities

*   **Connection Management**: Establishes and tests connectivity with Power BI services.
*   **Workspace and Report Discovery**: Lists accessible Power BI workspaces and reports within them.
*   **Data Extraction**: Extracts data from Power BI reports, including raw data from visuals and underlying datasets.
*   **PBIX File Processing**: Uploads and parses `.pbix` (Power BI Desktop) files to extract their content and metadata.
*   **Scheduled Synchronization**: Configures and manages scheduled jobs to periodically sync data from Power BI reports.
*   **Ingestion Preparation**: Prepares extracted Power BI data into a format suitable for ingestion into the RAG system.
*   **Status and History**: Provides real-time status updates and historical logs of synchronization jobs.

### Components

The Power BI Integration is primarily exposed through a single FastAPI router (`rag_system/src/api/routes/powerbi.py`). While the provided code includes mock implementations for most functionalities, a full implementation would involve:

#### 1. Power BI API Client (Conceptual)

*   **Role**: Handles authentication and communication with the Microsoft Power BI REST APIs.
*   **Responsibilities**:
    *   OAuth 2.0 authentication flow for secure access.
    *   Making API calls to list workspaces, reports, datasets, and to export data.
    *   Handling API responses and errors.

#### 2. Data Extractor (Conceptual)

*   **Role**: Processes data obtained from Power BI reports and `.pbix` files.
*   **Responsibilities**:
    *   **Report Data Extraction**: For live reports, this would involve using Power BI REST APIs to export data from visuals or datasets.
    *   **PBIX File Parsing**: For `.pbix` files, this would involve parsing the internal structure (which is a ZIP archive) to extract data models, DAX queries, and visual definitions. This is a complex task often requiring specialized libraries or custom parsers.
    *   **Data Normalization**: Converts extracted data (e.g., tables, visual descriptions) into a structured format (e.g., JSON, text) suitable for chunking and embedding.

#### 3. Scheduler (Conceptual)

*   **Role**: Manages automated synchronization jobs.
*   **Responsibilities**:
    *   Stores job configurations (workspace IDs, report IDs, intervals).
    *   Triggers data extraction and ingestion at specified intervals.
    *   Logs job execution status and history.

### Data Flow within Power BI Integration

1.  **Configuration**: Power BI connection details (e.g., tenant ID, client ID, client secret) and synchronization schedules are configured.
2.  **Discovery**: The system connects to Power BI to list available workspaces, reports, and datasets.
3.  **Synchronization (Manual/Scheduled)**:
    *   **Trigger**: A user initiates a manual sync via API (`/powerbi/sync`) or the `Scheduler` triggers a scheduled job.
    *   **Extraction**: The `Power BI API Client` extracts data from specified reports or datasets. For `.pbix` files, the file content is uploaded and parsed (`/powerbi/upload/pbix`).
    *   **Processing**: The extracted data (e.g., tables, visual descriptions, DAX queries) is processed and normalized into text chunks.
    *   **Ingestion**: These text chunks, along with relevant metadata (e.g., `workspace_id`, `report_id`, `page_name`, `visual_title`), are then passed to the RAG system's `IngestionEngine` for chunking, embedding, and storage in the vector store.
4.  **Querying**: Once ingested, the Power BI data becomes part of the RAG system's knowledge base and can be queried through the standard `Query` API endpoint.
5.  **Monitoring**: The service provides status updates on sync jobs and exposes history for monitoring.

### API Endpoints (from `rag_system/src/api/routes/powerbi.py`)

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

### Dependencies

The Power BI Integration service relies on:

*   `fastapi`, `logging`, `asyncio`, `datetime`: Standard FastAPI and Python libraries.
*   `requests` (conceptual): For HTTP communication with Power BI REST APIs.
*   `openpyxl`, `pandas` (conceptual): For parsing `.pbix` files (which contain Excel-like data) and general data manipulation.
*   `IngestionEngine`: To push processed data into the RAG system.