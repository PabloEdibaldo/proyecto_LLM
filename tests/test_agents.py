import pytest
from unittest.mock import patch, MagicMock
from app.agents.tools import mock_web_search, get_tools

def test_mock_web_search():
    result = mock_web_search.invoke({"query": "AI Trends"})
    assert "Mock search results" in result
    assert "AI Trends" in result

@patch('app.agents.tools.get_vector_store')
def test_vector_search_no_db(mock_get_vs):
    mock_get_vs.return_value = None
    from app.agents.tools import vector_search
    
    result = vector_search.invoke({"query": "Test"})
    assert result == "Could not connect to the internal document database."

@patch('app.agents.tools.get_vector_store')
def test_vector_search_with_results(mock_get_vs):
    mock_vs = MagicMock()
    mock_doc = MagicMock()
    mock_doc.page_content = "This is a test document."
    mock_vs.similarity_search.return_value = [mock_doc]
    mock_get_vs.return_value = mock_vs
    
    from app.agents.tools import vector_search
    result = vector_search.invoke({"query": "Test"})
    
    assert "Doc 1:" in result
    assert "This is a test document." in result

def test_get_tools_contains_vector_search():
    tools = get_tools()
    tool_names = [t.name for t in tools]
    assert "vector_search" in tool_names
