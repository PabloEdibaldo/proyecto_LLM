from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.logger import logger

def route_query_strategy(query: str) -> str:
    """
    Decides whether to use 'fast' or 'precise' RAG strategy based on query complexity.
    If the query is long, has multiple constraints, or asks for deep analysis, use 'precise'.
    Otherwise, use 'fast'.
    """
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a query router. Given a user query, determine if it requires a 'fast' or 'precise' search strategy. "
                       "Output ONLY 'fast' or 'precise'. "
                       "'fast' is for simple, direct, or short questions. "
                       "'precise' is for complex, multi-part, analytical, or very specific questions."),
            ("user", "{query}")
        ])
        
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"query": query}).strip().lower()
        
        if result in ["fast", "precise"]:
            return result
        return "fast"
    except Exception as e:
        logger.warning(f"Error in RAG router, defaulting to fast: {e}")
        return "fast"
