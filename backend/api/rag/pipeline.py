"""
RAG Pipeline Module
Complete RAG pipeline integrating all components.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from .loader import DocumentLoader, Document
from .splitter import RecursiveTextSplitter, TextChunk
from .embeddings import get_embeddings, BaseEmbeddings
from .vectordb import ChromaVectorDB, get_vector_db
from .retriever import DocumentRetriever, get_retriever, RetrievalResult

load_dotenv()


class RAGPipeline:
    """
    Complete RAG pipeline for document processing and retrieval.
    Integrates document loading, splitting, embedding, and retrieval.
    """
    
    def __init__(self):
        """Initialize RAG pipeline components."""
        self.loader = DocumentLoader()
        self.splitter = RecursiveTextSplitter()
        self.embeddings: Optional[BaseEmbeddings] = None
        self.vector_db: Optional[ChromaVectorDB] = None
        self.retriever: Optional[DocumentRetriever] = None
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize all RAG components.
        Called during application startup.
        """
        if self._initialized:
            return
        
        print("🔄 Initializing RAG Pipeline...")
        
        # Initialize embeddings
        print("  📊 Loading embedding model...")
        self.embeddings = get_embeddings("auto")
        
        # Initialize vector database
        print("  💾 Connecting to vector database...")
        self.vector_db = get_vector_db()
        
        # Initialize retriever
        print("  🔍 Setting up retriever...")
        self.retriever = DocumentRetriever(
            embeddings=self.embeddings,
            vector_db=self.vector_db
        )
        
        self._initialized = True
        print("✅ RAG Pipeline initialized!")
    
    def load_and_index_documents(self, directory: Optional[str] = None) -> int:
        """
        Load documents from directory and index them.
        
        Args:
            directory: Optional specific directory to load from
            
        Returns:
            Number of chunks indexed
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")
        
        # Load documents
        if directory:
            documents = self.loader.load_directory(directory)
        else:
            documents = self.loader.load_all_data()
        
        if not documents:
            print("⚠️ No documents found to index")
            return 0
        
        # Split into chunks
        print(f"\n📝 Splitting {len(documents)} documents into chunks...")
        all_chunks = []
        
        for doc in documents:
            chunks = self.splitter.split_text(doc.content, doc.metadata)
            all_chunks.extend(chunks)
        
        print(f"   Created {len(all_chunks)} chunks")
        
        # Generate embeddings
        print("\n📊 Generating embeddings...")
        chunk_texts = [chunk.content for chunk in all_chunks]
        embeddings = self.embeddings.embed_texts(chunk_texts)
        
        # Prepare metadata
        metadatas = [chunk.metadata for chunk in all_chunks]
        
        # Index in vector database
        print("\n💾 Indexing in vector database...")
        self.vector_db.add_documents(
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        print(f"\n✅ Indexed {len(all_chunks)} chunks successfully!")
        return len(all_chunks)
    
    def index_single_document(self, file_path: str) -> int:
        """
        Index a single document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Number of chunks indexed
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")
        
        # Load document
        document = self.loader.load_file(file_path)
        
        # Split into chunks
        chunks = self.splitter.split_text(document.content, document.metadata)
        
        if not chunks:
            return 0
        
        # Generate embeddings
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embeddings.embed_texts(chunk_texts)
        
        # Prepare metadata
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Index in vector database
        self.vector_db.add_documents(
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        return len(chunks)
    
    def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG pipeline.
        
        Args:
            query: User query
            top_k: Number of results
            filter_category: Optional category filter
            
        Returns:
            Dict with context and sources
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")
        
        filter_metadata = None
        if filter_category:
            filter_metadata = {"category": filter_category}
        
        results = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        if not results:
            return {
                "context": "",
                "sources": [],
                "num_results": 0
            }
        
        # Build response
        context_parts = []
        sources = []
        
        for i, result in enumerate(results):
            context_parts.append(f"[Source {i+1}]\n{result.content}")
            sources.append({
                "index": i + 1,
                "source": result.source,
                "category": result.metadata.get("category", "unknown"),
                "score": round(result.score, 4),
                "filename": result.metadata.get("filename", "unknown")
            })
        
        return {
            "context": "\n\n---\n\n".join(context_parts),
            "sources": sources,
            "num_results": len(results)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "document_count": self.vector_db.count(),
            "embedding_model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
            "top_k": int(os.getenv("RAG_TOP_K", 5)),
            "score_threshold": float(os.getenv("RAG_SCORE_THRESHOLD", 0.35))
        }
    
    def clear_index(self):
        """Clear all indexed documents."""
        if self.vector_db:
            self.vector_db.clear()


# Global pipeline instance
_pipeline: Optional[RAGPipeline] = None


def get_pipeline() -> RAGPipeline:
    """Get or create pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
