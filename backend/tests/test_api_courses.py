"""
Tests for the /api/courses API endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestCoursesEndpoint:
    """Tests for the /api/courses endpoint"""
    
    def test_get_courses_success(self, test_client, mock_rag_system):
        """Test successful retrieval of course statistics"""
        # Setup mock response
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": ["Python Basics", "Web Development", "Data Science"]
        }
        
        response = test_client.get("/api/courses")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3
        assert "Python Basics" in data["course_titles"]
        assert "Web Development" in data["course_titles"]
        assert "Data Science" in data["course_titles"]
        
        # Verify RAG system was called
        mock_rag_system.get_course_analytics.assert_called_once()
    
    def test_get_courses_empty_database(self, test_client, mock_rag_system):
        """Test retrieval when no courses are available"""
        # Setup mock response for empty database
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []
    
    def test_get_courses_single_course(self, test_client, mock_rag_system):
        """Test retrieval with exactly one course"""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Introduction to Programming"]
        }
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 1
        assert data["course_titles"] == ["Introduction to Programming"]
    
    def test_get_courses_many_courses(self, test_client, mock_rag_system):
        """Test retrieval with many courses"""
        # Generate a list of many course titles
        course_titles = [f"Course {i}" for i in range(100)]
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 100,
            "course_titles": course_titles
        }
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 100
        assert len(data["course_titles"]) == 100
        assert "Course 0" in data["course_titles"]
        assert "Course 99" in data["course_titles"]
    
    def test_get_courses_with_special_characters(self, test_client, mock_rag_system):
        """Test course titles with special characters and unicode"""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": [
                "C++ Programming", 
                "Español para Programadores",
                "🐍 Python & Data Science"
            ]
        }
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 3
        assert "C++ Programming" in data["course_titles"]
        assert "Español para Programadores" in data["course_titles"]
        assert "🐍 Python & Data Science" in data["course_titles"]
    
    def test_get_courses_rag_system_exception(self, test_client, mock_rag_system):
        """Test handling of RAG system exceptions"""
        # Setup mock to raise exception
        mock_rag_system.get_course_analytics.side_effect = Exception("Database connection error")
        
        response = test_client.get("/api/courses")
        
        # Should return 500 error
        assert response.status_code == 500
        assert "Database connection error" in response.json()["detail"]
    
    def test_get_courses_response_structure(self, test_client, mock_rag_system):
        """Test that response follows the expected structure"""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 2,
            "course_titles": ["Course A", "Course B"]
        }
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields are present
        required_fields = ["total_courses", "course_titles"]
        for field in required_fields:
            assert field in data
        
        # Check field types
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert all(isinstance(title, str) for title in data["course_titles"])
    
    def test_get_courses_invalid_methods(self, test_client):
        """Test that only GET method is allowed"""
        # POST should not be allowed
        response = test_client.post("/api/courses")
        assert response.status_code == 405
        
        # PUT should not be allowed
        response = test_client.put("/api/courses")
        assert response.status_code == 405
        
        # DELETE should not be allowed
        response = test_client.delete("/api/courses")
        assert response.status_code == 405
        
        # PATCH should not be allowed
        response = test_client.patch("/api/courses")
        assert response.status_code == 405
    
    def test_get_courses_query_parameters_ignored(self, test_client, mock_rag_system):
        """Test that query parameters are ignored (endpoint doesn't use them)"""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Test Course"]
        }
        
        # Make request with query parameters
        response = test_client.get("/api/courses?limit=5&sort=name")
        
        # Should still work and ignore parameters
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 1
        assert data["course_titles"] == ["Test Course"]
        
        # Verify RAG system was called normally
        mock_rag_system.get_course_analytics.assert_called_once_with()
    
    def test_get_courses_concurrent_requests(self, test_client, mock_rag_system):
        """Test handling of concurrent requests"""
        import threading
        
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 2,
            "course_titles": ["Course 1", "Course 2"]
        }
        
        results = []
        
        def make_request():
            response = test_client.get("/api/courses")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
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
    
    def test_get_courses_data_consistency(self, test_client, mock_rag_system):
        """Test that total_courses matches course_titles length"""
        # Test case where count and list don't match (edge case)
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 5,  # Says 5 courses
            "course_titles": ["Course 1", "Course 2"]  # But only 2 in list
        }
        
        response = test_client.get("/api/courses")
        
        # Should still return the data as provided by RAG system
        # (Data consistency is the responsibility of RAG system, not API)
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 5
        assert len(data["course_titles"]) == 2
    
    def test_get_courses_headers(self, test_client, mock_rag_system):
        """Test response headers"""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Test Course"]
        }
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        # Check for JSON content type
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_get_courses_caching_behavior(self, test_client, mock_rag_system):
        """Test that multiple calls work correctly (no unwanted caching)"""
        # First call
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Course A"]
        }
        
        response1 = test_client.get("/api/courses")
        assert response1.status_code == 200
        assert response1.json()["course_titles"] == ["Course A"]
        
        # Second call with different data
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 2,
            "course_titles": ["Course B", "Course C"]
        }
        
        response2 = test_client.get("/api/courses")
        assert response2.status_code == 200
        assert response2.json()["course_titles"] == ["Course B", "Course C"]
        
        # Verify both calls were made to RAG system
        assert mock_rag_system.get_course_analytics.call_count == 2
    
    def test_get_courses_very_long_titles(self, test_client, mock_rag_system):
        """Test courses with very long titles"""
        long_title = "A" * 1000  # Very long course title
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": [long_title]
        }
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 1
        assert data["course_titles"][0] == long_title