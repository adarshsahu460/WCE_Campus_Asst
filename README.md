# WCE Campus Assistant

A production-ready AI-powered Campus Assistant Chatbot for Walchand College of Engineering (WCE). The system combines a Retrieval-Augmented Generation (RAG) pipeline with a Model Context Protocol (MCP) server to provide intelligent responses to student queries about timetables, exams, syllabi, and more.

## 🚀 Features

- **RAG-Powered Responses**: Answers questions based on college documents (syllabi, notices, regulations)
- **MCP Tools**: Four specialized tools for common student queries
  - 📅 **Timetable Tool**: Get class schedules for any day
  - 📚 **Study Plan Tool**: Generate personalized study schedules
  - 🔔 **Exam Notify Tool**: Get upcoming exam reminders
  - 📁 **File Browser Tool**: Browse available documents
- **Document Upload**: Upload and index new documents on the fly
- **Modern UI**: Clean, responsive chat interface with markdown support

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI    │────▶│  ChromaDB   │
│   Frontend  │     │   Backend    │     │  VectorDB   │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  MCP Server  │
                    │  (4 Tools)   │
                    └──────────────┘
```

## 📋 Prerequisites

- Docker & Docker Compose
- Groq API key (for LLM chat - get free at https://console.groq.com)
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/wce-assistant.git
   cd wce-assistant
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Groq API key
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Seed the database**
   ```bash
   docker-compose exec backend python -m api.rag.seed
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001/docs
   - MCP Server: http://localhost:8002/docs

### Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start ChromaDB (in separate terminal)
docker run -p 8000:8000 chromadb/chroma

# Start backend API
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

# Start MCP server (in separate terminal)
cd mcp-server
uvicorn server:app --host 0.0.0.0 --port 8002 --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📁 Project Structure

```
wce-assistant/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   ├── rag/
│   │   │   ├── loader.py        # Document loader
│   │   │   ├── splitter.py      # Text splitter
│   │   │   ├── embeddings.py    # Embedding models
│   │   │   ├── vectordb.py      # ChromaDB wrapper
│   │   │   ├── retriever.py     # Document retriever
│   │   │   ├── pipeline.py      # RAG orchestration
│   │   │   └── seed.py          # Database seeding
│   │   └── routes/
│   │       ├── chat.py          # Chat endpoint
│   │       └── upload.py        # Upload endpoint
│   ├── mcp-server/
│   │   ├── server.py            # MCP server
│   │   └── tools/               # MCP tools
│   ├── tests/                   # Unit tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Home page
│   │   ├── chat/page.tsx        # Chat page
│   │   ├── components/          # React components
│   │   └── api/chat/route.ts    # API proxy
│   ├── package.json
│   └── Dockerfile
├── data/                        # Document storage
│   ├── syllabus/
│   ├── notices/
│   ├── regulations/
│   ├── timetables/
│   └── exams/
├── docs/                        # Documentation
│   ├── architecture.md
│   ├── mcptools.md
│   ├── rag_pipeline.md
│   └── api_reference.md
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key for LLM | Required |
| `LLM_MODEL` | Groq model name | llama-3.3-70b-versatile |
| `CHROMA_HOST` | ChromaDB host | localhost |
| `CHROMA_PORT` | ChromaDB port | 8000 |
| `EMBEDDING_MODEL` | HuggingFace embedding model | BAAI/bge-large-en-v1.5 |
| `MCP_SERVER_URL` | MCP server URL | http://localhost:8002 |
| `DATA_DIR` | Data directory | ./data |

### RAG Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| Chunk Size | 1000 | Characters per chunk |
| Chunk Overlap | 200 | Overlap between chunks |
| Top K | 5 | Retrieved documents |
| Score Threshold | 0.35 | Minimum similarity |

## 📚 API Reference

### Chat Endpoint

```bash
POST /chat
Content-Type: application/json

{
  "message": "What classes do I have today?",
  "context": {
    "class": "TE",
    "division": "A"
  }
}
```

### Upload Endpoint

```bash
POST /upload
Content-Type: multipart/form-data

file: <document>
category: syllabus
```

### RAG Query

```bash
POST /rag/query
Content-Type: application/json

{
  "query": "Machine Learning syllabus",
  "top_k": 5
}
```

See [API Reference](docs/api_reference.md) for complete documentation.

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_rag.py -v
```

## 📖 Example Queries

| Query | Tool/RAG |
|-------|----------|
| "What classes do I have today?" | Timetable Tool |
| "Show me the ML syllabus" | RAG |
| "Create a study plan for my exams" | Study Plan Tool |
| "When is my next exam?" | Exam Notify Tool |
| "What documents are available?" | File Browser Tool |
| "What are the attendance rules?" | RAG |

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Rebuild containers
docker-compose build

# Stop all services
docker-compose down

# Remove volumes (reset data)
docker-compose down -v
```

## 📊 Monitoring

- Health check: `GET /health`
- Readiness: `GET /ready`
- API docs: `http://localhost:8001/docs`
- MCP docs: `http://localhost:8002/docs`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Walchand College of Engineering for the use case
- Groq for fast LLM inference
- HuggingFace for embedding models
- ChromaDB for vector storage
- FastAPI and Next.js communities

---

Built with ❤️ for WCE students
