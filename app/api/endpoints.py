from fastapi import APIRouter, Depends, HTTPException
from app.api.models import AskRequest, AskResponse, FeedbackRequest
from app.core.dependencies import get_cache
from app.core.cache import RedisCache
from app.agents.graph import app_graph
from app.services.metrics import metrics_tracker
from app.core.logger import logger

router = APIRouter()

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest, cache: RedisCache = Depends(get_cache)):
    """
    Process a market research query.
    Uses A2A architecture: Researcher Agent + Evaluator Agent.
    """
    logger.info(f"Received query: {request.query}")
    
    # Check cache
    cached_response = await cache.get(request.query)
    if cached_response:
        return AskResponse(query=request.query, response=cached_response["response"], cached=True)
    
    # Process with LangGraph
    try:
        final_state = app_graph.invoke({"query": request.query})
        response_text = final_state.get("final_response", "No response generated.")
        
        # Cache the response for 1 hour (3600 seconds)
        await cache.set(request.query, {"response": response_text}, ttl_seconds=3600)
        
        return AskResponse(query=request.query, response=response_text, cached=False)
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during processing.")

from app.api.models import AskRequest, AskResponse, FeedbackRequest, EvaluationRequest, EvaluationResponse
from app.services.evaluator_judge import evaluator_judge

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_system(request: EvaluationRequest):
    """
    Run an automated evaluation over a batch of cases using LLM-as-a-judge.
    """
    logger.info(f"Running evaluation for {len(request.cases)} cases.")
    
    result = await evaluator_judge.evaluate_batch(request.cases)
    
    # Save score to metrics
    metrics_tracker.record_evaluation(result["average_score"])
    
    return EvaluationResponse(
        average_score=result["average_score"],
        results=result["results"]
    )

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback for a response to simulate fine-tuning data collection.
    """
    logger.info(f"Received feedback for query '{request.query}': Rating {request.rating}, Comments: {request.comments}")
    return {"status": "success", "message": "Feedback recorded successfully."}

@router.get("/metrics")
async def get_metrics():
    """
    Return accumulated metrics (costs, tokens, requests).
    """
    return metrics_tracker.get_summary()
