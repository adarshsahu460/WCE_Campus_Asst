"""
Retriever Module
Implements document retrieval with context building and optional reranking.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
from dotenv import load_dotenv

from .embeddings import get_default_embeddings, BaseEmbeddings
from .vectordb import get_vector_db, ChromaVectorDB, VectorSearchResult

load_dotenv()


@dataclass
class RetrievalResult:
    """Represents a retrieval result with grouped context."""
    content: str
    source: str
    metadata: Dict[str, Any]
    score: float
    chunk_indices: List[int]


class DocumentRetriever:
    """
    Document retriever with context building and optional reranking.
    Groups chunks from the same document for better context.
    """
    
    def __init__(
        self,
        embeddings: Optional[BaseEmbeddings] = None,
        vector_db: Optional[ChromaVectorDB] = None,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        use_reranker: bool = False
    ):
        """
        Initialize the retriever.
        
        Args:
            embeddings: Embeddings model instance
            vector_db: Vector database instance
            top_k: Number of results to retrieve
            score_threshold: Minimum similarity score
            use_reranker: Whether to use Cohere reranker
        """
        self.embeddings = embeddings or get_default_embeddings()
        self.vector_db = vector_db or get_vector_db()
        self.top_k = top_k or int(os.getenv("RAG_TOP_K", 5))
        self.score_threshold = score_threshold or float(os.getenv("RAG_SCORE_THRESHOLD", 0.35))
        self.use_reranker = use_reranker or os.getenv("USE_RERANKER", "false").lower() == "true"
        
        # Initialize reranker if needed
        self.reranker = None
        if self.use_reranker:
            self._init_reranker()
    
    def _init_reranker(self):
        """Initialize Cohere reranker if API key is available."""
        try:
            import cohere
            cohere_key = os.getenv("COHERE_API_KEY")
            if cohere_key:
                self.reranker = cohere.Client(cohere_key)
                print("✅ Cohere reranker initialized")
            else:
                print("⚠️ COHERE_API_KEY not set, reranking disabled")
                self.use_reranker = False
        except ImportError:
            print("⚠️ cohere package not installed, reranking disabled")
            self.use_reranker = False
    
    def _rerank(
        self,
        query: str,
        results: List[VectorSearchResult],
        top_n: int = 5
    ) -> List[VectorSearchResult]:
        """
        Rerank results using Cohere reranker.
        
        Args:
            query: Original query
            results: Initial search results
            top_n: Number of results after reranking
            
        Returns:
            Reranked results
        """
        if not self.reranker or not results:
            return results
        
        try:
            documents = [r.content for r in results]
            
            rerank_response = self.reranker.rerank(
                model="rerank-english-v2.0",
                query=query,
                documents=documents,
                top_n=top_n
            )
            
            # Reorder results based on reranking
            reranked = []
            for item in rerank_response.results:
                original_result = results[item.index]
                # Update score with reranker score
                original_result.score = item.relevance_score
                reranked.append(original_result)
            
            return reranked
        except Exception as e:
            print(f"⚠️ Reranking failed: {e}")
            return results
    
    def _group_by_source(
        self,
        results: List[VectorSearchResult]
    ) -> Dict[str, List[VectorSearchResult]]:
        """
        Group results by source document.
        
        Args:
            results: List of search results
            
        Returns:
            Dictionary mapping source to results
        """
        grouped = defaultdict(list)
        
        for result in results:
            source = result.metadata.get("source", result.metadata.get("filename", "unknown"))
            grouped[source].append(result)
        
        return dict(grouped)
    
    def _build_context(
        self,
        grouped_results: Dict[str, List[VectorSearchResult]]
    ) -> List[RetrievalResult]:
        """
        Build context by combining chunks from the same document.
        
        Args:
            grouped_results: Results grouped by source
            
        Returns:
            List of RetrievalResult with combined context
        """
        retrieval_results = []
        
        for source, results in grouped_results.items():
            # Sort by chunk index if available
            results.sort(key=lambda r: r.metadata.get("chunk_index", 0))
            
            # Combine content from chunks
            combined_content = "\n\n".join([r.content for r in results])
            
            # Calculate average score
            avg_score = sum(r.score for r in results) / len(results)
            
            # Collect chunk indices
            chunk_indices = [r.metadata.get("chunk_index", 0) for r in results]
            
            # Use first result's metadata as base
            base_metadata = results[0].metadata.copy()
            base_metadata["num_chunks"] = len(results)
            
            retrieval_results.append(RetrievalResult(
                content=combined_content,
                source=source,
                metadata=base_metadata,
                score=avg_score,
                chunk_indices=chunk_indices
            ))
        
        # Sort by score
        retrieval_results.sort(key=lambda r: r.score, reverse=True)
        
        return retrieval_results
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        group_by_source: bool = True
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results (overrides default)
            filter_metadata: Optional metadata filter
            group_by_source: Whether to group chunks by source
            
        Returns:
            List of RetrievalResult objects
        """
        top_k = top_k or self.top_k
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_text(query)
        
        # Search vector database (get more results for grouping/reranking)
        search_top_k = top_k * 3 if group_by_source or self.use_reranker else top_k
        
        results = self.vector_db.search(
            query_embedding=query_embedding,
            top_k=search_top_k,
            score_threshold=self.score_threshold,
            filter_metadata=filter_metadata
        )
        
        if not results:
            return []
        
        # Apply reranking if enabled
        if self.use_reranker:
            results = self._rerank(query, results, top_k * 2)
        
        # Group by source if enabled
        if group_by_source:
            grouped = self._group_by_source(results)
            retrieval_results = self._build_context(grouped)
            return retrieval_results[:top_k]
        
        # Return individual results
        return [
            RetrievalResult(
                content=r.content,
                source=r.metadata.get("source", "unknown"),
                metadata=r.metadata,
                score=r.score,
                chunk_indices=[r.metadata.get("chunk_index", 0)]
            )
            for r in results[:top_k]
        ]
    
    def retrieve_with_sources(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve documents with formatted source citations.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            Dict with context and sources
        """
        results = self.retrieve(query, top_k)
        
        if not results:
            return {
                "context": "",
                "sources": [],
                "num_results": 0
            }
        
        # Build context string
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


# Singleton instance
_retriever: Optional[DocumentRetriever] = None


def get_retriever() -> DocumentRetriever:
    """Get or create singleton retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = DocumentRetriever()
    return _retriever
