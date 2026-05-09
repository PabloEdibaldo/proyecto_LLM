from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.core.logger import logger
import os

COLLECTION_NAME = "market_research_docs"

def get_vector_store():
    """Get the PGVector vector store instance."""
    if not settings.OPENAI_API_KEY:
        # Fallback for testing/mocking if no API key is set
        logger.warning("No OPENAI_API_KEY provided. Using a dummy vector store or will fail on real queries.")
        os.environ["OPENAI_API_KEY"] = "dummy"

    embeddings = OpenAIEmbeddings()
    
    try:
        vector_store = PGVector(
            collection_name=COLLECTION_NAME,
            connection_string=settings.DATABASE_URL,
            embedding_function=embeddings,
        )
        return vector_store
    except Exception as e:
        logger.error(f"Failed to connect to PGVector: {e}")
        return None
