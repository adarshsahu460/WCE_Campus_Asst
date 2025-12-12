# RAG Pipeline Documentation

## Overview

The Retrieval-Augmented Generation (RAG) pipeline enables the WCE Campus Assistant to answer questions based on college documents. It combines document retrieval with LLM generation for accurate, contextual responses.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG Pipeline                              │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌────────────┐    ┌─────────┐ │
│  │ Document │───▶│  Text    │───▶│ Embedding  │───▶│ Vector  │ │
│  │  Loader  │    │ Splitter │    │ Generator  │    │   DB    │ │
│  └──────────┘    └──────────┘    └────────────┘    └────┬────┘ │
│                                                          │      │
│                                                          ▼      │
│  ┌──────────┐    ┌──────────┐    ┌────────────┐    ┌─────────┐ │
│  │   LLM    │◀───│ Context  │◀───│  Retriever │◀───│  Query  │ │
│  │ Response │    │ Builder  │    │            │    │Embedding│ │
│  └──────────┘    └──────────┘    └────────────┘    └─────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Document Loader (`loader.py`)

Handles loading and parsing various document formats.

**Supported Formats:**
| Format | Library | Notes |
|--------|---------|-------|
| PDF | PyMuPDF (fitz) | Primary; fallback to PyPDF2 |
| CSV | pandas | Converts rows to text |
| TXT | Built-in | Direct text reading |

**Usage:**
```python
from api.rag.loader import DocumentLoader

loader = DocumentLoader()
documents = await loader.load("/data/syllabus/")
# Returns: List[Document]
```

**Document Structure:**
```python
@dataclass
class Document:
    content: str          # Text content
    metadata: dict        # Source, page, category, etc.
    doc_id: str           # Unique identifier
```

### 2. Text Splitter (`splitter.py`)

Splits documents into chunks for optimal retrieval.

**Configuration:**
```python
CHUNK_SIZE = 1000        # Characters per chunk
CHUNK_OVERLAP = 200      # Overlap between chunks
```

**Algorithm: Recursive Character Splitting**

1. Try splitting by `\n\n` (paragraphs)
2. If chunks too large, split by `\n` (lines)
3. If still too large, split by `. ` (sentences)
4. Finally, split by space (words)

**Usage:**
```python
from api.rag.splitter import RecursiveTextSplitter

splitter = RecursiveTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(documents)
```

### 3. Embeddings (`embeddings.py`)

Generates vector embeddings for text chunks.

**Supported Models:**

| Provider | Model | Dimensions | Notes |
|----------|-------|------------|-------|
| HuggingFace | BAAI/bge-large-en-v1.5 | 1024 | Default, open source |
| HuggingFace | BAAI/bge-base-en-v1.5 | 768 | Faster, smaller |
| HuggingFace | sentence-transformers/all-MiniLM-L6-v2 | 384 | Lightweight |

**Note:** Groq is used for LLM chat but doesn't provide embeddings, so we use HuggingFace models.

**Usage:**
```python
from api.rag.embeddings import get_embeddings

embeddings = get_embeddings(provider="huggingface")
vectors = await embeddings.embed_documents(["text1", "text2"])
query_vector = await embeddings.embed_query("search query")
```

### 4. Vector Database (`vectordb.py`)

Stores and queries document embeddings using ChromaDB.

**Features:**
- Persistent storage
- Similarity search
- Metadata filtering
- Collection management

**Usage:**
```python
from api.rag.vectordb import ChromaVectorDB

db = ChromaVectorDB(
    host="localhost",
    port=8000,
    collection_name="wce_documents"
)

# Add documents
await db.add_documents(chunks, embeddings)

# Search
results = await db.search(query_embedding, top_k=5)
```

### 5. Retriever (`retriever.py`)

Retrieves relevant documents for a query.

**Configuration:**
```python
TOP_K = 5                    # Number of results
SCORE_THRESHOLD = 0.35       # Minimum similarity score
```

**Features:**
- Similarity-based retrieval
- Score thresholding
- Source grouping
- Optional reranking (Cohere)

**Usage:**
```python
from api.rag.retriever import DocumentRetriever

retriever = DocumentRetriever(
    vector_db=db,
    embeddings=embeddings,
    top_k=5,
    score_threshold=0.35
)

results = await retriever.retrieve("What is the ML syllabus?")
```

### 6. Pipeline (`pipeline.py`)

Orchestrates all components into a unified interface.

**Usage:**
```python
from api.rag.pipeline import RAGPipeline

pipeline = RAGPipeline()
await pipeline.initialize()

# Index documents
await pipeline.index_documents("/data/syllabus/")

# Query
response = await pipeline.query("What topics are in ML?")
```

---

## Configuration

### Environment Variables

```bash
# LLM (Groq)
GROQ_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile

# Embeddings (HuggingFace - Groq doesn't provide embeddings)
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_PROVIDER=huggingface

# Vector Database
CHROMA_HOST=localhost
CHROMA_PORT=8000
COLLECTION_NAME=wce_documents

# Retrieval
RAG_TOP_K=5
RAG_SCORE_THRESHOLD=0.35

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Tuning Parameters

| Parameter | Impact | Recommended Range |
|-----------|--------|-------------------|
| `chunk_size` | Larger = more context, less precision | 500-1500 |
| `chunk_overlap` | Higher = better continuity | 10-30% of chunk_size |
| `top_k` | More results = broader context | 3-10 |
| `score_threshold` | Higher = more relevant, fewer results | 0.3-0.5 |

---

## Document Categories

The system organizes documents into categories:

```
/data/
├── syllabus/          # Course syllabi
├── notices/           # Official announcements
├── regulations/       # Academic rules
├── timetables/        # Class schedules
└── exams/             # Exam schedules
```

Each category has metadata attached during indexing:

```python
metadata = {
    "source": "file_path",
    "category": "syllabus",
    "department": "computer_engineering",
    "year": "TE",
    "indexed_at": "2024-01-15T10:30:00"
}
```

---

## Indexing Workflow

### 1. Initial Seeding

```bash
# Run seed script
python -m api.rag.seed
```

This:
- Generates sample documents
- Loads all documents from `/data/`
- Splits into chunks
- Generates embeddings
- Stores in ChromaDB

### 2. Incremental Updates

Via the `/upload` endpoint:

1. File uploaded
2. Saved to appropriate category folder
3. Document loaded and parsed
4. Chunks created
5. Embeddings generated
6. Added to vector database

### 3. Full Reindex

```python
from api.rag.pipeline import RAGPipeline

pipeline = RAGPipeline()
await pipeline.initialize()

# Clear existing
await pipeline.clear()

# Reindex all
await pipeline.index_documents("/data/")
```

---

## Query Processing

### Query Flow

```
1. Receive query text
        ↓
2. Generate query embedding
        ↓
3. Search vector database
        ↓
4. Filter by score threshold
        ↓
5. Group by source
        ↓
6. (Optional) Rerank results
        ↓
7. Build context string
        ↓
8. Return with sources
```

### Context Building

```python
def build_context(results: List[SearchResult]) -> str:
    context_parts = []
    for result in results:
        context_parts.append(
            f"[Source: {result.source}]\n{result.content}"
        )
    return "\n\n---\n\n".join(context_parts)
```

---

## Evaluation

### Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Recall@K** | Relevant docs in top K | > 0.8 |
| **MRR** | Mean Reciprocal Rank | > 0.7 |
| **Latency** | Query response time | < 500ms |

### Evaluation Script

```python
# Run evaluation
python -m api.rag.evaluate

# Output:
# Recall@5: 0.85
# MRR: 0.72
# Avg Latency: 320ms
```

---

## Troubleshooting

### Common Issues

**1. Low retrieval quality**
- Check chunk size (too large = irrelevant content)
- Lower score threshold
- Increase top_k

**2. Missing context**
- Ensure documents are indexed
- Check category metadata
- Verify ChromaDB connection

**3. Slow queries**
- Check embedding model
- Verify ChromaDB is running
- Consider batch processing

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("api.rag").setLevel(logging.DEBUG)

# Query with debug info
results = await retriever.retrieve("query", debug=True)
# Returns scores, sources, timing
```

---

## Best Practices

### Document Preparation

1. **Clean text**: Remove headers/footers from PDFs
2. **Consistent format**: Use standard naming conventions
3. **Metadata**: Include year, department, subject info
4. **Update regularly**: Reindex when documents change

### Query Optimization

1. **Clear queries**: Encourage specific questions
2. **Context window**: Keep total context under 4000 tokens
3. **Source diversity**: Balance results from different sources

### Performance

1. **Batch indexing**: Index multiple documents together
2. **Persistent storage**: Use ChromaDB persistence
3. **Caching**: Cache frequent query embeddings
