"""
Tests for the /api/query API endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestQueryEndpoint:
    """Tests for the /api/query endpoint"""
    
    def test_query_success_without_session_id(self, test_client, mock_rag_system):
        """Test successful query without providing session ID"""
        # Setup mock response
        mock_rag_system.query.return_value = (
            "This is the answer to your query",
            ["Source 1: Test Course", "Source 2: Another Course"]
        )
        mock_rag_system.session_manager.create_session.return_value = "new-session-123"
        
        # Make request
        response = test_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is the answer to your query"
        assert len(data["sources"]) == 2
        assert "Source 1: Test Course" in data["sources"]
        assert data["session_id"] == "test-session"  # From fixture
        
        # Verify RAG system was called correctly
        mock_rag_system.query.assert_called_once_with("What is Python?", "test-session")
    
    def test_query_success_with_session_id(self, test_client, mock_rag_system):
        """Test successful query with provided session ID"""
        # Setup mock response
        mock_rag_system.query.return_value = (
            "Python is a programming language",
            ["Source: Python Basics Course"]
        )
        
        # Make request with session ID
        response = test_client.post(
            "/api/query",
            json={
                "query": "Explain Python basics",
                "session_id": "existing-session-456"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Python is a programming language"
        assert data["sources"] == ["Source: Python Basics Course"]
        assert data["session_id"] == "existing-session-456"
        
        # Verify RAG system was called with provided session ID
        mock_rag_system.query.assert_called_once_with("Explain Python basics", "existing-session-456")
    
    def test_query_empty_query_string(self, test_client, mock_rag_system):
        """Test query with empty query string"""
        response = test_client.post(
            "/api/query",
            json={"query": ""}
        )
        
        # Should still process (empty query handling is up to RAG system)
        assert response.status_code == 200
        mock_rag_system.query.assert_called_once()
    
    def test_query_missing_query_field(self, test_client):
        """Test request missing required query field"""
        response = test_client.post(
            "/api/query",
            json={"session_id": "test-session"}
        )
        
        # Should return validation error
        assert response.status_code == 422
        assert "query" in response.json()["detail"][0]["loc"]
    
    def test_query_invalid_json(self, test_client):
        """Test request with invalid JSON"""
        response = test_client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_query_rag_system_exception(self, test_client, mock_rag_system):
        """Test handling of RAG system exceptions"""
        # Setup mock to raise exception
        mock_rag_system.query.side_effect = Exception("RAG system error")
        
        response = test_client.post(
            "/api/query", 
            json={"query": "test query"}
        )
        
        # Should return 500 error
        assert response.status_code == 500
        assert "RAG system error" in response.json()["detail"]
    
    def test_query_response_structure(self, test_client, mock_rag_system):
        """Test that response follows the expected structure"""
        mock_rag_system.query.return_value = (
            "Test answer",
            ["Test source 1", "Test source 2", "Test source 3"]
        )
        
        response = test_client.post(
            "/api/query",
            json={"query": "test query"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields are present
        required_fields = ["answer", "sources", "session_id"]
        for field in required_fields:
            assert field in data
        
        # Check field types
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)
        assert all(isinstance(source, str) for source in data["sources"])
    
    def test_query_with_special_characters(self, test_client, mock_rag_system):
        """Test query with special characters and unicode"""
        special_query = "What about émojis 🚀 and special chars: @#$%^&*()?'"
        mock_rag_system.query.return_value = ("Answer", ["Source"])
        
        response = test_client.post(
            "/api/query",
            json={"query": special_query}
        )
        
        assert response.status_code == 200
        mock_rag_system.query.assert_called_once_with(special_query, "test-session")
    
    def test_query_very_long_query(self, test_client, mock_rag_system):
        """Test query with very long input"""
        long_query = "What is Python? " * 1000  # Very long query
        mock_rag_system.query.return_value = ("Answer", ["Source"])
        
        response = test_client.post(
            "/api/query",
            json={"query": long_query}
        )
        
        assert response.status_code == 200
        mock_rag_system.query.assert_called_once_with(long_query, "test-session")
    
    def test_query_with_none_session_id(self, test_client, mock_rag_system):
        """Test query with explicitly null session_id"""
        mock_rag_system.query.return_value = ("Answer", ["Source"])
        
        response = test_client.post(
            "/api/query",
            json={
                "query": "test query",
                "session_id": None
            }
        )
        
        assert response.status_code == 200
        # Should use default session from fixture
        mock_rag_system.query.assert_called_once_with("test query", "test-session")
    
    def test_query_returns_empty_sources(self, test_client, mock_rag_system):
        """Test query that returns no sources"""
        mock_rag_system.query.return_value = ("Answer without sources", [])
        
        response = test_client.post(
            "/api/query",
            json={"query": "test query"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Answer without sources"
        assert data["sources"] == []
    
    def test_query_http_methods(self, test_client):
        """Test that only POST method is allowed"""
        # GET should not be allowed
        response = test_client.get("/api/query")
        assert response.status_code == 405
        
        # PUT should not be allowed
        response = test_client.put("/api/query")
        assert response.status_code == 405
        
        # DELETE should not be allowed
        response = test_client.delete("/api/query")
        assert response.status_code == 405
    
    def test_query_content_type_validation(self, test_client, mock_rag_system):
        """Test content type validation"""
        # Test with form data instead of JSON
        response = test_client.post(
            "/api/query",
            data={"query": "test query"}
        )
        
        # Should still work with form data due to FastAPI's flexibility
        assert response.status_code in [200, 422]  # Depends on FastAPI version
    
    def test_query_concurrent_requests(self, test_client, mock_rag_system):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        mock_rag_system.query.return_value = ("Concurrent answer", ["Concurrent source"])
        
        results = []
        
        def make_request(query_text):
            response = test_client.post(
                "/api/query",
                json={"query": f"{query_text}"}
            )
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(f"Query {i}",))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5