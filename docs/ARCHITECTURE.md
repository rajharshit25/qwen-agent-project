# Architecture
```mermaid
flowchart TD
 U[User / Chrome popup] --> API[FastAPI]
 API --> C[Ollama client]
 C --> O[Ollama runtime] --> Q[Qwen model]
 API --> A[Custom agent engine] --> V[Action schema validation]
 V --> R[Allowlisted tool registry] --> T[Calculator / text parser / page analyzer]
 T --> A
 API --> DB[(SQLite history and document chunks)]
```
The LLM proposes text/actions; Python owns permissions, validation, tool execution, limits and state transitions. Current document retrieval is lexical SQLite search, not vector search.
