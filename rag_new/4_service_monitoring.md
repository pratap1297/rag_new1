# 4_service_monitoring.md - Monitoring Service Documentation

## Monitoring Service Documentation

### Overview

The Monitoring service (`rag_system/src/monitoring/`) provides comprehensive insights into the health, performance, and operational status of the RAG system. It is designed to proactively identify issues, track key metrics, and ensure the system's reliability and efficiency. This service is crucial for administrators to maintain the system and respond to anomalies.

### Key Responsibilities

*   **System Health Checks**: Periodically assesses the operational status of all critical system components (API, storage, vector store, LLM, etc.).
*   **Performance Metrics Collection**: Gathers and reports on key performance indicators (KPIs) such as CPU usage, memory consumption, disk space, query response times, and ingestion rates.
*   **Alerting**: Identifies deviations from normal operating parameters and generates alerts for critical issues.
*   **Historical Data**: Stores a history of health checks and performance metrics for trend analysis and post-mortem investigations.
*   **Folder Monitoring**: Automatically detects new, modified, or deleted files in designated directories and triggers ingestion or deletion processes.
*   **Pipeline Verification**: For automated ingestion, it can provide detailed, step-by-step verification of the processing pipeline.

### Components

The Monitoring service is composed of several key components:

#### 1. `HeartbeatMonitor` (`rag_system/src/monitoring/heartbeat_monitor.py`)

*   **Role**: The central component for system-wide health and performance monitoring.
*   **Responsibilities**:
    *   **Comprehensive Health Checks**: Orchestrates periodic checks of all registered components (e.g., `API`, `FAISSStore`, `LLMClient`, `IngestionEngine`, `DependencyContainer`).
    *   **Resource Monitoring**: Collects system-level metrics like CPU, memory, and disk usage using `psutil`.
    *   **Status Aggregation**: Aggregates individual component statuses into an overall system health status (Healthy, Warning, Critical).
    *   **Performance Metrics**: Gathers and exposes performance metrics for various operations.
    *   **History Management**: Stores a rolling history of `SystemHealth` objects for trend analysis.
    *   **Alert Generation**: Identifies performance bottlenecks or component failures and generates alerts.

#### 2. `FolderMonitor` (`rag_system/src/monitoring/folder_monitor.py`)

*   **Role**: Monitors specified file system folders for changes and triggers automated ingestion/deletion.
*   **Responsibilities**:
    *   **Folder Configuration**: Manages a list of directories to be monitored.
    *   **Change Detection**: Periodically scans monitored folders for new, modified, or deleted files by comparing file hashes, sizes, and modification times.
    *   **File Filtering**: Filters files based on supported extensions and maximum file size.
    *   **Automated Ingestion**: If `auto_ingest` is enabled, it triggers the `IngestionEngine` to process new or modified files.
    *   **Deletion Handling**: If a file is deleted from a monitored folder, it triggers the deletion of corresponding vectors from the RAG system.
    *   **Status Reporting**: Provides status on monitored folders, tracked files, and ingestion outcomes.

#### 3. `EnhancedFolderMonitor` (`rag_system/src/monitoring/enhanced_folder_monitor.py`)

*   **Role**: An advanced version of the `FolderMonitor` with integrated pipeline verification and real-time updates.
*   **Responsibilities**:
    *   Extends `FolderMonitor` capabilities.
    *   Integrates with `PipelineVerifier` (`rag_system/src/core/pipeline_verifier.py`) to provide step-by-step verification of the ingestion process for each file.
    *   Maintains detailed `FileProcessingState` for each file, including current stage, verification results, and processing metrics.
    *   Emits real-time events (via WebSockets) on file queuing, processing start, stage completion, and processing failures, enabling dynamic UI dashboards.
    *   Manages a processing queue and concurrent processors to handle multiple files simultaneously.

#### 4. `Logger` (`rag_system/src/monitoring/logger.py`)

*   **Role**: Centralized logging setup for the RAG system.
*   **Responsibilities**:
    *   Configures logging levels, formats (including JSON for structured logs), and handlers (console, file rotation).
    *   Ensures consistent logging across all system components.

#### 5. `setup.py` (`rag_system/src/monitoring/setup.py`)

*   **Role**: Entry point for initializing monitoring components.
*   **Responsibilities**: Orchestrates the setup of metrics collection and other monitoring-related services based on system configuration.

### Data Flow within Monitoring Service

#### Heartbeat Monitoring Flow:

1.  **Scheduled Check**: The `HeartbeatMonitor` initiates a comprehensive health check at regular intervals.
2.  **Component Probing**: It queries various system components (e.g., `API`, `FAISSStore`, `LLMClient`, `IngestionEngine`, `DependencyContainer`) for their health status and performance metrics.
3.  **Resource Data Collection**: `psutil` is used to gather real-time CPU, memory, and disk usage data from the operating system.
4.  **Status Aggregation**: Individual component health statuses and resource metrics are aggregated to determine an `overall_status` (Healthy, Warning, Critical) for the entire system.
5.  **Alert Generation**: If any component reports a critical status or if performance metrics exceed predefined thresholds, alerts are generated.
6.  **History Storage**: The complete `SystemHealth` object (including component details, performance metrics, and alerts) is stored in a historical log (`health_history.json`).
7.  **API Exposure**: The `SystemHealth` data is exposed via various API endpoints (`/heartbeat`, `/health/summary`, `/health/components`, `/health/performance`) for external monitoring tools and dashboards.

#### Folder Monitoring Flow:

1.  **Folder Configuration**: Monitored folders are configured in the system settings.
2.  **Periodic Scan**: The `FolderMonitor` (or `EnhancedFolderMonitor`) periodically scans these folders.
3.  **Change Detection**: It compares the current state of files (hash, size, modification time) with previously recorded states to detect new, modified, or deleted files.
4.  **Ingestion Trigger**: For new or modified files, the `FolderMonitor` queues the file for processing by the `IngestionEngine`.
5.  **Deletion Trigger**: For deleted files, it triggers the `IngestionEngine`'s `delete_file` method to remove corresponding vectors from the RAG system.
6.  **Progress Reporting (Enhanced)**: The `EnhancedFolderMonitor` integrates with `PipelineVerifier` to track each stage of the ingestion process (file validation, extraction, chunking, embedding, storage) and emits real-time events for UI updates.

### API Endpoints (Indirect Interaction)

The Monitoring service exposes its functionalities primarily through the main `API` service (`rag_system/src/api/main.py`) via endpoints like:

*   **Heartbeat Endpoints**: `/heartbeat`, `/health/summary`, `/health/components`, `/health/history`, `/health/check`, `/heartbeat/start`, `/heartbeat/stop`, `/heartbeat/status`, `/heartbeat/logs`, `/health/performance`.
*   **Folder Monitor Endpoints**: `/folder-monitor/status`, `/folder-monitor/add`, `/folder-monitor/remove`, `/folder-monitor/folders`, `/folder-monitor/start`, `/folder-monitor/stop`, `/folder-monitor/scan`, `/folder-monitor/files`, `/folder-monitor/retry`.
*   **Verification Endpoints (from `verification_endpoints.py`)**: `/api/verification/validate-file`, `/api/verification/test-extraction`, `/api/verification/test-chunking`, `/api/verification/test-embedding`, `/api/verification/verify-vectors/{vector_id}`, `/api/verification/ingest-with-verification`, `/api/verification/session/{session_id}`, `/api/verification/sessions`, `/api/verification/analyze-chunks`, `/api/verification/test-similarity`, `/api/verification/performance-stats`, `/api/verification/debug/file-access/{file_path:path}`, `/api/verification/health`, `/api/verification/dashboard`.

### Dependencies

The Monitoring service relies on:

*   `psutil`: For collecting system-level resource metrics.
*   `requests`: For probing external services (e.g., API server itself).
*   `threading`, `asyncio`: For running background monitoring loops and asynchronous operations.
*   `json`, `datetime`, `pathlib`: For data serialization, timestamps, and file system operations.
*   `IngestionEngine`: To trigger document processing and deletion.
*   `ConfigManager`: For configuration management.
*   `DependencyContainer`: To access other system components for health checks.
*   `PipelineVerifier`: For detailed ingestion pipeline verification (in `EnhancedFolderMonitor`).