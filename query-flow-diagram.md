# User Query Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 1. User Input (script.js:45-96)                                        │   │
│  │    • User types query & presses Enter/clicks Send                      │   │
│  │    • sendMessage() triggered                                           │   │
│  │    • Input disabled, loading animation shown                           │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                           │
│                                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 2. HTTP Request (script.js:63-72)                                      │   │
│  │    POST /api/query                                                      │   │
│  │    {                                                                    │   │
│  │      "query": "user question",                                          │   │
│  │      "session_id": "uuid-or-null"                                       │   │
│  │    }                                                                    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  BACKEND                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 3. FastAPI Endpoint (app.py:56-74)                                     │   │
│  │    • /api/query receives POST                                           │   │
│  │    • Create session if needed                                           │   │
│  │    • Call rag_system.query()                                           │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                           │
│                                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 4. RAG System (rag_system.py:102-140)                                  │   │
│  │    • Format prompt: "Answer this question about course materials..."   │   │
│  │    • Get conversation history from session_manager                     │   │
│  │    • Call ai_generator.generate_response()                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                           │
│                                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 5. AI Generator (ai_generator.py:43-87)                                │   │
│  │    • Build system prompt + conversation context                        │   │
│  │    • Create Anthropic API call with tools                              │   │
│  │    • Send to Claude API                                                 │   │
│  │    • If tool_use needed → handle_tool_execution()                      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                           │
│                                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 6. Tool Execution (ai_generator.py:89-135)                             │   │
│  │    • Parse Claude's tool use requests                                  │   │
│  │    • Call tool_manager.execute_tool()                                  │   │
│  │    • Collect tool results                                              │   │
│  │    • Final API call to Claude with results                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                           │
│                                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 7. Search Tool (search_tools.py:52-86)                                 │   │
│  │    • Execute vector_store.search()                                     │   │
│  │    • Handle course name & lesson filters                               │   │
│  │    • Format results with context                                       │   │
│  │    • Store sources in last_sources                                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                           │
│                                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 8. Vector Store (vector_store.py:61-100)                               │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐    │   │
│  │  │ Course          │  │ Filter           │  │ Content Search     │    │   │
│  │  │ Resolution      │  │ Building         │  │                    │    │   │
│  │  │                 │  │                  │  │                    │    │   │
│  │  │ • Semantic      │  │ • Course title   │  │ • Query course     │    │   │
│  │  │   search on     │  │   filter         │  │   content          │    │   │
│  │  │   catalog       │  │ • Lesson number  │  │   collection       │    │   │
│  │  │ • Find best     │  │   filter         │  │ • Return results   │    │   │
│  │  │   course match  │  │ • ChromaDB       │  │   with metadata    │    │   │
│  │  │                 │  │   where clause   │  │                    │    │   │
│  │  └─────────────────┘  └──────────────────┘  └────────────────────┘    │   │
│  │                                                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │                     ChromaDB Collections                        │   │   │
│  │  │                                                                 │   │   │
│  │  │  course_catalog: Course metadata (titles, instructors)         │   │   │
│  │  │  course_content: Chunked course material with embeddings       │   │   │
│  │  │                                                                 │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                           │
│                                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 9. Response Assembly (rag_system.py:129-140)                           │   │
│  │    • Get sources from tool_manager                                     │   │
│  │    • Update conversation history                                       │   │
│  │    • Reset sources                                                     │   │
│  │    • Return (response_text, sources_list)                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                           │
│                                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 10. API Response (app.py:68-72)                                        │   │
│  │     {                                                                   │   │
│  │       "answer": "AI generated response",                               │   │
│  │       "sources": ["Course 1 - Lesson 2"],                              │   │
│  │       "session_id": "uuid-string"                                       │   │
│  │     }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 FRONTEND                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 11. Response Handling (script.js:76-85)                                │   │
│  │     • Receive JSON response                                             │   │
│  │     • Update session ID                                                 │   │
│  │     • Remove loading animation                                          │   │
│  │     • Call addMessage() with response & sources                        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                           │
│                                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 12. UI Rendering (script.js:113-138)                                   │   │
│  │     • Convert markdown to HTML                                          │   │
│  │     • Create collapsible sources section                               │   │
│  │     • Append to chat messages                                           │   │
│  │     • Auto-scroll to bottom                                             │   │
│  │     • Re-enable input                                                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════
                               KEY DATA FLOWS
═══════════════════════════════════════════════════════════════════════════════════

Text Processing Pipeline:
User Query → Embeddings → Semantic Search → Retrieved Context → AI Response

Session Management:
session_id tracks conversation across requests for context-aware responses

Tool-Based Search:
Claude AI decides when to search and with what parameters, not hardcoded retrieval

Vector Storage:
- course_catalog: Searchable course metadata 
- course_content: Chunked course material with embeddings
- Semantic matching for both course resolution and content retrieval
```