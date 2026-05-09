from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from app.services.vector_db import get_vector_store
from app.core.config import settings
from app.core.logger import logger

# Try to initialize Tavily
if settings.TAVILY_API_KEY:
    try:
        web_search_tool = TavilySearchResults(max_results=3)
    except Exception as e:
        logger.warning(f"Could not initialize Tavily: {e}")
        web_search_tool = None
else:
    web_search_tool = None

@tool
def mock_web_search(query: str) -> str:
    """Mock web search for development and testing."""
    return f"Mock search results for: {query}. The market is growing rapidly with AI adoption."

@tool
def vector_search(query: str) -> str:
    """Search internal market research documents."""
    vector_store = get_vector_store()
    if not vector_store:
        return "Could not connect to the internal document database."
    
    docs = vector_store.similarity_search(query, k=3)
    if not docs:
        return "No relevant internal documents found."
    
    return "\n\n".join([f"Doc {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])

def get_tools():
    """Return the available tools for the researcher."""
    tools = [vector_search]
    if web_search_tool:
        tools.append(web_search_tool)
    else:
        tools.append(mock_web_search)
    return tools
