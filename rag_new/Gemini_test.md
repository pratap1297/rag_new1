## RAG System Test Case Generation Guide

This document outlines a strategy for creating test cases for the Enterprise RAG System, leveraging the provided architectural flow diagram. Testers can utilize existing data or generate new test data using an LLM.

### 1. Understanding the System Flow

Refer to the `Gemini_flow.md` Mermaid diagram for a visual representation of the RAG system's architecture and data flow. Each subgraph represents a major component or pipeline, and the arrows indicate data/control flow, often annotated with the methods involved.

**Key Subgraphs to Focus On:**

*   **User Interaction:** How users initiate actions (queries, uploads).
*   **API Layer:** The entry points and routing logic.
*   **Ingestion Pipeline:** The process of adding documents to the knowledge base.
*   **Query Pipeline:** How user questions are processed to retrieve answers.
*   **Conversational Flow:** The stateful interaction and dialogue management.
*   **System Management & Monitoring:** Backend operations, health checks, and configuration.

### 2. Test Case Creation Strategy

For each test case, consider the following:

*   **Test Case ID:** Unique identifier (e.g., `ING-001`, `QRY-005`, `CONV-002`).
*   **Component/Module:** The specific part of the system being tested (e.g., `IngestionEngine`, `QueryEngine`, `LLMClient`).
*   **Scenario Description:** A brief, clear description of what is being tested.
*   **Preconditions:** Any setup required before executing the test (e.g., system running, specific data ingested).
*   **Input Data:**
    *   **Source:** Specify if using existing data (provide path/description) or LLM-generated data (provide prompt).
    *   **Details:** Content of the document, query string, conversation turn, API payload.
*   **Expected Output:**
    *   **Functional:** The expected response, retrieved documents, conversation state, system status.
    *   **Non-Functional:** Performance metrics (response time, resource usage), error messages (if applicable).
*   **Steps to Execute:** Detailed steps to perform the test.
*   **Post-conditions/Cleanup:** Any state changes or cleanup required after the test.
*   **Error Handling:** How the system should behave under invalid inputs or failures.

### 3. Specific Areas for Test Case Generation

#### 3.1. Ingestion Pipeline (`IngestionEngine`, `Processors`, `Chunker`, `Embedder`, `VectorStore`, `MetadataStore`, `FolderMonitor`)

**Goal:** Verify that documents are correctly processed, chunked, embedded, and stored, and that metadata is preserved.

*   **Functional Tests:**
    *   **Successful Ingestion:** Upload various supported file types (`.pdf`, `.docx`, `.xlsx`, `.txt`, `.md`, `.json`, `.jpg`, etc.) and verify they are ingested, chunks are created, and vectors are stored.
    *   **Metadata Preservation:** Ensure custom metadata provided during upload is correctly associated with chunks.
    *   **Content Extraction Accuracy:** Verify that text extracted from complex documents (e.g., tables in PDFs, images in Excel) is accurate.
    *   **Chunking Logic:** Test documents with varying lengths, structures (headings, lists, code blocks) to ensure appropriate chunk sizes and overlaps.
    *   **Duplicate Handling:** Upload the same file multiple times; verify it's skipped or updated correctly.
    *   **Folder Monitoring:** Place new/modified files in a monitored folder and verify automatic ingestion.
*   **Error Handling Tests:**
    *   **Unsupported File Types:** Attempt to upload unsupported file formats.
    *   **Corrupted Files:** Upload corrupted documents.
    *   **Large Files:** Upload files exceeding the configured size limit.
    *   **Empty Files:** Upload empty files.
    *   **Ingestion Failures:** Simulate failures at different stages (e.g., embedder unavailable, vector store full).

#### 3.2. Query Pipeline (`QueryEngine`, `QueryEnhancer`, `LLMClient`, `VectorStore`, `Reranker`)

**Goal:** Verify that user queries are processed, relevant information is retrieved, and accurate responses are generated.

*   **Functional Tests:**
    *   **Basic Query:** Ask simple questions for which direct answers exist in ingested documents.
    *   **Complex Query:** Ask multi-part questions, questions requiring synthesis from multiple sources.
    *   **Contextual Query:** Test follow-up questions in a conversation (e.g., "What about X?").
    *   **Query Enhancement:** Verify that enhanced queries (expansions, reformulations) improve retrieval for ambiguous queries.
    *   **Reranking Effectiveness:** For queries with many initial results, verify that reranking prioritizes the most relevant ones.
    *   **No Results Found:** Query for information not present in the knowledge base.
    *   **Specific Filters:** Query using metadata filters (e.g., "documents from HR department").
*   **Error Handling Tests:**
    *   **Empty Query:** Submit an empty query.
    *   **LLM Unavailable:** Simulate LLM service downtime.
    *   **Vector Store Empty/Unavailable:** Query when no documents are ingested or the vector store is down.

#### 3.3. Conversational Flow (`ConversationManager`, `ConversationState/Memory`)

**Goal:** Verify the system's ability to maintain context, manage dialogue state, and provide coherent multi-turn responses.

*   **Functional Tests:**
    *   **Start/End Conversation:** Initiate and terminate conversations.
    *   **Multi-turn Dialogue:** Engage in a series of related questions and answers, ensuring context is maintained.
    *   **Clarification:** Test scenarios where the system needs to ask for clarification.
    *   **Memory Recall:** Verify the system remembers facts or preferences mentioned earlier in the conversation.
    *   **Intent Switching:** Test switching between different topics within a single conversation.
*   **Error Handling Tests:**
    *   **Invalid Session ID:** Attempt to interact with a non-existent or expired session.
    *   **Context Loss:** Test if context is lost unexpectedly after a certain number of turns or time.

#### 3.4. System Management & Monitoring (`HeartbeatMonitor`, `ConfigManager`, `DependencyContainer`)

**Goal:** Verify system health, configuration management, and resource allocation.

*   **Functional Tests:**
    *   **Health Check:** Access `/health` and `/health/detailed` endpoints; verify all components report healthy status.
    *   **Configuration Update:** Modify a configuration parameter (e.g., `top_k` for retrieval) and verify the change is applied.
    *   **Resource Monitoring:** Observe CPU, memory, and disk usage under load.
*   **Error Handling Tests:**
    *   **Component Failure:** Simulate a component failure (e.g., stop the vector store) and verify it's reflected in health checks.
    *   **Invalid Configuration:** Attempt to apply invalid configuration values.

### 4. Data Generation with LLM

Testers can use an LLM to generate diverse and challenging test data.

**General Prompting Guidelines:**

*   **Be Specific:** Clearly state the type of data needed.
*   **Specify Format:** Request data in a structured format (e.g., JSON, Markdown table).
*   **Define Constraints:** Mention length, complexity, keywords, or specific scenarios.
*   **Iterate:** Refine prompts based on initial LLM outputs.

**Example Prompts for Test Data Generation:**

*   **For Ingestion (Documents):**
    *   "Generate a 500-word technical document about 'network security protocols' in Markdown format, including sections on firewalls, VPNs, and intrusion detection. Include a small table summarizing common attack types."
    *   "Create a short PDF document (text only) about 'company HR policies on remote work'. Make sure it includes a paragraph about 'flexible hours' and 'equipment reimbursement'."
    *   "Generate an Excel-like dataset (as a CSV string) with 10 rows and 5 columns: 'EmployeeID', 'Name', 'Department', 'Project', 'Manager'. Include diverse department names and project types."
    *   "Generate a JSON object representing a ServiceNow incident ticket. Include fields like 'number', 'short_description', 'description', 'priority', 'category', and 'assigned_to'. Make the description about a 'critical server outage affecting database connectivity'."
*   **For Querying:**
    *   "Given a document about 'cloud computing benefits', generate 5 diverse questions a user might ask, ranging from simple factual to complex comparative questions."
    *   "Generate 3 ambiguous queries that could have multiple interpretations, suitable for testing query enhancement."
    *   "Create a series of 4 conversational turns between a user and an AI about 'troubleshooting a printer issue'. Include a follow-up question."
*   **For Error Handling:**
    *   "Generate a text document that is intentionally corrupted with non-UTF-8 characters."
    *   "Create a very long single-line string (over 10,000 characters) to test chunking limits."

### 5. Testing Tools and Environment

*   **API Testing Tools:** Postman, Insomnia, `curl`, or custom Python scripts for interacting with FastAPI endpoints.
*   **File System Monitoring:** Tools like `inotify-tools` (Linux) or PowerShell scripts (Windows) for observing folder changes.
*   **Database Inspection:** SQLite browser for `feedback_store.db` and `servicenow_cache.db`. Qdrant UI/CLI for vector store inspection.
*   **System Monitoring:** `htop`, `top`, `perfmon` (Windows), `psutil` (Python) for resource usage.
*   **Logging:** Monitor application logs (`logs/rag_system.log`) for errors, warnings, and debug information.
*   **LLM Access:** Ensure access to a configured LLM (e.g., through the `LLMClient` or a separate API key for direct prompting).

---

By following this guide, testers can systematically create and execute test cases that cover the breadth and depth of the RAG system's functionality, ensuring its robustness and reliability.
