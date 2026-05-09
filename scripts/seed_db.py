import os
import sys
from langchain_core.documents import Document
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def seed_database():
    print("Seeding database with sample market research documents...")
    
    if not settings.OPENAI_API_KEY:
        print("Warning: OPENAI_API_KEY is not set. Using dummy key. Embeddings will fail if not using a mock.")
        os.environ["OPENAI_API_KEY"] = "dummy"
        
    docs = [
        Document(
            page_content="Generative AI adoption in startups grew by 300% in 2024, focusing mostly on operational efficiency and content creation tools. Large enterprises showed a slower 45% growth, primarily investing in custom model training.",
            metadata={"source": "industry_report_2024", "topic": "AI Adoption"}
        ),
        Document(
            page_content="The SaaS market in Europe is expected to reach $150B by 2026. Key drivers include increased regulatory compliance solutions (GDPR tech) and localized cloud infrastructure.",
            metadata={"source": "eu_market_outlook", "topic": "SaaS European Market"}
        ),
        Document(
            page_content="Consumer hardware trends show a shift towards wearable AI companions. Investment in smart glasses and voice-first AI pins outpaced traditional smartwatches by 2x in Q3 2024.",
            metadata={"source": "hardware_trends_q3", "topic": "Wearables"}
        )
    ]
    
    try:
        embeddings = OpenAIEmbeddings()
        PGVector.from_documents(
            documents=docs,
            embedding=embeddings,
            collection_name="market_research_docs",
            connection_string=settings.DATABASE_URL
        )
        print("Successfully seeded database with 3 sample documents.")
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_database()
