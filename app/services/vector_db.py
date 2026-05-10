from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.core.logger import logger
import os

COLLECTION_SMALL = "docs_small"
COLLECTION_LARGE = "docs_large"

def get_vector_store(strategy: str = "fast"):
    """Get the PGVector vector store instance for the given strategy."""
    if not settings.OPENAI_API_KEY:
        # Fallback for testing/mocking if no API key is set
        logger.warning("No OPENAI_API_KEY provided. Using a dummy vector store or will fail on real queries.")
        os.environ["OPENAI_API_KEY"] = "dummy"

    try:
        if strategy == "precise":
            embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            vector_store = PGVector(
                collection_name=COLLECTION_LARGE,
                connection_string=settings.DATABASE_URL,
                embedding_function=embeddings,
            )
        else: # default fast
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vector_store = PGVector(
                collection_name=COLLECTION_SMALL,
                connection_string=settings.DATABASE_URL,
                embedding_function=embeddings,
            )
        return vector_store
    except Exception as e:
        logger.error(f"Failed to connect to PGVector: {e}")
        return None
