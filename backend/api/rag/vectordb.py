"""
Vector Database Module
ChromaDB integration for document storage and retrieval.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()


@dataclass
class VectorSearchResult:
    """Represents a search result from the vector database."""
    content: str
    metadata: Dict[str, Any]
    score: float
    id: str


class ChromaVectorDB:
    """
    ChromaDB vector database wrapper for document storage and retrieval.
    Supports both local and server modes.
    """
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_directory: Optional[str] = None,
        use_server: bool = False
    ):
        """
        Initialize ChromaDB connection.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory for persistent storage
            use_server: Whether to use ChromaDB server mode
        """
        self.collection_name = collection_name or os.getenv(
            "CHROMA_COLLECTION_NAME", 
            "wce_documents"
        )
        
        # Determine mode (server vs local)
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", 8000))
        
        if use_server or os.getenv("CHROMA_USE_SERVER", "false").lower() == "true":
            # Connect to ChromaDB server
            print(f"📡 Connecting to ChromaDB server at {chroma_host}:{chroma_port}")
            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port
            )
        else:
            # Use local persistent storage
            persist_dir = persist_directory or os.getenv(
                "CHROMA_PERSIST_DIR",
                "./chroma_db"
            )
            print(f"💾 Using local ChromaDB at {persist_dir}")
            self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        print(f"✅ ChromaDB collection '{self.collection_name}' ready")
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector database.
        
        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Default metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        # Ensure metadata values are serializable
        clean_metadatas = []
        for meta in metadatas:
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif isinstance(v, list):
                    clean_meta[k] = str(v)
                else:
                    clean_meta[k] = str(v)
            clean_metadatas.append(clean_meta)
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=clean_metadatas,
            ids=ids
        )
        
        print(f"✅ Added {len(documents)} documents to collection")
        return ids
    
    def search(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            filter_metadata: Optional metadata filter
            
        Returns:
            List of VectorSearchResult objects
        """
        top_k = top_k or int(os.getenv("RAG_TOP_K", 5))
        score_threshold = score_threshold or float(os.getenv("RAG_SCORE_THRESHOLD", 0.35))
        
        # Perform query
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )
        
        # Process results
        search_results = []
        
        if results and results['documents'] and results['documents'][0]:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else [{} for _ in documents]
            distances = results['distances'][0] if results['distances'] else [0.0 for _ in documents]
            ids = results['ids'][0] if results['ids'] else ['' for _ in documents]
            
            for doc, meta, dist, doc_id in zip(documents, metadatas, distances, ids):
                # Convert distance to similarity score (cosine distance to similarity)
                # ChromaDB returns distance, so similarity = 1 - distance for cosine
                score = 1 - dist
                
                # Apply score threshold
                if score >= score_threshold:
                    search_results.append(VectorSearchResult(
                        content=doc,
                        metadata=meta,
                        score=score,
                        id=doc_id
                    ))
        
        return search_results
    
    def delete(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        self.collection.delete(ids=ids)
    
    def clear(self) -> None:
        """Clear all documents from collection."""
        # Get all IDs and delete
        all_data = self.collection.get()
        if all_data['ids']:
            self.collection.delete(ids=all_data['ids'])
        print(f"🗑️ Cleared collection '{self.collection_name}'")
    
    def count(self) -> int:
        """Get total number of documents in collection."""
        return self.collection.count()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all documents in collection."""
        return self.collection.get(include=["documents", "metadatas"])


# Singleton instance
_vector_db: Optional[ChromaVectorDB] = None


def get_vector_db() -> ChromaVectorDB:
    """Get or create singleton vector database instance."""
    global _vector_db
    if _vector_db is None:
        _vector_db = ChromaVectorDB()
    return _vector_db
