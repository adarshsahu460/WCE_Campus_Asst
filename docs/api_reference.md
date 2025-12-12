# API Reference

## Overview

The WCE Campus Assistant provides a RESTful API for chat interactions, document upload, and RAG queries.

**Base URLs:**
- Backend API: `http://localhost:8001`
- MCP Server: `http://localhost:8002`

---

## Authentication

Currently, the API does not require authentication. In production, implement:
- API key authentication
- JWT tokens
- OAuth 2.0

---

## Backend API Endpoints

### Health Check

#### `GET /health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /ready`

Check if the API is ready to serve requests (all dependencies initialized).

**Response:**
```json
{
  "status": "ready",
  "chromadb": "connected",
  "mcp_server": "connected"
}
```

---

### Chat

#### `POST /chat`

Send a message and receive an AI-generated response.

**Request Body:**
```json
{
  "message": "What classes do I have today?",
  "session_id": "user-123-session-456",
  "context": {
    "class": "TE",
    "division": "A"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's message |
| `session_id` | string | No | Session identifier for context |
| `context` | object | No | Additional context (class, division, etc.) |

**Response:**
```json
{
  "response": "Based on the timetable, you have the following classes today:\n\n- 09:00-10:00: Machine Learning (Room 301)\n- 10:00-11:00: Data Science (Room 302)\n- 11:15-12:15: Cloud Computing (Lab 1)",
  "sources": [
    {
      "title": "TE_A Timetable",
      "path": "/data/timetables/te_a_timetable.csv"
    }
  ],
  "tool_used": "timetable",
  "session_id": "user-123-session-456"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | AI-generated response |
| `sources` | array | Documents used for response |
| `tool_used` | string | MCP tool used (if any) |
| `session_id` | string | Session identifier |

**Error Response:**
```json
{
  "error": "Failed to process message",
  "detail": "Error description"
}
```

---

### RAG Query

#### `POST /rag/query`

Query the RAG system directly without LLM generation.

**Request Body:**
```json
{
  "query": "What is the syllabus for Machine Learning?",
  "top_k": 5,
  "category": "syllabus",
  "score_threshold": 0.35
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `top_k` | integer | No | Number of results (default: 5) |
| `category` | string | No | Filter by category |
| `score_threshold` | float | No | Minimum similarity score |

**Response:**
```json
{
  "results": [
    {
      "content": "Machine Learning Syllabus:\n1. Introduction to ML\n2. Supervised Learning\n3. Unsupervised Learning...",
      "source": "/data/syllabus/ml_syllabus.pdf",
      "score": 0.89,
      "metadata": {
        "category": "syllabus",
        "page": 1
      }
    }
  ],
  "total": 5,
  "query_time_ms": 120
}
```

---

### Document Upload

#### `POST /upload`

Upload a document to be indexed.

**Request:**
- Content-Type: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Document file (PDF, CSV, TXT) |
| `category` | string | Yes | Document category |

**cURL Example:**
```bash
curl -X POST http://localhost:8001/upload \
  -F "file=@syllabus.pdf" \
  -F "category=syllabus"
```

**Response:**
```json
{
  "success": true,
  "filename": "syllabus.pdf",
  "category": "syllabus",
  "path": "/data/syllabus/syllabus.pdf",
  "chunks_created": 15,
  "message": "Document uploaded and indexed successfully"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Unsupported file type",
  "detail": "Only PDF, CSV, and TXT files are supported"
}
```

**Supported File Types:**
- `application/pdf` (.pdf)
- `text/csv` (.csv)
- `text/plain` (.txt)

**Maximum File Size:** 10 MB

---

## MCP Server Endpoints

### List Tools

#### `GET /tools`

List all available MCP tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "timetable",
      "description": "Get class timetable for a specific day",
      "parameters": {
        "type": "object",
        "properties": {
          "class_name": {"type": "string"},
          "division": {"type": "string"},
          "day": {"type": "string"}
        },
        "required": ["class_name"]
      }
    },
    {
      "name": "study_plan",
      "description": "Generate a study plan for upcoming exams",
      "parameters": {...}
    },
    {
      "name": "exam_notify",
      "description": "Get upcoming exam notifications",
      "parameters": {...}
    },
    {
      "name": "file_browser",
      "description": "Browse available documents",
      "parameters": {...}
    }
  ]
}
```

---

### Execute Tool

#### `POST /tools/execute`

Execute an MCP tool.

**Request Body:**
```json
{
  "name": "timetable",
  "arguments": {
    "class_name": "TE",
    "division": "A",
    "day": "today"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tool name |
| `arguments` | object | Yes | Tool parameters |

**Response:**
```json
{
  "success": true,
  "tool": "timetable",
  "data": {
    "class": "TE",
    "division": "A",
    "day": "Monday",
    "schedule": [...]
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Tool not found",
  "tool": "unknown_tool"
}
```

---

### Get Tool Schema

#### `GET /tools/{tool_name}/schema`

Get the JSON schema for a specific tool.

**Response:**
```json
{
  "name": "timetable",
  "description": "Get class timetable for a specific day",
  "parameters": {
    "type": "object",
    "properties": {
      "class_name": {
        "type": "string",
        "description": "The class name (e.g., TE, BE)"
      },
      "division": {
        "type": "string",
        "description": "The division (default: A)"
      },
      "day": {
        "type": "string",
        "description": "Day of week or 'today'/'tomorrow'"
      }
    },
    "required": ["class_name"]
  }
}
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource not found |
| 413 | Payload Too Large - File exceeds limit |
| 415 | Unsupported Media Type - Invalid file type |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Dependency down |

---

## Rate Limiting

In production, implement rate limiting:

| Endpoint | Limit |
|----------|-------|
| `/chat` | 60 requests/minute |
| `/rag/query` | 100 requests/minute |
| `/upload` | 10 requests/minute |
| `/tools/execute` | 60 requests/minute |

---

## WebSocket (Future)

For real-time chat streaming:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/chat');

ws.send(JSON.stringify({
  type: 'message',
  content: 'What are my classes today?',
  session_id: 'user-123'
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'chunk') {
    // Streaming response chunk
    console.log(data.content);
  } else if (data.type === 'done') {
    // Response complete
    console.log('Sources:', data.sources);
  }
};
```

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8001"

# Chat
response = requests.post(
    f"{BASE_URL}/chat",
    json={
        "message": "What classes do I have today?",
        "context": {"class": "TE", "division": "A"}
    }
)
print(response.json()["response"])

# Upload
with open("syllabus.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/upload",
        files={"file": f},
        data={"category": "syllabus"}
    )
print(response.json())
```

### JavaScript/TypeScript

```typescript
const BASE_URL = "http://localhost:8001";

// Chat
const chatResponse = await fetch(`${BASE_URL}/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: "What classes do I have today?",
    context: { class: "TE", division: "A" }
  })
});
const data = await chatResponse.json();
console.log(data.response);

// Upload
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("category", "syllabus");

const uploadResponse = await fetch(`${BASE_URL}/upload`, {
  method: "POST",
  body: formData
});
console.log(await uploadResponse.json());
```

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
- Backend: `http://localhost:8001/docs`
- MCP Server: `http://localhost:8002/docs`

Interactive Swagger UI:
- Backend: `http://localhost:8001/docs`
- MCP Server: `http://localhost:8002/docs`

ReDoc:
- Backend: `http://localhost:8001/redoc`
- MCP Server: `http://localhost:8002/redoc`
