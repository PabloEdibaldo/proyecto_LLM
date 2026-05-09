from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from app.agents.researcher import get_researcher_agent_executor
from app.agents.evaluator import get_evaluator_chain
from app.core.logger import logger

# Define the state schema
class GraphState(TypedDict):
    query: str
    draft: Optional[str]
    final_response: Optional[str]

# Define nodes
def research_node(state: GraphState):
    logger.info("Executing Researcher Agent...")
    query = state["query"]
    executor = get_researcher_agent_executor(query)
    
    result = executor.invoke({"input": query})
    draft = result.get("output", "")
    
    return {"draft": draft}

def evaluate_node(state: GraphState):
    logger.info("Executing Evaluator Agent...")
    query = state["query"]
    draft = state["draft"]
    
    chain = get_evaluator_chain(query)
    final_response = chain.invoke({"query": query, "draft": draft})
    
    return {"final_response": final_response}

# Build the graph
workflow = StateGraph(GraphState)

workflow.add_node("researcher", research_node)
workflow.add_node("evaluator", evaluate_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "evaluator")
workflow.add_edge("evaluator", END)

# Compile graph
app_graph = workflow.compile()
