# Gemini Application Architecture Overview

This document provides a detailed and comprehensive overview of the Gemini application's architecture, designed for scalability, modularity, and efficient operation within an enterprise RAG (Retrieval-Augmented Generation) system. It elucidates the interplay between various components, technologies, and data flows, offering a blueprint for understanding, maintaining, and extending the system.

## 1. Introduction

The Gemini application is a sophisticated Enterprise RAG System engineered to provide intelligent support through advanced natural language processing and information retrieval. Its architecture is fundamentally modular, allowing for flexible integration of diverse AI/ML models, data sources, and external services. The system is bifurcated into a robust Python backend and a dynamic React frontend, complemented by specialized modules for data generation and enterprise system integration.

## 2. Core Architectural Principles

*   **Modularity:** Components are designed as independent, interchangeable units, facilitating easier development, testing, and maintenance.
*   **Scalability:** The architecture supports horizontal scaling of backend services and flexible data storage solutions to accommodate growing data volumes and user loads.
*   **Extensibility:** New LLM providers, document types, and external integrations can be seamlessly added without significant architectural overhauls.
*   **Observability:** Comprehensive logging, monitoring, and error handling mechanisms are integrated throughout the system to ensure operational transparency and rapid issue identification.
*   **Security:** Emphasis on secure handling of credentials, data privacy, and robust error management to prevent information leakage.
*   **Asynchronous Processing:** Leveraging asynchronous operations in the backend for improved responsiveness and resource utilization.

## 3. High-Level Architecture

At a high level, the Gemini application comprises the following interconnected layers and modules:

```mermaid
graph TD
    User[User] -->|Interacts via| Frontend[React Frontend]
    Frontend -->|API Requests| Backend[FastAPI Backend]

    Backend -->|Manages| CoreRAG[Core RAG System]
    Backend -->|Integrates with| ServiceNowInt[ServiceNow Integration Module]

    CoreRAG -->|Uses| LLMProviders[External LLM Providers (Groq, OpenAI, Azure AI)]
    CoreRAG -->|Accesses| VectorStore[Vector Store (FAISS/Qdrant)]
    CoreRAG -->|Accesses| MetadataStore[Metadata Store]
    CoreRAG -->|Uses| DocProcessors[Document Processors]
    CoreRAG -->|Monitors| MonitoredFolders[Monitored Folders]

    ServiceNowInt -->|Communicates with| ServiceNow[ServiceNow Platform]

    SubGraph DataGeneration
        DocGenerator[Document Generator] -->|Creates Test Data| MonitoredFolders
    end

    Backend -->|Logs to| LoggingSystem[Logging System]
    Backend -->|Metrics to| MonitoringSystem[Monitoring System]

    style Frontend fill:#f9f,stroke:#333,stroke-width:2px
    style Backend fill:#bbf,stroke:#333,stroke-width:2px
    style CoreRAG fill:#ccf,stroke:#333,stroke-width:2px
    style ServiceNowInt fill:#cfc,stroke:#333,stroke-width:2px
    style LLMProviders fill:#ffc,stroke:#333,stroke-width:2px
    style VectorStore fill:#fcf,stroke:#333,stroke-width:2px
    style MetadataStore fill:#fcf,stroke:#333,stroke-width:2px
    style DocProcessors fill:#cff,stroke:#333,stroke-width:2px
    style MonitoredFolders fill:#eee,stroke:#333,stroke-width:2px
    style ServiceNow fill:#9f9,stroke:#333,stroke-width:2px
    style DocGenerator fill:#fcc,stroke:#333,stroke-width:2px
    style LoggingSystem fill:#ddd,stroke:#333,stroke-width:2px
    style MonitoringSystem fill:#ddd,stroke:#333,stroke-width:2px
```

## 4. Detailed Component Breakdown

### 4.1. Frontend (React Application)

*   **Technology Stack:** React, Vite, TypeScript, Tailwind CSS, Radix UI, React Router DOM, React Markdown, Axios.
*   **Role:** Serves as the primary interface for end-users. It provides a rich, interactive experience for submitting queries, viewing responses, and managing application settings or documents. It communicates with the FastAPI backend via RESTful API calls.
*   **Key Sub-components:**
    *   **Pages:** Defines distinct views of the application (e.g., `HomePage`, `ConversationPage`, `AdminDashboardPage`, `RagPage`, `LoginPage`).
    *   **UI Components:** Reusable and composable UI elements (e.g., `Alert`, `Avatar`, `Button`, `Card`, `Input`, `Label`) built with Radix UI primitives and styled with Tailwind CSS for consistency and rapid development.
    *   **Utilities:** Client-side logic for authentication, data formatting, and other common tasks (`auth.ts`, `cn.ts`, `sourceFormatter.js`).

### 4.2. Backend (FastAPI Application)

*   **Technology Stack:** FastAPI, Uvicorn, Python, Pydantic, various AI/ML libraries.
*   **Role:** The central nervous system of the application. It exposes a comprehensive set of APIs to the frontend and orchestrates all core RAG functionalities, including data ingestion, query processing, LLM interactions, and integrations with external systems.
*   **Key Sub-modules (`rag_system/src/`):**
    *   **`api/` (API Layer):** Defines the external-facing API endpoints (`routes/`) and their corresponding request/response data models (`models/`). It acts as the gateway for all client-side interactions.
    *   **`conversation/` (Conversation Management):** Manages the state, context, and flow of multi-turn conversations. It includes components for smart routing of queries, context awareness, and memory management to maintain conversational coherence.
    *   **`core/` (Core Services):** Provides foundational services essential for the application's operation. This includes `config_manager` for centralized configuration, `dependency_container` for managing service dependencies, `error_handling` for robust error management, `metadata_manager` for document metadata, and `resource_manager` for system resource allocation.
    *   **`ingestion/` (Ingestion Engine):** Responsible for the entire document ingestion pipeline. It encompasses `chunker` for breaking down documents, `embedder` for generating vector representations, and a suite of `processors/` (e.g., `pdf_processor`, `excel_processor`) to handle diverse document formats. It also includes a `scheduler` for automated ingestion tasks.
    *   **`integrations/`:** Houses modules for seamless integration with third-party services. Notably, `azure_ai/` provides clients and validators for Azure AI services (e.g., Document Intelligence, LLM Inference), and `servicenow/` facilitates communication with the ServiceNow platform.
    *   **`monitoring/`:** Implements internal monitoring capabilities, including `folder_monitor` for detecting new documents, `heartbeat_monitor` for system health checks, and `logger` for comprehensive event logging. Metrics are exposed for external monitoring systems.
    *   **`retrieval/`:** The core of the RAG functionality. It includes `llm_client` for interacting with various LLM providers, `query_engine` for executing searches against the vector store, `query_enhancer` for optimizing user queries, and `reranker` for improving the relevance of retrieved results.
    *   **`storage/`:** Manages the persistence layer. It supports `faiss_store` for local vector indexing and `qdrant_store` for scalable, cloud-native vector database operations. It also manages `feedback_store` and `persistent_metadata_store` for application-specific data.
    *   **`utils/`:** A collection of general-purpose utility functions, such as `source_formatter`.

### 4.3. ServiceNow Integration Module (`ServiceNow-Int/`)

*   **Technology Stack:** Python, leveraging `requests` and `python-dotenv`.
*   **Role:** A specialized module designed for deep integration with the ServiceNow platform. It handles bidirectional data synchronization, allowing the RAG system to ingest information from ServiceNow and perform actions like creating incidents or updating records within ServiceNow.
*   **Key Sub-modules:**
    *   `backend_integration.py`: Orchestrates the data flow and business logic specific to ServiceNow integration.
    *   `servicenow_connector.py`: Manages authenticated API calls to the ServiceNow instance.
    *   `servicenow_scheduler.py`: Handles scheduled tasks for periodic data pulls or pushes to ServiceNow.

### 4.4. Data Storage

*   **Vector Stores:**
    *   **FAISS:** Utilized for efficient similarity search, particularly suitable for local development or smaller-scale deployments. Data is stored in flat files within `data/vectors/`.
    *   **Qdrant:** A cloud-native vector database offering high scalability and performance for production environments. The system supports migration from FAISS to Qdrant (`faiss_to_qdrant_migration.py`).
*   **Metadata Store:** Stores structured information about ingested documents, managed by `rag_system/src/core/metadata_manager.py`.
*   **Feedback Store:** Captures user feedback for continuous improvement, managed by `rag_system/src/storage/feedback_store.py`.
*   **File System:** `data/uploads/` for raw ingested documents and `data/logs/` for application logs.

### 4.5. External AI Services

*   **LLM Providers:** Integration with various Large Language Model services (e.g., Groq, OpenAI, Azure AI Inference) for natural language understanding, generation, and conversational capabilities.
*   **Azure AI Services:** Leveraged for advanced document processing, including optical character recognition (OCR) and intelligent document analysis, enhancing the quality of ingested data.

## 5. Data Flow and Interactions

### 5.1. User Query Flow

1.  **User Input:** A user submits a query via the React Frontend.
2.  **API Request:** The Frontend sends an API request to the FastAPI Backend (`/conversation` endpoint).
3.  **Query Processing (Backend):** The Backend's `Conversation Management` module processes the query, potentially using `query_enhancer` to refine it.
4.  **Information Retrieval:** The `Retrieval Engine` queries the `Vector Store` (FAISS/Qdrant) to find relevant document chunks and retrieves associated metadata from the `Metadata Store`.
5.  **LLM Interaction:** The `LLM Client` forwards the user query and retrieved context to an `External LLM Provider`.
6.  **Response Generation:** The LLM generates a response based on the query and context.
7.  **Response to User:** The Backend sends the generated response back to the Frontend, which displays it to the user.

### 5.2. Document Ingestion Flow

1.  **Document Drop/Detection:** New documents are placed in `Monitored Folders` (or uploaded via UI).
2.  **Monitoring Trigger:** The `Monitoring` module detects the new document.
3.  **Ingestion Initiation:** The `Ingestion Engine` is triggered.
4.  **Document Processing:** The `Ingestion Engine` utilizes appropriate `Document Processors` (e.g., `pdf_processor`, `excel_processor`) to extract text and other data. This may involve calls to `Azure AI Vision/Document Intelligence` for advanced parsing.
5.  **Chunking & Embedding:** The extracted content is passed to the `Chunker` and then the `Embedder` to create vector representations.
6.  **Storage:** The generated embeddings are stored in the `Vector Store`, and document metadata is saved in the `Metadata Store`.

### 5.3. ServiceNow Data Synchronization Flow

1.  **Scheduled Sync:** The `ServiceNow Scheduler` (within `ServiceNow-Int`) initiates a synchronization task.
2.  **Data Fetch:** The `ServiceNow Connector` makes API calls to the `ServiceNow Platform` to retrieve or update data (e.g., incidents, knowledge articles).
3.  **Processing:** Data is processed by the `ServiceNow Processor` (within `rag_system/src/integrations/servicenow/`) and integrated into the RAG system's `Vector Store` and `Metadata Store`.
4.  **Action Trigger (Optional):** Based on RAG system logic, actions (e.g., creating a new incident) can be triggered via the `ServiceNow Connector`.

## 6. Scalability and Extensibility

*   **Microservice-Oriented Design:** The clear separation of concerns between the FastAPI backend, ServiceNow integration, and frontend allows for independent development, deployment, and scaling of each component.
*   **Containerization Readiness:** The Python backend and Node.js frontend are designed to be easily containerized (e.g., Docker), enabling deployment on container orchestration platforms like Kubernetes for high availability and scalability.
*   **Pluggable Components:** The `ingestion/processors`, `retrieval/llm_client`, and `storage/` modules are designed with interfaces that allow for easy integration of new document types, LLM providers, or vector databases without affecting other parts of the system.
*   **Asynchronous Operations:** FastAPI's asynchronous nature and the use of `aiofiles` and `requests` ensure that I/O-bound operations do not block the main event loop, enhancing responsiveness and throughput.

## 7. Security Considerations

*   **Environment Variables:** Sensitive information (API keys, credentials) is managed through environment variables (`.env` files) and not hardcoded in the codebase.
*   **API Key Management:** Secure handling and rotation of API keys for external services.
*   **Input Validation:** Pydantic models are used extensively for robust input validation on API endpoints, preventing common security vulnerabilities like injection attacks.
*   **Error Handling:** Centralized error handling (`rag_system/src/core/error_handling.py`) ensures that sensitive system details are not exposed in error responses.
*   **Dependency Management:** Regular updates of Python and Node.js dependencies to mitigate known security vulnerabilities.

## 8. Conclusion

The Gemini application's architecture is a testament to a thoughtful design that prioritizes modularity, scalability, and extensibility. By clearly defining roles and interactions between components, and by embracing modern development practices, the system is well-positioned for continuous evolution and adaptation to future requirements, providing a robust and intelligent support solution.