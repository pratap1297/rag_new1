# RAG System Flow - Mermaid Diagram (Detailed)

This diagram illustrates the comprehensive data and control flow within the Enterprise RAG System, including key classes and their methods.

```mermaid
graph TD
    subgraph User Interaction
        A[User] -->|1. Query/Upload| B(FastAPI API)
    end

    subgraph API Layer
        B -->|2. Process Request| C{API Endpoints}
        C -->|2.1 Query| D[QueryEngine]
        C -->|2.2 Upload File| E[IngestionEngine]
        C -->|2.3 Conversation| F[ConversationManager]
        C -->|2.4 Management/Monitoring| G[Management/Monitoring Endpoints]
    end

    subgraph Ingestion Pipeline
        E --&gt;|E.ingest_file()| H[Processors]
        H --&gt;|H.process()| I[Chunker]
        I --&gt;|I.chunk_text()| J[Embedder]
        J --&gt;|J.embed_texts()| K[VectorStore]
        K --&gt;|K.add_vectors()| E
        E --&gt;|E.ingest_file()| L[MetadataStore]
        K --&gt;|8. Vector IDs| L
        L --&gt;|9. Metadata| K
        M[FolderMonitor] --&gt;|M._process_changes()| E
    end

    subgraph Query Pipeline
        D --&gt;|D.process_query()| N[QueryEnhancer]
        N --&gt;|N.enhance_query()| J
        J --&gt;|J.embed_texts()| K
        K --&gt;|K.search()| L
        L --&gt;|L.get_metadata_by_vector_id()| D
        K --&gt;|14. Rerank Results (Optional)| O[Reranker]
        O --&gt;|O.rerank()| P[LLMClient]
        P --&gt;|P.generate()| D
        D --&gt;|D._generate_llm_response()| B
    end

    subgraph Conversational Flow
        F --&gt;|F.process_user_message()| D
        D --&gt;|D.process_query()| F
        F --&gt;|F.process_user_message()| P
        P --&gt;|P.generate()| F
        F --&gt;|F.update_state()| Q[ConversationState/Memory]
        Q --&gt;|23. Return Response| B
    end

    subgraph System Management & Monitoring
        G --&gt;|G.get_status()| R[HeartbeatMonitor]
        R --&gt;|R.comprehensive_health_check()| S[Monitoring Dashboard/Logs]
        G --&gt;|G.update_config()| T[ConfigManager]
        T --&gt;|T.get_config()| U[DependencyContainer]
        U --&gt;|U.get()| D, E, F, J, K, L, P, N, O, R
    end

    B --&gt;|B.query()/B.upload_file()| A

    classDef FastAPIAPI fill:#f9f,stroke:#333,stroke-width:2px;
    classDef QueryEngine fill:#bbf,stroke:#333,stroke-width:2px;
    classDef IngestionEngine fill:#bfb,stroke:#333,stroke-width:2px;
    classDef Processors fill:#ffb,stroke:#333,stroke-width:2px;
    classDef Chunker fill:#fbc,stroke:#333,stroke-width:2px;
    classDef Embedder fill:#cbf,stroke:#333,stroke-width:2px;
    classDef VectorStore fill:#ccf,stroke:#333,stroke-width:2px;
    classDef MetadataStore fill:#cfc,stroke:#333,stroke-width:2px;
    classDef FolderMonitor fill:#fcf,stroke:#333,stroke-width:2px;
    classDef QueryEnhancer fill:#fdd,stroke:#333,stroke-width:2px;
    classDef Reranker fill:#dfd,stroke:#333,stroke-width:2px;
    classDef LLMClient fill:#ddf,stroke:#333,stroke-width:2px;
    classDef ConversationManager fill:#fdf,stroke:#333,stroke-width:2px;
    classDef ConversationStateMemory fill:#eee,stroke:#333,stroke-width:2px;
    classDef HeartbeatMonitor fill:#eef,stroke:#333,stroke-width:2px;
    classDef ConfigManager fill:#ffe,stroke:#333,stroke-width:2px;
    classDef DependencyContainer fill:#efe,stroke:#333,stroke-width:2px;

    class B FastAPIAPI
    class D QueryEngine
    class E IngestionEngine
    class H Processors
    class I Chunker
    class J Embedder
    class K VectorStore
    class L MetadataStore
    class M FolderMonitor
    class N QueryEnhancer
    class O Reranker
    class P LLMClient
    class F ConversationManager
    class Q ConversationStateMemory
    class R HeartbeatMonitor
    class T ConfigManager
    class U DependencyContainer

    subgraph Classes and Methods
        class B {
            FastAPI API
            + create_api_app()
            + query()
            + upload_file()
            + handle_conversation()
        }
        class D {
            QueryEngine
            + process_query()
            + _generate_llm_response()
            + _format_sources()
        }
        class E {
            IngestionEngine
            + ingest_file()
            + ingest_text()
            + _extract_text()
            + _handle_existing_file()
        }
        class H {
            Processors
            + can_process()
            + process()
        }
        class I {
            Chunker
            + chunk_text()
            + _clean_text()
        }
        class J {
            Embedder
            + embed_texts()
            + embed_text()
        }
        class K {
            VectorStore
            + add_vectors()
            + search()
            + delete_vectors()
        }
        class L {
            MetadataStore
            + add_file_metadata()
            + add_chunk_metadata()
            + get_metadata_by_vector_id()
        }
        class M {
            FolderMonitor
            + start_monitoring()
            + _scan_folder()
            + _process_changes()
        }
        class N {
            QueryEnhancer
            + enhance_query()
            + _detect_intent()
            + _expand_query()
        }
        class O {
            Reranker
            + rerank()
        }
        class P {
            LLMClient
            + generate()
        }
        class F {
            ConversationManager
            + start_conversation()
            + process_user_message()
            + get_conversation_history()
        }
        class Q {
            ConversationState/Memory
            + update_state()
            + get_state()
        }
        class R {
            HeartbeatMonitor
            + comprehensive_health_check()
        }
        class T {
            ConfigManager
            + get_config()
            + update_config()
        }
        class U {
            DependencyContainer
            + get()
            + register()
        }
    end
```
