"""
Text Splitter Module
Implements recursive text splitting for optimal chunking.
"""

import os
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    metadata: dict
    chunk_index: int
    start_char: int
    end_char: int


class RecursiveTextSplitter:
    """
    Recursive text splitter that maintains semantic coherence.
    Uses configurable chunk size and overlap from environment variables.
    """
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize the text splitter.
        
        Args:
            chunk_size: Maximum size of each chunk (default from env)
            chunk_overlap: Overlap between consecutive chunks (default from env)
            separators: List of separators to use for splitting
        """
        self.chunk_size = chunk_size or int(os.getenv("RAG_CHUNK_SIZE", 1000))
        self.chunk_overlap = chunk_overlap or int(os.getenv("RAG_CHUNK_OVERLAP", 200))
        
        # Default separators in order of preference (most to least specific)
        self.separators = separators or [
            "\n\n\n",      # Triple newline (major sections)
            "\n\n",        # Double newline (paragraphs)
            "\n",          # Single newline
            ". ",          # Sentence end
            "? ",          # Question end
            "! ",          # Exclamation end
            "; ",          # Semicolon
            ", ",          # Comma
            " ",           # Space
            ""             # Character level (last resort)
        ]
    
    def _split_text_by_separator(self, text: str, separator: str) -> List[str]:
        """Split text by a single separator."""
        if separator == "":
            return list(text)
        return text.split(separator)
    
    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """
        Merge splits to create chunks of approximately chunk_size.
        Maintains overlap between chunks.
        """
        merged = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_length = len(split) + len(separator)
            
            # If adding this split would exceed chunk_size
            if current_length + split_length > self.chunk_size and current_chunk:
                # Save current chunk
                merged.append(separator.join(current_chunk))
                
                # Calculate overlap - keep last portions for context
                overlap_length = 0
                overlap_splits = []
                
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_splits.insert(0, s)
                        overlap_length += len(s) + len(separator)
                    else:
                        break
                
                current_chunk = overlap_splits
                current_length = overlap_length
            
            current_chunk.append(split)
            current_length += split_length
        
        # Don't forget the last chunk
        if current_chunk:
            merged.append(separator.join(current_chunk))
        
        return merged
    
    def _recursive_split(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """
        Recursively split text using separators in order of preference.
        """
        if not text:
            return []
        
        # Base case: text is small enough
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []
        
        # Try each separator
        for i, separator in enumerate(separators):
            splits = self._split_text_by_separator(text, separator)
            
            # If we got meaningful splits
            if len(splits) > 1:
                # Merge splits to get chunks of appropriate size
                merged = self._merge_splits(splits, separator)
                
                # Check if any merged chunk is still too large
                final_chunks = []
                for chunk in merged:
                    if len(chunk) > self.chunk_size and i < len(separators) - 1:
                        # Recursively split with remaining separators
                        sub_chunks = self._recursive_split(
                            chunk,
                            separators[i + 1:]
                        )
                        final_chunks.extend(sub_chunks)
                    else:
                        if chunk.strip():
                            final_chunks.append(chunk)
                
                return final_chunks
        
        # If no separator worked, split by character limit
        return [text[i:i + self.chunk_size] 
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]
    
    def split_text(self, text: str, metadata: Optional[dict] = None) -> List[TextChunk]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: The text to split
            metadata: Optional metadata to include in each chunk
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        
        # Perform recursive splitting
        chunk_texts = self._recursive_split(text, self.separators)
        
        # Create TextChunk objects with positioning
        chunks = []
        current_pos = 0
        
        for i, chunk_text in enumerate(chunk_texts):
            # Find actual position in original text
            start_pos = text.find(chunk_text[:100], current_pos)
            if start_pos == -1:
                start_pos = current_pos
            
            end_pos = start_pos + len(chunk_text)
            
            chunk = TextChunk(
                content=chunk_text,
                metadata={
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunk_texts)
                },
                chunk_index=i,
                start_char=start_pos,
                end_char=end_pos
            )
            chunks.append(chunk)
            
            # Update position for next search
            current_pos = end_pos - self.chunk_overlap
            if current_pos < 0:
                current_pos = 0
        
        return chunks
    
    def split_documents(self, documents: List) -> List[TextChunk]:
        """
        Split multiple documents into chunks.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of all TextChunk objects
        """
        all_chunks = []
        
        for doc in documents:
            chunks = self.split_text(doc.content, doc.metadata)
            all_chunks.extend(chunks)
        
        return all_chunks


# Convenience function
def split_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    metadata: Optional[dict] = None
) -> List[TextChunk]:
    """
    Convenience function to split text with default settings.
    
    Args:
        text: Text to split
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks
        metadata: Optional metadata
        
    Returns:
        List of TextChunk objects
    """
    splitter = RecursiveTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text, metadata)
