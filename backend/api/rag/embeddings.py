"""
Embeddings Module
Handles text embedding using HuggingFace models (default) or OpenAI.
Note: Groq doesn't provide embeddings, so we use HuggingFace BGE models.
"""

import os
from typing import List, Optional, Union
from abc import ABC, abstractmethod
import numpy as np
from dotenv import load_dotenv

load_dotenv()


class BaseEmbeddings(ABC):
    """Abstract base class for embedding models."""
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass


class OpenAIEmbeddings(BaseEmbeddings):
    """
    OpenAI embeddings using text-embedding-3-large model.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize OpenAI embeddings.
        
        Args:
            model: Model name (default from env or text-embedding-3-large)
            api_key: OpenAI API key (default from env)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")
        
        self.model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Dimension depends on model
        self._dimensions = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536
        }
    
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        if not texts:
            return []
        
        # Filter empty texts and track their positions
        valid_texts = []
        valid_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)
        
        if not valid_texts:
            return [[0.0] * self.dimension for _ in texts]
        
        # Batch embed valid texts
        response = self.client.embeddings.create(
            model=self.model,
            input=valid_texts
        )
        
        # Create result array with proper ordering
        results = [[0.0] * self.dimension for _ in texts]
        for i, embedding in enumerate(response.data):
            results[valid_indices[i]] = embedding.embedding
        
        return results
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension for current model."""
        return self._dimensions.get(self.model, 3072)


class HuggingFaceEmbeddings(BaseEmbeddings):
    """
    HuggingFace embeddings using sentence-transformers.
    Supports BGE, MiniLM, and other sentence transformer models.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Initialize HuggingFace embeddings.
        
        Args:
            model_name: Model name (default: BAAI/bge-large-en-v1.5)
            device: Device to use (cpu, cuda, mps)
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers package is required. "
                "Install with: pip install sentence-transformers"
            )
        
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", 
            "BAAI/bge-large-en-v1.5"
        )
        
        # Only use HuggingFace if model name indicates it
        if self.model_name.startswith("text-embedding"):
            self.model_name = "BAAI/bge-large-en-v1.5"
        
        self.device = device or self._get_device()
        self.model = SentenceTransformer(self.model_name, device=self.device)
        self._dimension = self.model.get_sentence_embedding_dimension()
    
    def _get_device(self) -> str:
        """Auto-detect best available device."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"
    
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        if not texts:
            return []
        
        # Handle empty texts
        valid_texts = [t if t and t.strip() else " " for t in texts]
        
        embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension


def get_embeddings(model_type: str = "auto") -> BaseEmbeddings:
    """
    Factory function to get appropriate embeddings instance.
    
    Args:
        model_type: "openai", "huggingface", or "auto"
        
    Returns:
        BaseEmbeddings instance
    """
    embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
    provider = os.getenv("EMBEDDING_PROVIDER", "huggingface")
    
    if model_type == "auto":
        # Auto-detect based on provider env var or model name
        if provider == "openai" or embedding_model.startswith("text-embedding"):
            model_type = "openai"
        else:
            model_type = "huggingface"
    
    if model_type == "openai":
        return OpenAIEmbeddings()
    else:
        return HuggingFaceEmbeddings(model_name=embedding_model)


# Default embeddings instance
_default_embeddings: Optional[BaseEmbeddings] = None


def get_default_embeddings() -> BaseEmbeddings:
    """Get or create default embeddings instance."""
    global _default_embeddings
    if _default_embeddings is None:
        _default_embeddings = get_embeddings("auto")
    return _default_embeddings
