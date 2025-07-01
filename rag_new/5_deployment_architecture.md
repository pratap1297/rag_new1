# 5_deployment_architecture.md - Deployment Architecture Documentation

## Deployment Architecture: RAG System

This document outlines the recommended deployment architecture for the RAG (Retrieval-Augmented Generation) System, focusing on scalability, reliability, and maintainability. The architecture is designed to support various deployment scenarios, from single-server setups to distributed, cloud-based environments.

### 1. High-Level Architecture Diagram

```mermaid
graph TD
    User[User Interface/Application] --> |API Calls| FastAPI_API[FastAPI API Service]
    FastAPI_API --> |Query/Ingest| RAG_Core[RAG Core Services]
    RAG_Core --> |Vector Search| Vector_Store[Vector Store (Qdrant/FAISS)]
    RAG_Core --> |Metadata Storage| Metadata_Store[Metadata Store (SQLite/JSON)]
    RAG_Core --> |LLM Inference| LLM_Service[LLM Service (Groq/Azure/OpenAI)]
    RAG_Core --> |Document Processing| Document_Processors[Document Processors]
    Document_Processors --> |External APIs (OCR/DI)| Azure_AI[Azure AI Services]
    FastAPI_API --> |Monitoring Data| Monitoring_Service[Monitoring Service]
    Monitoring_Service --> |Logs/Metrics| Log_Storage[Log Storage]
    Monitoring_Service --> |Alerts| Alerting_System[Alerting System]
    FastAPI_API --> |Scheduled Sync| External_Systems[External Systems (ServiceNow/PowerBI)]
    External_Systems --> |Data Fetch| RAG_Core
    Folder_Monitor[Monitored Folders] --> |File Changes| RAG_Core

    subgraph RAG System Components
        FastAPI_API
        RAG_Core
        Vector_Store
        Metadata_Store
        Document_Processors
        Monitoring_Service
    end

    subgraph External Services
        LLM_Service
        Azure_AI
        External_Systems
        Folder_Monitor
        Log_Storage
        Alerting_System
    end
```

### 2. Component Breakdown and Deployment Considerations

#### 2.1. User Interface/Application

*   **Description**: The frontend application that users interact with. This could be a custom web application, a chat bot interface, or the provided Gradio UI.
*   **Deployment**: Typically deployed as a static web application (e.g., S3, Azure Blob Storage) or a containerized web server (e.g., Nginx, Apache) separate from the backend API.
*   **Integration**: Communicates with the FastAPI API Service via RESTful API calls and WebSockets.

#### 2.2. FastAPI API Service (`rag_system/src/api/main.py`)

*   **Description**: The main backend service exposing all RAG system functionalities.
*   **Deployment**: 
    *   **Containerization**: Highly recommended using Docker. This ensures consistent environments and simplifies deployment.
    *   **Orchestration**: For production, deploy using Kubernetes (EKS, AKS, GKE) or Docker Swarm for scalability, high availability, and automated management.
    *   **Workers**: Utilize Uvicorn with Gunicorn for multiple worker processes to handle concurrent requests efficiently.
    *   **Load Balancing**: Place behind a load balancer (e.g., Nginx, AWS ALB, Azure Application Gateway) for traffic distribution and SSL termination.
*   **Scaling**: Scales horizontally by adding more instances/pods.

#### 2.3. RAG Core Services (`rag_system/src/core/`)

*   **Description**: Internal services managing configuration, dependency injection, error handling, and resource management. These are tightly coupled with the FastAPI API and typically run within the same process or container.
*   **Deployment**: Co-located with the FastAPI API Service.

#### 2.4. Vector Store (`rag_system/src/storage/faiss_store.py` or `rag_system/src/storage/qdrant_store.py`)

*   **Description**: Stores high-dimensional vector embeddings for semantic search.
*   **Deployment Options**:
    *   **FAISS (Local)**: For smaller deployments or proof-of-concepts, FAISS can run in-process within the RAG Core Service. This requires sufficient memory on the API server.
        *   **Persistence**: FAISS indexes are saved to disk (`data/vectors/index.faiss`). Ensure persistent storage (e.g., Kubernetes Persistent Volume, Docker Volume) is configured to prevent data loss on container restarts.
    *   **Qdrant (Dedicated Service)**: **Recommended for production.** Qdrant is a standalone vector database that can be deployed as a separate service.
        *   **Deployment**: Deploy Qdrant in its own container/pod, potentially in a high-availability cluster. It can be self-hosted or use a managed service (if available).
        *   **Persistence**: Qdrant inherently supports data persistence. Configure appropriate storage for its data directory.
        *   **Scaling**: Qdrant can scale independently of the RAG API service.

#### 2.5. Metadata Store (`rag_system/src/storage/persistent_metadata_store.py`)

*   **Description**: Stores metadata associated with documents and chunks (e.g., file paths, titles, authors, chunk indices).
*   **Deployment**: Currently uses local JSON files (`data/metadata/`).
    *   **Persistence**: Similar to FAISS, ensure persistent storage is configured for the `data/metadata` directory.
    *   **Scalability**: For very large-scale deployments or multi-instance setups, consider migrating to a centralized database (e.g., PostgreSQL, MongoDB) to avoid file-locking issues and enable easier scaling.

#### 2.6. LLM Service (`rag_system/src/retrieval/llm_client.py`)

*   **Description**: Provides Large Language Model inference capabilities.
*   **Deployment**: 
    *   **Managed Cloud Services**: **Recommended.** Utilize managed LLM services like Azure OpenAI, OpenAI API, or Groq API. This offloads infrastructure management, scaling, and GPU requirements.
    *   **Self-Hosted**: For specific requirements (e.g., custom models, strict data privacy), LLMs can be self-hosted. This requires significant GPU resources and expertise in model serving (e.g., using NVIDIA Triton Inference Server, vLLM, Hugging Face TGI).
*   **Integration**: Communicates with the RAG Core Services via HTTP/HTTPS.

#### 2.7. Document Processors (`rag_system/src/ingestion/processors/`)

*   **Description**: Components responsible for extracting content from various document types.
*   **Deployment**: Run within the RAG Core Service containers. Some processors (e.g., `EnhancedPDFProcessor`, `RobustExcelProcessor`) may interact with external Azure AI Services.

#### 2.8. Azure AI Services

*   **Description**: External cloud services for advanced document processing (e.g., Computer Vision for OCR, Document Intelligence for layout analysis).
*   **Deployment**: Consumed as managed services from Microsoft Azure. Requires proper API keys and endpoints configuration.

#### 2.9. Monitoring Service (`rag_system/src/monitoring/`)

*   **Description**: Collects health metrics, logs, and provides insights into system operations.
*   **Deployment**: 
    *   **Heartbeat Monitor**: Runs within the RAG Core Service containers, collecting internal metrics.
    *   **Log Storage**: Centralized logging solution (e.g., ELK Stack, Splunk, Azure Log Analytics) for collecting logs from all RAG components. Configure containers to send logs to this system.
    *   **Metrics Collection**: Prometheus/Grafana for time-series metrics and dashboards.
    *   **Alerting System**: PagerDuty, Opsgenie, or custom solutions for notifying administrators of critical issues.

#### 2.10. External Systems (ServiceNow, Power BI)

*   **Description**: Third-party systems that the RAG system integrates with for data ingestion.
*   **Deployment**: These are external systems. The RAG system connects to their APIs.

#### 2.11. Monitored Folders

*   **Description**: File system directories that the `FolderMonitor` watches for new or modified documents.
*   **Deployment**: These folders must be accessible by the RAG Core Service containers. In cloud environments, this typically means using network file systems (e.g., NFS, Azure Files, AWS EFS) mounted into the containers.

### 3. Network Architecture

*   **Public Access**: Only the FastAPI API Service should be publicly accessible, ideally through a secure gateway or load balancer with SSL/TLS encryption.
*   **Internal Communication**: All communication between RAG components (e.g., API to Vector Store, RAG Core to LLM Service) should be internal to the Virtual Private Cloud (VPC) or private network, secured with firewalls and network policies.
*   **Firewall Rules**: Implement strict firewall rules to allow only necessary ports and protocols between components.

### 4. Scalability Strategy

*   **Horizontal Scaling**: The FastAPI API Service and (if used) Qdrant can be scaled horizontally by adding more instances/pods.
*   **Stateless API**: The FastAPI API is designed to be largely stateless, simplifying horizontal scaling.
*   **Persistent Storage**: Ensure all stateful components (Vector Store, Metadata Store) use persistent volumes that can be shared or replicated across instances.
*   **Asynchronous Processing**: Long-running tasks (ingestion, complex queries) are handled asynchronously to prevent API blocking.

### 5. High Availability and Disaster Recovery

*   **Redundancy**: Deploy multiple instances of critical components (FastAPI API, Qdrant) across different availability zones.
*   **Automated Failover**: Utilize Kubernetes or cloud-native services for automated failover and self-healing capabilities.
*   **Data Backups**: Implement regular backup strategies for the Vector Store and Metadata Store. For Qdrant, leverage its snapshot capabilities.
*   **Disaster Recovery Plan**: Develop a comprehensive disaster recovery plan including RTO (Recovery Time Objective) and RPO (Recovery Point Objective) targets.