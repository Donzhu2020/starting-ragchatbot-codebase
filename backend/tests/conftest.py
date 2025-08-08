"""
Shared fixtures and configuration for RAG system tests.
"""

import pytest
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from typing import Generator

# Mock the static file mounting to avoid dependency on frontend directory
import sys
from unittest.mock import patch

# Patch StaticFiles before importing the app
with patch('fastapi.staticfiles.StaticFiles'):
    # Import after patching to avoid static file mounting issues
    from config import Config
    from rag_system import RAGSystem
    from models import Course, Lesson


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = Config()
    # Override with test-specific values
    config.CHUNK_SIZE = 100
    config.CHUNK_OVERLAP = 20
    config.MAX_RESULTS = 3
    config.MAX_HISTORY = 1
    config.ANTHROPIC_API_KEY = "test-api-key"
    return config


@pytest.fixture
def sample_course_data():
    """Sample course data for testing"""
    return {
        "course_title": "Test Course",
        "course_link": "https://example.com/test-course",
        "course_instructor": "Test Instructor",
        "lessons": [
            {
                "lesson_number": 0,
                "title": "Introduction",
                "lesson_link": "https://example.com/lesson-0",
                "content": "This is the introduction lesson content."
            },
            {
                "lesson_number": 1, 
                "title": "Advanced Topics",
                "lesson_link": "https://example.com/lesson-1",
                "content": "This lesson covers advanced topics in detail."
            }
        ]
    }


@pytest.fixture
def sample_courses():
    """Sample Course objects for testing"""
    return [
        Course(
            title="Python Basics",
            link="https://example.com/python",
            instructor="John Doe",
            lessons=[
                Lesson(lesson_number=0, title="Introduction", lesson_link="https://example.com/python/0"),
                Lesson(lesson_number=1, title="Variables", lesson_link="https://example.com/python/1")
            ]
        ),
        Course(
            title="Web Development",
            link="https://example.com/web",
            instructor="Jane Smith", 
            lessons=[
                Lesson(lesson_number=0, title="HTML Basics", lesson_link="https://example.com/web/0"),
                Lesson(lesson_number=1, title="CSS Styling", lesson_link="https://example.com/web/1")
            ]
        )
    ]


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "This is a test response from Claude."
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing"""
    mock_store = MagicMock()
    mock_store.add_courses.return_value = None
    mock_store.search.return_value = [
        {
            "content": "Test content chunk",
            "course_title": "Test Course", 
            "lesson_number": 0,
            "source": "Test Course - Lesson 0: Introduction"
        }
    ]
    mock_store.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Python Basics", "Web Development"]
    }
    return mock_store


@pytest.fixture
def mock_rag_system(mock_config, mock_vector_store, mock_anthropic_client):
    """Mock RAG system for testing"""
    with patch('rag_system.VectorStore') as mock_vs_class:
        with patch('rag_system.anthropic.Anthropic') as mock_anthropic_class:
            mock_vs_class.return_value = mock_vector_store
            mock_anthropic_class.return_value = mock_anthropic_client
            
            rag_system = RAGSystem(mock_config)
            return rag_system


@pytest.fixture
def temp_docs_dir():
    """Create a temporary directory with sample documents for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a sample course document
        course_doc = """Course Title: Sample Course
Course Link: https://example.com/sample
Course Instructor: Test Instructor

Lesson 0: Introduction
Lesson Link: https://example.com/lesson0
This is the introduction lesson with basic concepts.

Lesson 1: Advanced Topics  
Lesson Link: https://example.com/lesson1
This lesson covers more advanced material and techniques.
"""
        doc_path = os.path.join(temp_dir, "sample_course.txt")
        with open(doc_path, "w") as f:
            f.write(course_doc)
            
        yield temp_dir


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing"""
    mock_manager = MagicMock()
    mock_manager.create_session.return_value = "test-session-123"
    mock_manager.get_session.return_value = {"history": []}
    mock_manager.add_to_session.return_value = None
    return mock_manager


class TestAppFactory:
    """Factory for creating test FastAPI applications"""
    
    @staticmethod
    def create_test_app(mock_rag_system):
        """Create a test FastAPI app without static file mounting"""
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        from typing import List, Optional
        
        # Create test app without static files
        app = FastAPI(title="Test RAG System")
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Pydantic models
        class QueryRequest(BaseModel):
            query: str
            session_id: Optional[str] = None

        class QueryResponse(BaseModel):
            answer: str
            sources: List[str]
            session_id: str

        class CourseStats(BaseModel):
            total_courses: int
            course_titles: List[str]
        
        # API endpoints
        @app.post("/api/query", response_model=QueryResponse)
        async def query_documents(request: QueryRequest):
            try:
                session_id = request.session_id or "test-session"
                answer, sources = mock_rag_system.query(request.query, session_id)
                return QueryResponse(
                    answer=answer,
                    sources=sources,
                    session_id=session_id
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/courses", response_model=CourseStats)
        async def get_course_stats():
            try:
                analytics = mock_rag_system.get_course_analytics()
                return CourseStats(
                    total_courses=analytics["total_courses"],
                    course_titles=analytics["course_titles"]
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        return app


@pytest.fixture
def test_app(mock_rag_system):
    """FastAPI test application"""
    return TestAppFactory.create_test_app(mock_rag_system)


@pytest.fixture
def test_client(test_app):
    """FastAPI test client"""
    return TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables"""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
    os.environ["TESTING"] = "true"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)