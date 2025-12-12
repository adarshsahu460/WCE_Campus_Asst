# WCE Campus Assistant - System Architecture

## Overview

The WCE Campus Assistant is a production-ready AI-powered chatbot designed for Walchand College of Engineering. It combines a Retrieval-Augmented Generation (RAG) system with a Model Context Protocol (MCP) server to provide intelligent responses to student queries.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WCE Campus Assistant                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────────────────────────────────────────┐ │
│  │              │     │                  Backend API                      │ │
│  │   Next.js    │────▶│  ┌────────────┐  ┌─────────────┐  ┌───────────┐ │ │
│  │   Frontend   │     │  │   /chat    │  │  /rag/query │  │  /upload  │ │ │
│  │   (Port 3000)│◀────│  └─────┬──────┘  └──────┬──────┘  └─────┬─────┘ │ │
│  │              │     │        │                │                │       │ │
│  └──────────────┘     │        ▼                ▼                ▼       │ │
│                       │  ┌─────────────────────────────────────────────┐ │ │
│                       │  │              RAG Pipeline                    │ │ │
│                       │  │  ┌─────────┐ ┌──────────┐ ┌─────────────┐  │ │ │
│                       │  │  │ Loader  │→│ Splitter │→│ Embeddings  │  │ │ │
│                       │  │  └─────────┘ └──────────┘ └──────┬──────┘  │ │ │
│                       │  │                                   │         │ │ │
│                       │  │  ┌───────────┐  ┌─────────────────▼───────┐│ │ │
│                       │  │  │ Retriever │◀─│      VectorDB           ││ │ │
│                       │  │  └───────────┘  │     (ChromaDB)          ││ │ │
│                       │  │                 └─────────────────────────┘│ │ │
│                       │  └─────────────────────────────────────────────┘ │ │
│                       │                     (Port 8001)                   │ │
│                       └──────────────────────────────────────────────────┘ │
│                                        │                                    │
│                                        │ Tool Calls                         │
│                                        ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          MCP Server (Port 8002)                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────────┐  │   │
│  │  │  Timetable   │ │  Study Plan  │ │ Exam Notify│ │ File Browser │  │   │
│  │  │    Tool      │ │    Tool      │ │    Tool    │ │    Tool      │  │   │
│  │  └──────────────┘ └──────────────┘ └────────────┘ └──────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          ChromaDB (Port 8000)                        │   │
│  │                        Vector Database Storage                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Frontend (Next.js 14)

**Location:** `/frontend/`

**Technology Stack:**
- Next.js 14 with App Router
- React 18
- TailwindCSS 3.4
- TypeScript

**Key Features:**
- Server-side rendering for optimal performance
- Chat interface with markdown rendering
- File upload with drag-and-drop
- Exam reminder sidebar
- Responsive design

**Main Pages:**
- `/` - Home page with quick actions
- `/chat` - Main chat interface

### 2. Backend API (FastAPI)

**Location:** `/backend/api/`

**Technology Stack:**
- FastAPI
- Python 3.11
- Uvicorn ASGI server

**Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ready` | GET | Readiness probe |
| `/chat` | POST | Main chat endpoint |
| `/rag/query` | POST | Direct RAG query |
| `/upload` | POST | Document upload |

### 3. RAG Pipeline

**Location:** `/backend/api/rag/`

**Components:**
- **Loader** (`loader.py`): Loads PDF, CSV, TXT documents
- **Splitter** (`splitter.py`): Recursive text chunking
- **Embeddings** (`embeddings.py`): OpenAI or HuggingFace embeddings
- **VectorDB** (`vectordb.py`): ChromaDB wrapper
- **Retriever** (`retriever.py`): Document retrieval with reranking
- **Pipeline** (`pipeline.py`): Orchestrates all components

**Configuration:**
```python
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 5
SCORE_THRESHOLD = 0.35
```

### 4. MCP Server

**Location:** `/backend/mcp-server/`

**Tools:**
1. **TimetableTool**: Fetch class schedules
2. **StudyPlanTool**: Generate study plans
3. **ExamNotifyTool**: Get exam reminders
4. **FileBrowserTool**: Browse available documents

### 5. ChromaDB

**Port:** 8000

**Purpose:** Vector database for storing document embeddings

## Data Flow

### Chat Request Flow

```
1. User sends message via Frontend
        ↓
2. Request hits /chat endpoint
        ↓
3. Intent detection (tool vs RAG)
        ├── Tool detected → Call MCP Server
        │                          ↓
        │                   Execute tool
        │                          ↓
        │                   Return result
        ↓
4. RAG query (if needed)
        ↓
5. Generate LLM response
        ↓
6. Return to Frontend
```

### Document Upload Flow

```
1. User uploads document
        ↓
2. File saved to /data/{category}/
        ↓
3. Document loaded and parsed
        ↓
4. Text split into chunks
        ↓
5. Embeddings generated
        ↓
6. Stored in ChromaDB
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key for LLM | - |
| `LLM_MODEL` | Groq model name | llama-3.3-70b-versatile |
| `CHROMA_HOST` | ChromaDB host | localhost |
| `CHROMA_PORT` | ChromaDB port | 8000 |
| `EMBEDDING_MODEL` | HuggingFace model name | BAAI/bge-large-en-v1.5 |
| `EMBEDDING_PROVIDER` | Embedding provider | huggingface |
| `MCP_SERVER_URL` | MCP server URL | http://localhost:8002 |
| `DATA_DIR` | Data directory | ./data |

## Deployment

### Docker Compose Services

```yaml
services:
  chromadb:    # Vector database
  backend:     # FastAPI backend
  mcp-server:  # MCP tool server
  frontend:    # Next.js frontend
```

### Ports

| Service | Port |
|---------|------|
| ChromaDB | 8000 |
| Backend | 8001 |
| MCP Server | 8002 |
| Frontend | 3000 |

## Security Considerations

1. **API Keys**: Stored in environment variables, never committed
2. **CORS**: Configured for allowed origins only
3. **File Upload**: Validated file types and size limits
4. **Container Security**: Non-root users in Docker containers

## Monitoring

- Health check endpoints for all services
- Structured logging with timestamps
- Docker healthchecks for container orchestration
