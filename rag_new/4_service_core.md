# 4_service_core.md - Core Services Documentation

## Core Services Documentation

### Overview

The Core Services (`rag_system/src/core/`) form the foundational layer of the RAG system, providing essential functionalities and infrastructure that all other components rely upon. This module ensures the system's stability, configurability, and efficient resource management.

### Key Responsibilities

*   **Configuration Management**: Centralized handling of system settings and environment overrides.
*   **Dependency Injection**: Manages the creation and provision of all system components, promoting modularity and testability.
*   **Error Handling**: Provides a unified, robust framework for managing and reporting errors across the entire system.
*   **Metadata Management**: Ensures consistency and proper linking of all metadata associated with documents and vectors.
*   **Resource Management**: Optimizes the allocation and cleanup of system resources, particularly for memory-intensive machine learning models.
*   **Progress Tracking**: Monitors the progress of long-running operations like document ingestion.
*   **System Initialization**: Orchestrates the startup sequence, including logging setup and directory creation.
*   **Pipeline Verification**: Offers tools for detailed, step-by-step validation of the ingestion pipeline.

### Components

The Core Services module comprises several critical components:

#### 1. `ConfigManager` (`rag_system/src/core/config_manager.py`)

*   **Role**: Manages the system's configuration.
*   **Responsibilities**:
    *   Loads configuration from `system_config.json`.
    *   Applies environment variable overrides for flexible deployment.
    *   Provides structured access to various configuration sections (e.g., `VectorStoreConfig`, `EmbeddingConfig`, `LLMConfig`, `APIConfig`, `IngestionConfig`).
    *   Validates configuration settings and reports issues.
    *   Saves and updates configuration dynamically.

#### 2. `DependencyContainer` (`rag_system/src/core/dependency_container.py`)

*   **Role**: Implements a simple dependency injection (DI) pattern.
*   **Responsibilities**:
    *   Registers service factories and instances.
    *   Provides a centralized mechanism to `get` service instances, resolving their dependencies automatically.
    *   Supports singleton and non-singleton services.
    *   Helps prevent circular dependencies during component creation.
    *   Used globally to access core system components.

#### 3. `Error Handling` (`rag_system/src/core/error_handling.py` and `rag_system/src/core/unified_error_handling.py`)

*   **Role**: Provides a comprehensive and unified error management system.
*   **Responsibilities**:
    *   Defines standardized `ErrorCode` enums for various error types.
    *   Introduces `ErrorInfo` and `ErrorContext` for detailed error reporting.
    *   Implements a `Result` monad for functional error handling (`Result.ok()` / `Result.fail()`).
    *   Provides `with_error_handling` decorators for easy integration into functions.
    *   Includes an `ErrorTracker` for monitoring and aggregating system errors.
    *   Maintains backward compatibility with older `RAGSystemError` exceptions.

#### 4. `MetadataManager` (`rag_system/src/core/metadata_manager.py`)

*   **Role**: Ensures consistency and proper linking of all metadata.
*   **Responsibilities**:
    *   Defines a `MetadataSchema` for standardized metadata structure.
    *   Provides `MetadataValidator` for validating and normalizing incoming metadata.
    *   Generates consistent `doc_id` and `vector_id` values.
    *   Merges multiple metadata dictionaries with conflict resolution.
    *   Prepares metadata for storage in the vector store and recovers it with migration support.

#### 5. `ModelMemoryManager` (`rag_system/src/core/model_memory_manager.py`)

*   **Role**: Optimizes memory usage for machine learning models.
*   **Responsibilities**:
    *   Manages the loading and unloading of ML models (e.g., Sentence Transformers) to prevent memory leaks.
    *   Uses weak references and a background thread to automatically evict idle models.
    *   Tracks memory usage and provides statistics on model lifecycle.

#### 6. `PipelineVerifier` (`rag_system/src/core/pipeline_verifier.py`)

*   **Role**: Provides tools for detailed verification of the ingestion pipeline.
*   **Responsibilities**:
    *   Defines `PipelineStage` and `VerificationStatus` for granular tracking.
    *   Performs checks at each stage of document processing (file validation, extraction, chunking, embedding, storage).
    *   Generates detailed `VerificationResult` objects.
    *   Can emit real-time events for progress monitoring.
    *   Generates comprehensive verification reports.

#### 7. `ProgressTracker` (`rag_system/src/core/progress_tracker.py`)

*   **Role**: Tracks the progress of long-running operations, especially document ingestion.
*   **Responsibilities**:
    *   Defines `ProgressStatus` and `ProgressStage` for granular tracking.
    *   Manages `FileProgress` for individual files and aggregates `BatchProgress`.
    *   Provides real-time updates on overall progress, estimated time remaining, and resource usage.
    *   Supports persistence of progress state across restarts.
    *   Offers callbacks for external components to subscribe to progress updates.

#### 8. `ResourceManager` (`rag_system/src/core/resource_manager.py`)

*   **Role**: Centralized management of system resources.
*   **Responsibilities**:
    *   Registers and tracks various resources (e.g., thread pools, file handles, model instances).
    *   Provides generic and custom cleanup handlers to prevent resource leaks.
    *   Manages application lifecycle (startup, shutdown) to ensure all resources are properly released.
    *   Handles system signals (e.g., `SIGINT`, `SIGTERM`) for graceful shutdown.

#### 9. `System Initialization` (`rag_system/src/core/system_init.py`)

*   **Role**: Orchestrates the initial setup of the entire RAG system.
*   **Responsibilities**:
    *   Sets up logging configuration.
    *   Creates necessary data directories.
    *   Validates system requirements and dependencies.
    *   Initializes core components and registers them with the `DependencyContainer`.
    *   Performs a basic health check during startup.

### Data Flow within Core Services

1.  **Initialization**: During `System Initialization`, `ConfigManager` loads settings. `DependencyContainer` is populated with factories for all core components. `ResourceManager` is initialized to oversee resource lifecycle.
2.  **Component Access**: Other services (e.g., `IngestionEngine`, `QueryEngine`) request necessary components from the `DependencyContainer`. The container either provides an existing instance or creates a new one using its registered factory.
3.  **Configuration Access**: Components retrieve their specific settings from the `ConfigManager`.
4.  **Error Reporting**: When an error occurs in any part of the system, it is wrapped in an `ErrorInfo` object and passed to the `ErrorHandler`, which logs it, triggers callbacks, and updates the `ErrorTracker`.
5.  **Metadata Handling**: `MetadataManager` is used by `IngestionEngine` to generate consistent IDs, merge, validate, and prepare metadata for storage. It's also used by `QueryEngine` to retrieve metadata for search results.
6.  **Resource Allocation/Deallocation**: `ResourceManager` allocates resources like `ManagedThreadPools` and `ManagedModelLoaders` to other services. During shutdown, `ResourceManager` ensures all registered resources are properly cleaned up.
7.  **Progress Updates**: `ProgressTracker` receives updates from `IngestionEngine` and other long-running processes, storing and aggregating progress data.
8.  **Health Checks**: `HeartbeatMonitor` (from the Monitoring module) queries various core components (e.g., `FAISSStore`, `LLMClient`, `DependencyContainer`) for their status, leveraging their internal health-check methods.

### API Endpoints (Indirect Interaction)

The Core Services are primarily internal, but their functionalities are exposed indirectly through the main `API` service (`rag_system/src/api/main.py`) via endpoints like:

*   **`/health`**: Utilizes `System Initialization`'s health check and `HeartbeatMonitor`.
*   **`/config`**: Exposes `ConfigManager` settings.
*   **`/stats`**: Aggregates statistics from various components, including those managed by Core Services.

### Dependencies

Core Services are designed to be self-contained and foundational. They primarily depend on standard Python libraries (e.g., `os`, `json`, `datetime`, `threading`, `logging`, `pathlib`, `enum`, `dataclasses`, `uuid`, `traceback`, `functools`, `contextlib`, `psutil`, `atexit`, `signal`, `sys`, `gc`, `concurrent.futures`) and specific external libraries for specialized tasks (e.g., `faiss`, `sentence_transformers`, `qdrant_client`, `groq`, `openai`, `azure.ai.inference`, `langchain`, `langgraph`, `requests`, `sqlite3`, `tqdm`, `numpy`, `pandas`, `openpyxl`, `PIL`, `PyPDF2`, `docx`, `fitz`, `camelot`, `pytesseract`, `dotenv`).