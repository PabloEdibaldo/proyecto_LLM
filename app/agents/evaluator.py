from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.llm_factory import LLMFactory

def get_evaluator_chain(query: str):
    """
    Creates a simple chain for the Evaluator Agent.
    The evaluator reviews the draft from the researcher and refines it.
    """
    llm = LLMFactory.get_model(query, purpose="evaluation")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Market Research Analyst.
Your task is to review a draft response written by a junior researcher.
Improve the tone, structure, and clarity of the draft. 
If the draft is already excellent, simply return it with minor polishes.
Do not mention that this is a refined draft, just output the final version for the client.

Original User Query: {query}
"""),
        ("user", "Junior Researcher Draft:\n{draft}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain
