# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Quick start using the shell script
chmod +x run.sh && ./run.sh

# Manual start - from backend directory
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Environment Setup
```bash
# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env to add your ANTHROPIC_API_KEY
```

### Development Tasks
- **Web Interface**: Access at http://localhost:8000
- **API Documentation**: Available at http://localhost:8000/docs
- **Course Documents**: Place in `docs/` directory for automatic loading

## System Architecture

This is a Retrieval-Augmented Generation (RAG) chatbot system with the following key architectural patterns:

### Core Data Flow
User Query → FastAPI → RAG System → AI Generator → Search Tools → Vector Store → ChromaDB

### Component Relationships

**RAG System (`rag_system.py`)** is the central orchestrator that coordinates:
- **Document Processor**: Parses course documents with structured metadata (Course Title/Link/Instructor format)
- **Vector Store**: Manages two ChromaDB collections (course_catalog for metadata, course_content for chunks)
- **AI Generator**: Handles Claude API integration with tool-based search decisions
- **Session Manager**: Maintains conversation context with configurable history limits
- **Tool Manager**: Manages search tools that AI can invoke

### Key Architectural Decisions

**Tool-Based Search**: The AI (Claude) decides when and how to search using structured tools, rather than hardcoded retrieval. The `CourseSearchTool` provides semantic course name matching and lesson filtering.

**Dual Vector Storage**:
- `course_catalog`: Stores course metadata for semantic course name resolution
- `course_content`: Stores text chunks with course/lesson context for content search

**Chunking Strategy**: Text is split using sentence-based chunking with configurable overlap. Course and lesson context is prepended to chunks for better retrieval.

**Session Management**: Conversations maintain limited history (MAX_HISTORY * 2 messages) for context while preventing unbounded memory growth.

### Document Format Expected

Course documents in `docs/` should follow this structure:
```
Course Title: [Course Name]
Course Link: [URL] 
Course Instructor: [Instructor Name]

Lesson 0: Introduction
Lesson Link: [URL]
[Lesson content...]

Lesson 1: Topic Name
Lesson Link: [URL]
[Lesson content...]
```

### Configuration

Key settings in `config.py`:
- `CHUNK_SIZE`: 800 characters (sentence-based chunking)
- `CHUNK_OVERLAP`: 100 characters
- `MAX_RESULTS`: 5 search results returned
- `MAX_HISTORY`: 2 conversation exchanges remembered
- `EMBEDDING_MODEL`: "all-MiniLM-L6-v2" (sentence transformers)
- `ANTHROPIC_MODEL`: "claude-sonnet-4-20250514"

### Data Models

**Course**: Contains title, optional link/instructor, and list of lessons
**Lesson**: Has lesson_number, title, and optional lesson_link
**CourseChunk**: Text chunk with course_title, lesson_number, and chunk_index for vector storage

### Vector Store Search Flow

1. **Course Resolution**: If course name provided, semantic search on course_catalog to find best match
2. **Filter Building**: Create ChromaDB filters for course title and/or lesson number  
3. **Content Search**: Semantic search on course_content collection
4. **Results Formatting**: Include course/lesson context headers and track sources

The system automatically loads all documents from `docs/` directory on startup, avoiding duplicate processing by checking existing course titles in the vector store.
- always use uv to run the server do not use pip directly
- make sure to use uv to manage all dependencies
- use uv to run python files
- don't run the server using ./run.sh I will start it myself