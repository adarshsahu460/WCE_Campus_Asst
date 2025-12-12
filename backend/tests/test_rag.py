"""
Unit Tests for RAG Pipeline
Tests document loading, splitting, embeddings, and retrieval.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from rag.loader import DocumentLoader, Document
from rag.splitter import RecursiveTextSplitter, TextChunk
from rag.retriever import DocumentRetriever, RetrievalResult


class TestDocumentLoader:
    """Tests for DocumentLoader class."""
    
    def test_init_creates_directories(self, tmp_path):
        """Test that loader creates necessary directories."""
        with patch.dict(os.environ, {
            "DATA_DIR": str(tmp_path / "data"),
            "TIMETABLE_DIR": str(tmp_path / "data" / "timetables"),
            "NOTICES_DIR": str(tmp_path / "data" / "notices"),
            "SYLLABUS_DIR": str(tmp_path / "data" / "syllabus"),
            "EXAMS_DIR": str(tmp_path / "data" / "exams"),
            "REGULATIONS_DIR": str(tmp_path / "data" / "regulations")
        }):
            loader = DocumentLoader()
            assert Path(tmp_path / "data").exists()
            assert Path(tmp_path / "data" / "timetables").exists()
    
    def test_load_text_file(self, tmp_path):
        """Test loading a text file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "This is a test document."
        test_file.write_text(test_content)
        
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            loader = DocumentLoader()
            doc = loader.load_text(str(test_file))
            
            assert doc.content == test_content
            assert doc.doc_type == "text"
            assert "test.txt" in doc.metadata["filename"]
    
    def test_load_csv_file(self, tmp_path):
        """Test loading a CSV file."""
        test_file = tmp_path / "test.csv"
        test_content = "name,value\nitem1,100\nitem2,200"
        test_file.write_text(test_content)
        
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            loader = DocumentLoader()
            doc = loader.load_csv(str(test_file))
            
            assert "name" in doc.content
            assert "item1" in doc.content
            assert doc.doc_type == "csv"
            assert doc.metadata["row_count"] == 2
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test that loading nonexistent file raises error."""
        with patch.dict(os.environ, {"DATA_DIR": str(tmp_path)}):
            loader = DocumentLoader()
            
            with pytest.raises(FileNotFoundError):
                loader.load_text(str(tmp_path / "nonexistent.txt"))


class TestRecursiveTextSplitter:
    """Tests for RecursiveTextSplitter class."""
    
    def test_split_short_text(self):
        """Test that short text is not split."""
        splitter = RecursiveTextSplitter(chunk_size=100, chunk_overlap=20)
        text = "This is a short text."
        
        chunks = splitter.split_text(text)
        
        assert len(chunks) == 1
        assert chunks[0].content == text
    
    def test_split_long_text(self):
        """Test that long text is split into chunks."""
        splitter = RecursiveTextSplitter(chunk_size=50, chunk_overlap=10)
        text = "This is a longer text. " * 20
        
        chunks = splitter.split_text(text)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= 60  # Some tolerance
    
    def test_chunk_metadata(self):
        """Test that chunks have correct metadata."""
        splitter = RecursiveTextSplitter(chunk_size=50, chunk_overlap=10)
        text = "Test " * 100
        metadata = {"source": "test.txt", "category": "test"}
        
        chunks = splitter.split_text(text, metadata)
        
        for i, chunk in enumerate(chunks):
            assert chunk.metadata["source"] == "test.txt"
            assert chunk.metadata["chunk_index"] == i
            assert "total_chunks" in chunk.metadata
    
    def test_empty_text(self):
        """Test handling of empty text."""
        splitter = RecursiveTextSplitter()
        
        chunks = splitter.split_text("")
        assert len(chunks) == 0
        
        chunks = splitter.split_text("   ")
        assert len(chunks) == 0


class TestDocumentRetriever:
    """Tests for DocumentRetriever class."""
    
    @patch('rag.retriever.get_default_embeddings')
    @patch('rag.retriever.get_vector_db')
    def test_retrieve_returns_results(self, mock_db, mock_embeddings):
        """Test that retrieve returns results."""
        # Setup mocks
        mock_embeddings.return_value.embed_text.return_value = [0.1] * 768
        mock_db.return_value.search.return_value = [
            Mock(
                content="Test content",
                metadata={"source": "test.txt", "category": "test"},
                score=0.9,
                id="1"
            )
        ]
        
        retriever = DocumentRetriever()
        results = retriever.retrieve("test query")
        
        assert len(results) > 0
        assert results[0].content == "Test content"
    
    @patch('rag.retriever.get_default_embeddings')
    @patch('rag.retriever.get_vector_db')
    def test_retrieve_with_sources(self, mock_db, mock_embeddings):
        """Test retrieve_with_sources returns formatted output."""
        mock_embeddings.return_value.embed_text.return_value = [0.1] * 768
        mock_db.return_value.search.return_value = [
            Mock(
                content="Test content",
                metadata={"source": "test.txt", "category": "test", "filename": "test.txt"},
                score=0.9,
                id="1"
            )
        ]
        
        retriever = DocumentRetriever()
        result = retriever.retrieve_with_sources("test query")
        
        assert "context" in result
        assert "sources" in result
        assert "num_results" in result
        assert result["num_results"] > 0


class TestEmbeddings:
    """Tests for embedding modules."""
    
    @patch('rag.embeddings.OpenAI')
    def test_openai_embeddings_dimension(self, mock_openai):
        """Test OpenAI embeddings dimension property."""
        from rag.embeddings import OpenAIEmbeddings
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            assert embeddings.dimension == 3072
    
    def test_get_embeddings_auto(self):
        """Test get_embeddings with auto detection."""
        from rag.embeddings import get_embeddings
        
        with patch.dict(os.environ, {
            "EMBEDDING_MODEL": "text-embedding-3-large",
            "OPENAI_API_KEY": "test-key"
        }):
            with patch('rag.embeddings.OpenAI'):
                embeddings = get_embeddings("auto")
                assert embeddings is not None


# Pytest fixtures
@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        content="This is sample content for testing.",
        metadata={"source": "test.txt", "type": "text"},
        source="test.txt",
        doc_type="text"
    )


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    return [
        TextChunk(
            content=f"Chunk {i} content",
            metadata={"chunk_index": i},
            chunk_index=i,
            start_char=i * 100,
            end_char=(i + 1) * 100
        )
        for i in range(5)
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
