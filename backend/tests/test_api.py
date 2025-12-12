"""
Unit Tests for API Endpoints
Tests FastAPI routes and functionality.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
from fastapi.testclient import TestClient

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))


@pytest.fixture
def mock_rag_pipeline():
    """Create a mock RAG pipeline."""
    pipeline = Mock()
    pipeline.query.return_value = {
        "context": "Test context",
        "sources": [{"filename": "test.pdf", "score": 0.9, "category": "test"}],
        "num_results": 1
    }
    pipeline.get_stats.return_value = {
        "status": "initialized",
        "document_count": 100
    }
    return pipeline


@pytest.fixture
def client(mock_rag_pipeline):
    """Create a test client with mocked dependencies."""
    with patch('main.RAGPipeline') as mock_pipeline_class:
        mock_pipeline_class.return_value = mock_rag_pipeline
        mock_rag_pipeline.initialize = AsyncMock()
        
        from main import app
        app.state.rag_pipeline = mock_rag_pipeline
        
        return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns healthy status."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_health_endpoint(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data


class TestChatEndpoints:
    """Tests for chat endpoints."""
    
    def test_chat_endpoint_basic(self, client, mock_rag_pipeline):
        """Test basic chat request."""
        with patch('routes.chat.generate_llm_response', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Test response"
            
            response = client.post("/chat/", json={
                "message": "Hello",
                "use_rag": True,
                "use_tools": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
    
    def test_chat_with_conversation_history(self, client, mock_rag_pipeline):
        """Test chat with conversation history."""
        with patch('routes.chat.generate_llm_response', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Response with history"
            
            response = client.post("/chat/", json={
                "message": "Follow up question",
                "conversation_history": [
                    {"role": "user", "content": "Previous question"},
                    {"role": "assistant", "content": "Previous answer"}
                ],
                "use_rag": True,
                "use_tools": False
            })
            
            assert response.status_code == 200
    
    def test_rag_query_endpoint(self, client, mock_rag_pipeline):
        """Test direct RAG query endpoint."""
        response = client.post("/chat/rag/query", json={
            "query": "test query",
            "top_k": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "context" in data or "sources" in data
    
    def test_stats_endpoint(self, client, mock_rag_pipeline):
        """Test stats endpoint."""
        response = client.get("/chat/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestUploadEndpoints:
    """Tests for file upload endpoints."""
    
    def test_get_categories(self, client):
        """Test getting upload categories."""
        response = client.get("/upload/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0
    
    def test_upload_invalid_file_type(self, client):
        """Test that invalid file types are rejected."""
        response = client.post(
            "/upload/",
            files={"file": ("test.exe", b"content", "application/octet-stream")},
            data={"category": "general"}
        )
        
        assert response.status_code == 400
    
    def test_reindex_endpoint(self, client, mock_rag_pipeline):
        """Test reindex endpoint."""
        mock_rag_pipeline.clear_index = Mock()
        mock_rag_pipeline.load_and_index_documents = Mock(return_value=100)
        
        response = client.post("/upload/reindex")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestToolDetection:
    """Tests for tool intent detection in chat."""
    
    def test_detect_timetable_intent(self):
        """Test timetable intent detection."""
        from routes.chat import detect_tool_intent
        
        result = detect_tool_intent("What classes do I have today?")
        assert result is not None
        assert result["tool"] == "read_timetable_file"
    
    def test_detect_exam_intent(self):
        """Test exam notification intent detection."""
        from routes.chat import detect_tool_intent
        
        result = detect_tool_intent("When are my upcoming exams?")
        assert result is not None
        assert result["tool"] == "notify_upcoming_exams"
    
    def test_detect_study_plan_intent(self):
        """Test study plan intent detection."""
        from routes.chat import detect_tool_intent
        
        result = detect_tool_intent("Can you create a study plan for me?")
        assert result is not None
        assert result["tool"] == "generate_study_plan"
    
    def test_no_tool_intent(self):
        """Test that regular questions don't trigger tools."""
        from routes.chat import detect_tool_intent
        
        result = detect_tool_intent("What is machine learning?")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
