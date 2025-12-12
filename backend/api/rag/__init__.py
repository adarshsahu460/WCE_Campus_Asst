"""
RAG Package
Exports all RAG components.
"""

from .loader import DocumentLoader, Document
from .splitter import RecursiveTextSplitter, TextChunk, split_text
from .embeddings import (
    BaseEmbeddings,
    OpenAIEmbeddings,
    HuggingFaceEmbeddings,
    get_embeddings,
    get_default_embeddings
)
from .vectordb import ChromaVectorDB, VectorSearchResult, get_vector_db
from .retriever import DocumentRetriever, RetrievalResult, get_retriever
from .pipeline import RAGPipeline, get_pipeline

__all__ = [
    # Loader
    "DocumentLoader",
    "Document",
    # Splitter
    "RecursiveTextSplitter",
    "TextChunk",
    "split_text",
    # Embeddings
    "BaseEmbeddings",
    "OpenAIEmbeddings",
    "HuggingFaceEmbeddings",
    "get_embeddings",
    "get_default_embeddings",
    # Vector DB
    "ChromaVectorDB",
    "VectorSearchResult",
    "get_vector_db",
    # Retriever
    "DocumentRetriever",
    "RetrievalResult",
    "get_retriever",
    # Pipeline
    "RAGPipeline",
    "get_pipeline"
]
