# GEMINI.md - Project Guidelines for AI Agent

This document outlines the conventions, tools, and workflows for the Gemini AI agent when interacting with this project. Adhering to these guidelines ensures consistency, maintainability, and efficient collaboration.

## 1. Project Overview

This project is an Enterprise RAG (Retrieval-Augmented Generation) System with a Python backend (FastAPI, various AI/ML libraries) and a React/TypeScript frontend. It also includes a dedicated ServiceNow integration module and a data generation tool.

## 2. Core Mandates for Gemini

### 2.1. Conventions

*   **Language:** Primary backend language is Python. Frontend is React/TypeScript.
*   **Naming:** Adhere to existing naming conventions (e.g., `snake_case` for Python variables/functions, `PascalCase` for Python classes, `camelCase` for JavaScript variables/functions, `PascalCase` for React components).
*   **Code Style:** Follow `black` formatting for Python code and `ESLint` rules for TypeScript/JavaScript.
*   **Project Structure:** Respect the existing modular structure, especially within `rag_system/src/` and `ServiceNow-Int/`.

### 2.2. Libraries and Frameworks

*   **Python:**
    *   **Web Framework:** FastAPI, Uvicorn.
    *   **Data Validation:** Pydantic.
    *   **AI/ML:** `sentence-transformers`, `cohere`, `faiss-cpu`, `groq`, `openai`, `langgraph`, `langchain`, `langchain-core`, `langchain-community`.
    *   **Document Processing:** `PyPDF2`, `python-docx`, `python-magic`, `openpyxl`, `xlrd`.
    *   **Cloud Integrations:** `azure-cognitiveservices-vision-computervision`, `azure-ai-documentintelligence`, `azure-ai-inference`, `msrest`, `azure-core`.
    *   **Utilities:** `python-dotenv`, `requests`, `aiofiles`, `psutil`, `portalocker`, `APScheduler`, `schedule`, `python-jose[cryptography]`, `prometheus-client`.
    *   **UI (Backend-driven):** `gradio`.
*   **Frontend (Node.js/React):**
    *   **Framework:** React.
    *   **Build Tool:** Vite.
    *   **Language:** TypeScript.
    *   **Styling:** Tailwind CSS, clsx, tailwind-merge.
    *   **UI Libraries:** @radix-ui/react-*, lucide-react.
    *   **Routing:** react-router-dom.
    *   **Markdown:** react-markdown, remark-gfm.
    *   **HTTP Client:** axios.

*   **Verification:** Before introducing new libraries, check `requirements.txt` (for Python) and `package.json` (for Node.js) to confirm existing usage. If a new dependency is required, propose adding it to the relevant `requirements.txt` or `package.json` file.

### 2.3. Idiomatic Changes

*   When modifying existing code, analyze the surrounding code to match its style, error handling patterns, and data flow. For example, if a Python module uses type hints extensively, continue to use them in your modifications.
*   For frontend changes, ensure new components or modifications align with the existing React component structure and styling approach.

## 3. Development Workflows

### 3.1. Running Tests

*   **Python Tests:** The primary test runner is `pytest`. To run all Python tests, navigate to the project root and execute:
    ```bash
    pepenv/Scripts/pytest # On Windows
    # or
    source pepenv/bin/activate && pytest # On macOS/Linux
    ```
    Specific test files or directories can be run by providing their paths (e.g., `pytest rag_system/tests/integration/test_excel_ingestion.py`).

### 3.2. Running Build, Lint, and Type-Checking Commands

*   **Python:**
    *   **Linting (flake8):**
        ```bash
        pepenv/Scripts/flake8 . # On Windows
        # or
        source pepenv/bin/activate && flake8 . # On macOS/Linux
        ```
    *   **Formatting (black):**
        ```bash
        pepenv/Scripts/black . # On Windows
        # or
        source pepenv/bin/activate && black . # On macOS/Linux
        ```
    *   **Type Checking (mypy):**
        ```bash
        pepenv/Scripts/mypy . # On Windows
        # or
        source pepenv/bin/activate && mypy . # On macOS/Linux
        ```

*   **Frontend:**
    *   **Build:**
        ```bash
        cd frontend
        npm run build
        ```
    *   **Linting:**
        ```bash
        cd frontend
        npm run lint
        ```
    *   **Type Checking:** This is typically part of the `npm run build` process (via `tsc`).

## 4. Project-Specific Notes

*   **Virtual Environment:** Always ensure the `pepenv` virtual environment is activated before running Python commands.
*   **Environment Variables:** Critical configuration is managed via `.env` files. Ensure all necessary environment variables are set for the specific task (e.g., API keys for LLMs, database credentials).
*   **ServiceNow Integration:** Be mindful of the `ServiceNow-Int` module's specific requirements and API interactions when making changes related to ServiceNow.
*   **Data Directories:** The `data/` directory is used for persistent storage (e.g., vector stores, feedback). Avoid directly modifying its contents unless explicitly instructed or part of a data migration task.
