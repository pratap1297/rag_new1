# Gemini Application Regeneration Report

This report provides a comprehensive overview of the application's architecture, technology stack, and setup instructions, enabling a developer to regenerate the complete application environment.

## 1. Project Overview

This is an Enterprise RAG (Retrieval-Augmented Generation) System designed to provide intelligent support. It integrates various AI/ML components for document ingestion, conversation management, and data retrieval, with a web-based user interface and a dedicated ServiceNow integration module.

**Key Functionalities:**
*   **Document Ingestion:** Processes various document types (PDF, DOCX, Excel, Text) and extracts content for embedding.
*   **Vector Storage:** Utilizes vector databases (FAISS, Qdrant) for efficient similarity search.
*   **LLM Integration:** Connects with multiple LLM providers (Groq, OpenAI, Azure AI) for conversational AI and query enhancement.
*   **Conversation Management:** Manages conversational flow, context, and memory.
*   **ServiceNow Integration:** Dedicated module for interacting with ServiceNow, including data synchronization and incident management.
*   **Monitoring:** Includes components for folder monitoring and system health checks.
*   **Web UI:** A Gradio-based UI for interaction and a React-based frontend for a richer user experience.

## 2. Tech Stack

### 2.1. Backend (Python)

The backend is primarily built with Python and leverages the following key libraries:

**Core Framework:**
*   `fastapi`: High-performance web framework for building APIs.
*   `uvicorn[standard]`: ASGI server for running FastAPI applications.
*   `pydantic`: Data validation and settings management.
*   `python-multipart`: For handling form data in API requests.

**AI/ML & Data Processing:**
*   `sentence-transformers`: For generating embeddings from text.
*   `cohere`: Integration with Cohere AI services.
*   `faiss-cpu`: For efficient similarity search (vector database).
*   `groq`: Integration with Groq LLM services.
*   `openai`: Integration with OpenAI LLM services.
*   `PyPDF2`: For PDF document processing.
*   `python-docx`: For Word document processing.
*   `python-magic`: For file type detection.
*   `openpyxl`: For reading and writing Excel files.
*   `pandas`: For data manipulation and analysis.
*   `numpy`: Fundamental package for numerical computing.
*   `xlrd`: For reading older Excel files.
*   `azure-cognitiveservices-vision-computervision`: For Azure AI Vision services.
*   `azure-ai-documentintelligence`: For Azure AI Document Intelligence.
*   `azure-ai-inference`: For Azure AI Inference LLM.
*   `msrest`, `azure-core`: Azure SDK core libraries.
*   `langgraph`, `langchain`, `langchain-core`, `langchain-community`: For building LLM applications and managing conversational graphs.

**System Utilities & Scheduling:**
*   `python-dotenv`: For managing environment variables.
*   `requests`: HTTP library for making API requests.
*   `aiofiles`: Asynchronous file operations.
*   `psutil`: For system and process utilities.
*   `portalocker`: For cross-platform file locking.
*   `APScheduler`: Advanced Python scheduler for background tasks.
*   `schedule`: Lightweight job scheduler.

**Security:**
*   `python-jose[cryptography]`: For JOSE (JSON Object Signing and Encryption) operations.

**UI Framework (Backend-driven):**
*   `gradio`: For building interactive web UIs for ML models.

**Monitoring & Observability:**
*   `prometheus-client`: For Prometheus metrics exposition.

### 2.2. Frontend (React)

The frontend is a React application built with Vite and uses the following technologies:

*   **Framework:** `React`
*   **Build Tool:** `Vite`
*   **Language:** `TypeScript`
*   **Styling:** `Tailwind CSS`, `clsx`, `tailwind-merge`
*   **UI Components:** `@radix-ui/react-avatar`, `@radix-ui/react-label`, `@radix-ui/react-slot`, `lucide-react`
*   **Routing:** `react-router-dom`
*   **Markdown Rendering:** `react-markdown`, `remark-gfm`
*   **HTTP Client:** `axios`

## 3. Application Structure

The project is organized into several key directories:

*   `rag_new/`: The root directory of the project.
    *   `rag_system/`: Contains the core RAG backend logic.
        *   `src/`: Source code for the RAG system.
            *   `api/`: FastAPI endpoints and related models.
                *   `routes/`: Defines API routes (e.g., `conversation.py`, `powerbi.py`, `servicenow.py`).
                *   `models/`: Pydantic models for API requests and responses.
                *   `main.py`: Main FastAPI application entry point.
                *   `enhanced_folder_endpoints.py`, `management_api.py`, `servicenow_ui.py`, `simple_enhanced_endpoints.py`, `verification_endpoints.py`: Various API endpoints.
            *   `conversation/`: Logic for managing conversational flow, state, and memory.
                *   `fresh_conversation_graph.py`, `fresh_conversation_nodes.py`, `fresh_context_manager.py`, `fresh_memory_manager.py`, `fresh_smart_router.py`: Core conversation components.
            *   `core/`: Fundamental utilities and services.
                *   `config_manager.py`: Manages application configuration.
                *   `dependency_container.py`: Dependency injection setup.
                *   `error_handling.py`: Centralized error handling.
                *   `json_store.py`: JSON-based data storage.
                *   `logging_config.py`: Logging configuration.
                *   `metadata_manager.py`: Manages document metadata.
                *   `model_memory_manager.py`: Manages LLM model memory.
                *   `resource_manager.py`: Manages system resources.
                *   `verified_ingestion_engine.py`: Core ingestion logic.
            *   `ingestion/`: Handles document ingestion, chunking, and embedding.
                *   `chunker.py`: Document chunking logic.
                *   `embedder.py`: Document embedding logic.
                *   `ingestion_engine.py`: Orchestrates the ingestion process.
                *   `memory_efficient_semantic_chunker.py`, `semantic_chunker.py`: Advanced chunking.
                *   `processors/`: Contains specific processors for different document types.
                    *   `base_processor.py`, `enhanced_pdf_processor.py`, `excel_processor.py`, `image_processor.py`, `pdf_processor.py`, `servicenow_processor.py`, `text_processor.py`, `word_processor.py`: Document type specific processing.
                *   `scheduler.py`: Schedules ingestion tasks.
            *   `integrations/`: Connectors for external services.
                *   `azure_ai/`: Azure AI services integration.
                    *   `azure_client.py`, `config_validator.py`, `robust_azure_client.py`: Azure client and configuration.
                *   `servicenow/`: ServiceNow integration components.
                    *   `connector.py`, `integration.py`, `processor.py`, `scheduler.py`: ServiceNow API interaction and data processing.
            *   `monitoring/`: System monitoring and health checks.
                *   `enhanced_folder_monitor.py`, `folder_monitor.py`, `heartbeat_monitor.py`, `logger.py`: Monitoring utilities.
            *   `retrieval/`: Logic for retrieving and enhancing information.
                *   `llm_client.py`: LLM client interface.
                *   `qdrant_query_engine.py`: Qdrant-specific query engine.
                *   `query_engine.py`: Generic query engine.
                *   `query_enhancer.py`: Enhances user queries.
                *   `reranker.py`: Reranks search results.
            *   `storage/`: Manages data storage.
                *   `faiss_store.py`: FAISS vector store implementation.
                *   `faiss_to_qdrant_migration.py`: Script for migrating data from FAISS to Qdrant.
                *   `feedback_store.py`: Stores user feedback.
                *   `persistent_metadata_store.py`: Persistent storage for metadata.
                *   `qdrant_store.py`: Qdrant vector store implementation.
            *   `utils/`: General utility functions.
                *   `source_formatter.py`: Formats source information.
    *   `ServiceNow-Int/`: Dedicated module for ServiceNow integration.
        *   `backend_integration.py`: Main backend integration logic.
        *   `servicenow_connector.py`: Encapsulates the logic for making authenticated API calls to the ServiceNow instance, handling requests and responses.
        *   `servicenow_scheduler.py` : Manages scheduled tasks for periodic data synchronization or automated workflows with ServiceNow.
    *   `document_generator/`: Tools for generating test data.
        *   `rag_data_generator.py`: Script for generating RAG test data.
    *   `frontend/`: Contains the React web application.
        *   `src/`: Frontend source code.
            *   `pages/`: React components for different application pages (e.g., `HomePage.tsx`, `ConversationPage.tsx`).
            *   `components/ui/`: Reusable UI components.
            *   `utils/`: Frontend utility functions.
            *   `App.tsx`, `index.css`, `main.tsx`: Core application files.
    *   `data/`: Directory for storing application data (e.g., `feedback_store.db`, `uploads/`, `vectors/`).
    *   `logs/`: Application logs.
    *   `pepenv/`: Python virtual environment.

## 4. Setup Instructions

### 4.1. Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd rag_new
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv pepenv
    # On Windows:
    .\pepenv\Scripts\activate
    # On macOS/Linux:
    source pepenv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r rag_system/requirements.txt
    pip install -r ServiceNow-Int/requirements.txt
    pip install -r document_generator/requirements.txt
    ```
    *(Note: Some dependencies like `python-magic-bin` might be needed on Windows if `python-magic` causes issues. Adjust accordingly.)*

4.  **Environment Variables:**
    Create a `.env` file in the `rag_new/` directory (or `rag_system/` if specific to the RAG system) and configure necessary environment variables such as API keys for LLM providers (Groq, OpenAI, Azure AI), Azure AI service endpoints, and ServiceNow credentials.
    Example `.env` (replace with your actual keys/endpoints):
    ```
    OPENAI_API_KEY="your_openai_api_key"
    GROQ_API_KEY="your_groq_api_key"
    AZURE_AI_ENDPOINT="your_azure_ai_endpoint"
    AZURE_AI_KEY="your_azure_ai_key"
    SERVICENOW_URL="your_servicenow_instance_url"
    SERVICENOW_USERNAME="your_servicenow_username"
    SERVICENOW_PASSWORD="your_servicenow_password"
    QDRANT_HOST="localhost"
    QDRANT_PORT="6333"
    ```

5.  **Run the FastAPI Application:**
    Navigate to the `rag_system` directory and run the main FastAPI application.
    ```bash
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    This will start the backend API server, typically accessible at `http://localhost:8000`.

### 4.2. Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

3.  **Run the React development server:**
    ```bash
    npm run dev
    ```
    This will start the frontend development server, usually accessible at `http://localhost:5173` (or a similar port).

### 4.3. Database/Vector Store Setup

*   **FAISS:** If using FAISS, it stores data locally in files. Ensure the `data/vectors/` directory exists and is accessible. Ingestion processes will create and manage FAISS indexes within this directory.
*   **Qdrant:** If using Qdrant, ensure a Qdrant instance is running (e.g., via Docker). The `QDRANT_HOST` and `QDRANT_PORT` environment variables should point to your Qdrant instance. You might need to run migration scripts if transitioning from FAISS.

### 4.4. ServiceNow Integration

The `ServiceNow-Int` directory contains scripts for integrating with ServiceNow.
*   Ensure the ServiceNow environment variables are correctly set in your `.env` file.
*   You can run specific scripts within this directory for tasks like data synchronization or testing the connection. For example:
    ```bash
    python ServiceNow-Int/servicenow_scheduler.py
    ```

## 5. Key Components and Their Roles (Detailed)

### 5.1. `rag_system/src`

*   **`api/`**: Exposes the core functionalities of the RAG system as RESTful APIs. This includes endpoints for conversational interactions, administrative tasks, and data retrieval.
*   **`conversation/`**: Manages the state and flow of conversations, including context handling, memory management, and routing user queries to appropriate handlers.
*   **`core/`**: Provides foundational services like configuration management, dependency injection, centralized error handling, and system initialization. It also includes components for verifying ingestion pipelines and managing metadata.
*   **`ingestion/`**: Orchestrates the process of taking raw documents, chunking them into smaller, manageable pieces, and generating embeddings. It supports various document types through specialized processors.
*   **`integrations/`**: Contains modules for connecting to external services, notably Azure AI for advanced document processing and LLM capabilities, and ServiceNow for enterprise service management.
*   **`monitoring/`**: Implements system monitoring and health checks, folder monitoring for new documents, and logging mechanisms to ensure the system's operational stability and data integrity.
*   **`retrieval/`**: Handles the core RAG logic, including interacting with LLMs, enhancing search queries, and retrieving relevant information from the vector store.
*   **`storage/`**: Manages the persistence layer for vector embeddings (FAISS, Qdrant) and metadata, ensuring efficient data storage and retrieval.
*   **`ui/`**: Contains the Gradio application code, providing a quick and interactive way to test and demonstrate the RAG system's capabilities.

### 5.2. `ServiceNow-Int/`

*   **`backend_integration.py`**: The central script for orchestrating data flow and interactions between the RAG system and ServiceNow.
*   **`servicenow_connector.py`**: Encapsulates the logic for making authenticated API calls to the ServiceNow instance, handling requests and responses.
*   **`servicenow_scheduler.py`**: Manages scheduled tasks for periodic data synchronization or automated workflows with ServiceNow.

### 5.3. `frontend/src`

*   **`pages/`**: Defines the main views of the web application, suchs as the home page, conversation interface, and administrative dashboards.
*   **`components/ui/`**: A collection of reusable UI components built with React and styled using Tailwind CSS, ensuring a consistent look and feel across the application.
*   **`utils/`**: Provides helper functions and utilities specific to the frontend, such as authentication logic and general-purpose helpers.

## 6. Running the Application

To run the complete application, you will need to start both the backend and frontend servers.

1.  **Start the Backend:**
    Open a terminal, navigate to `D:\Projects-D\pepsi-final3\rag_new\rag_system`, activate your Python virtual environment, and run:
    ```bash
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
    ```

2.  **Start the Frontend:**
    Open a separate terminal, navigate to `D:\Projects-D\pepsi-final3\rag_new\frontend`, and run:
    ```bash
    npm run dev
    ```

Once both are running, you can access the frontend application in your web browser, which will communicate with the backend API.
