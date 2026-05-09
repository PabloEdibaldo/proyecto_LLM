import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.core.cache import redis_cache

client = TestClient(app)

@pytest.fixture
def mock_cache():
    with patch.object(redis_cache, 'get', new_callable=AsyncMock) as mock_get:
        with patch.object(redis_cache, 'set', new_callable=AsyncMock) as mock_set:
            yield mock_get, mock_set

@pytest.fixture
def mock_graph():
    with patch('app.api.endpoints.app_graph.invoke') as mock_invoke:
        yield mock_invoke

def test_ask_endpoint_cache_miss(mock_cache, mock_graph):
    mock_get, mock_set = mock_cache
    mock_get.return_value = None
    mock_graph.return_value = {"final_response": "Mocked response from agents."}

    response = client.post("/api/v1/ask", json={"query": "test query"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test query"
    assert data["response"] == "Mocked response from agents."
    assert data["cached"] == False
    
    mock_get.assert_called_once()
    mock_graph.assert_called_once()
    mock_set.assert_called_once()

def test_ask_endpoint_cache_hit(mock_cache, mock_graph):
    mock_get, mock_set = mock_cache
    mock_get.return_value = {"response": "Cached answer"}

    response = client.post("/api/v1/ask", json={"query": "test query"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Cached answer"
    assert data["cached"] == True
    
    mock_get.assert_called_once()
    mock_graph.assert_not_called()

def test_feedback_endpoint():
    response = client.post("/api/v1/feedback", json={
        "query": "test query",
        "rating": 5,
        "comments": "Great answer"
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_metrics_endpoint():
    response = client.get("/api/v1/metrics")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_cost" in data
    assert "total_tokens" in data
