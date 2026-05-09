from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from app.services.llm_factory import LLMFactory
from app.agents.tools import get_tools

def get_researcher_agent_executor(query: str):
    """
    Creates an AgentExecutor for the Researcher Agent.
    It binds the tools and system prompt to the selected LLM.
    """
    llm = LLMFactory.get_model(query, purpose="research")
    tools = get_tools()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Market Research Assistant. 
You have access to internal documents (via vector_search) and the web (via web_search/mock_web_search).
Always try to use internal documents first. If the information is missing or outdated, use web search.
Provide a comprehensive, clear, and well-structured draft response to the user's query."""),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor
