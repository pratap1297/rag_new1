# 7_testing_documentation.md - Testing Documentation

## Testing Documentation: RAG System

This document outlines the testing strategy and methodologies employed for the RAG (Retrieval-Augmented Generation) System. Comprehensive testing is crucial to ensure the system's accuracy, reliability, performance, and scalability.

### 1. Testing Philosophy

Our testing philosophy is based on a multi-layered approach, combining automated and manual testing techniques across different stages of the software development lifecycle. We emphasize:

*   **Shift-Left Testing**: Integrating testing early in the development process.
*   **Automation**: Maximizing automated tests to ensure rapid feedback and efficient regression testing.
*   **Coverage**: Aiming for comprehensive test coverage across all critical functionalities and components.
*   **Performance**: Regularly assessing system performance under various loads.
*   **Data Integrity**: Verifying that data is correctly ingested, stored, and retrieved.
*   **User Experience**: Ensuring the system meets user expectations for accuracy and usability.

### 2. Testing Types and Methodologies

#### 2.1. Unit Testing

*   **Purpose**: To test individual components or functions in isolation.
*   **Methodology**: Developers write unit tests for their code using `pytest`.
*   **Coverage**: Aim for high code coverage (e.g., >80%) for critical business logic and utility functions.
*   **Examples**:
    *   `rag_system/src/core/config_manager.py`: Test `ConfigManager`'s ability to load, validate, and apply environment overrides.
    *   `rag_system/src/ingestion/chunker.py`: Test `Chunker`'s ability to split text correctly with various chunk sizes and overlaps.
    *   `rag_system/src/retrieval/query_enhancer.py`: Test `QueryEnhancer`'s intent detection and query reformulation logic.
    *   `rag_system/src/integrations/servicenow/processor.py`: Test `ServiceNowTicketProcessor`'s ability to parse raw incident data and extract specific fields.

#### 2.2. Integration Testing

*   **Purpose**: To test the interactions and interfaces between different modules or services.
*   **Methodology**: Tests are written to verify that components work together as expected.
*   **Examples**:
    *   **Ingestion Pipeline**: Test the flow from document input (`IngestionEngine`) through `Chunker`, `Embedder`, and `FAISSStore`/`QdrantVectorStore` (`test_document_ingestion.py`, `test_comprehensive_pipeline.py`).
    *   **Query Pipeline**: Test the flow from query input through `Embedder`, `FAISSStore`/`QdrantVectorStore`, `Reranker`, and `LLMClient` (`test_default_query.py`, `test_final_queries.py`).
    *   **API Endpoints**: Test that API endpoints correctly interact with their underlying services (e.g., `test_api.py`, `test_frontend_api.py`).
    *   **ServiceNow Integration**: Test that `ServiceNowConnector` can fetch data and `ServiceNowScheduler` can process and ingest it (`test_network_queries.py`, `test_pdf_azure_integration.py`).

#### 2.3. End-to-End (E2E) Testing

*   **Purpose**: To test the entire system from a user's perspective, simulating real-world scenarios.
*   **Methodology**: Automated tests that interact with the system through its external interfaces (e.g., API, UI).
*   **Examples**:
    *   **Conversational Flow**: Simulate a multi-turn conversation, verifying context retention and accurate responses (`test_complete_system.py`, `test_unified_rag_integration.py`).
    *   **Document Upload & Query**: Upload a document via the UI/API, then query for its content to ensure it's retrievable (`test_unified_ui_integration.py`).
    *   **Folder Monitoring**: Set up a monitored folder, add a file, and verify its automatic ingestion and subsequent retrievability.
    *   **`IngestionVerifier`**: The `rag_system/src/core/ingestion_verification_system.py` provides a comprehensive framework for E2E ingestion testing, including checks for text extraction, chunking, embedding, vector storage, and retrieval consistency.

#### 2.4. Performance Testing

*   **Purpose**: To evaluate the system's responsiveness, stability, and scalability under various load conditions.
*   **Methodology**: Use tools like `Locust` or `JMeter` to simulate concurrent users and measure response times, throughput, and resource utilization.
*   **Focus Areas**:
    *   **Query Latency**: Measure response times for queries under increasing load.
    *   **Ingestion Throughput**: Measure the rate at which documents can be processed and ingested.
    *   **Resource Utilization**: Monitor CPU, memory, and disk I/O during peak loads.
*   **Examples**:
    *   `test_memory_leak_fixes.py`: Focuses on memory usage during long-running operations.
    *   `test_api_timeout.py`: Tests API behavior under timeout conditions.
    *   `IngestionMonitor` (`rag_system/src/core/ingestion_debug_tools.py`): Provides tools for recording and analyzing ingestion performance metrics.

#### 2.5. Security Testing

*   **Purpose**: To identify vulnerabilities and weaknesses in the system's security posture.
*   **Methodology**: Includes penetration testing, vulnerability scanning, and code reviews focused on security best practices.
*   **Focus Areas**:
    *   API authentication and authorization bypasses.
    *   Data leakage (e.g., sensitive information in logs, unencrypted communication).
    *   Injection vulnerabilities (if any direct database/shell interactions).
    *   Denial-of-Service (DoS) vulnerabilities.

#### 2.6. Regression Testing

*   **Purpose**: To ensure that new changes or bug fixes do not negatively impact existing functionalities.
*   **Methodology**: All automated unit, integration, and E2E tests are run as part of the Continuous Integration (CI) pipeline after every code change.

### 3. Test Automation and CI/CD Integration

*   **Test Framework**: `pytest` is used as the primary testing framework for Python code.
*   **Mocking/Patching**: `unittest.mock` is used for mocking external dependencies (e.g., LLM APIs, external databases) during unit and integration tests.
*   **CI/CD Pipeline**: Tests are integrated into a CI/CD pipeline (e.g., GitHub Actions, GitLab CI, Jenkins) to run automatically on every push or pull request.
    *   **Stages**: The pipeline typically includes linting, unit tests, integration tests, and potentially E2E tests for critical paths.
    *   **Reporting**: Test results and code coverage reports are generated and published.

### 4. Test Data Management

*   **Sample Documents**: A set of diverse sample documents (PDFs, DOCXs, Excels, etc.) is maintained for ingestion and query testing (`create_test_files` in `rag_system/src/core/ingestion_verification_system.py`).
*   **Mock Data**: Mock responses for external APIs (e.g., LLMs, ServiceNow) are used to ensure test stability and independence.
*   **Test Databases**: Dedicated test databases (FAISS/Qdrant collections, SQLite files) are used for testing and are typically cleared before each test run.

### 5. Test Coverage

*   **Code Coverage**: Tools like `pytest-cov` are used to measure code coverage, aiming for high coverage in core logic.
*   **Functional Coverage**: Ensure all user flows and API endpoints are covered by automated tests.
*   **Error Handling Coverage**: Specific tests are written to verify that error handling mechanisms correctly capture, log, and report errors under various failure conditions.

### 6. Test Files and Directories

*   **`rag_new/rag_system/test_*.py`**: Contains various test scripts for different components and functionalities.
    *   `test_api_with_working_embeddings.py`
    *   `test_backend_qdrant.py`
    *   `test_comprehensive_metadata_fixes.py`
    *   `test_comprehensive_pipeline.py`
    *   `test_config_loading.py`
    *   `test_default_query.py`
    *   `test_doc_id_consistency.py`
    *   `test_document_ingestion.py`
    *   `test_enhanced_folder_monitoring.py`
    *   `test_existing_data.py`
    *   `test_feedback_system.py`
    *   `test_final_queries.py`
    *   `test_frontend_api.py`
    *   `test_memory_leak_fixes.py`
    *   `test_metadata_fix.py`
    *   `test_monitoring_fix.py`
    *   `test_network_queries.py`
    *   `test_pdf_azure_integration.py`
    *   `test_pdf_content_analysis.py`
    *   `test_pdf_ingestion.py`
    *   `test_pipeline_verification.py`
    *   `test_processor_chunks_fix.py`
    *   `test_qdrant_capabilities_demo.py`
    *   `test_qdrant_functionality.py`
    *   `test_qdrant_system.py`
    *   `test_qdrant_ui_integration.py`
    *   `test_qdrant_with_data.py`
    *   `test_router_query.py`
    *   `test_semantic_chunker_memory.py`
    *   `test_specific_queries.py`
    *   `test_threshold_fix.py`
    *   `test_unified_error_handling.py`
    *   `test_unified_processors_comprehensive.py`
    *   `test_unified_processors.py`
    *   `test_unified_rag_integration_simple.py`
    *   `test_unified_rag_integration.py`
    *   `test_unified_ui_integration.py`
    *   `test_working_system.py`
    *   `test_zero_threshold.py`

This comprehensive testing approach ensures the RAG system is robust, reliable, and performs as expected in various operational scenarios.