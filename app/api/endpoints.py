import time
from fastapi import APIRouter, Depends, HTTPException, Response
from app.api.models import AskRequest, AskResponse, FeedbackRequest
from app.core.dependencies import get_cache
from app.core.cache import RedisCache
from app.agents.graph import app_graph
from app.services.prometheus_metrics import metrics_tracker, get_metrics_prometheus
from app.services.quality_evaluator import quality_evaluator
from app.core.structured_logger import logger, log_query, RequestContext
import asyncio

router = APIRouter()

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest, cache: RedisCache = Depends(get_cache)):
    """
    Process a market research query.
    Uses A2A architecture: Researcher Agent + Evaluator Agent.
    Includes quality evaluation on sample basis and comprehensive metrics tracking.
    """
    start_time = time.time()
    request_id = RequestContext.get_request_id()
    
    logger.info(f"Processing query: {request.query[:100]}...")
    
    # Check cache
    cached_response = await cache.get(request.query)
    if cached_response:
        metrics_tracker.record_cache_hit()
        duration = (time.time() - start_time) * 1000
        log_query(logger, request.query, "cached", duration, cached=True)
        return AskResponse(
            query=request.query,
            response=cached_response["response"],
            cached=True,
            request_id=request_id
        )
    
    metrics_tracker.record_cache_miss()
    
    # Process with LangGraph
    try:
        final_state = app_graph.invoke({"query": request.query})
        response_text = final_state.get("final_response", "No response generated.")
        
        # Cache the response for 1 hour (3600 seconds)
        await cache.set(request.query, {"response": response_text}, ttl_seconds=3600)
        
        # Quality evaluation on sample basis (default 10%)
        quality_score, quality_reasoning = await quality_evaluator.evaluate_response(
            query=request.query,
            response=response_text,
            agent_role="evaluator"
        )
        
        # Record query type (this would be determined by RAG router in production)
        # For now, we'll default to hybrid
        metrics_tracker.record_query_type("hybrid")
        
        duration = (time.time() - start_time) * 1000
        log_query(logger, request.query, "hybrid", duration, cached=False)
        
        return AskResponse(
            query=request.query,
            response=response_text,
            cached=False,
            quality_score=quality_score,
            request_id=request_id
        )
    except Exception as e:
        metrics_tracker.record_error("query_processing_error", "evaluator")
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during processing.")


@router.get("/metrics")
async def prometheus_metrics():
    """
    Expose Prometheus metrics in OpenMetrics format.
    Compatible with Prometheus scraping.
    """
    return Response(
        content=get_metrics_prometheus(),
        media_type="text/plain; charset=utf-8"
    )


@router.get("/api/v1/metrics")
async def metrics_summary():
    """
    Get a summary of current metrics (JSON format).
    Useful for dashboards and monitoring.
    """
    return {
        "cache_hit_ratio": metrics_tracker.prometheus.cache_hit_ratio._value.get(),
        "total_cost_usd": metrics_tracker.cumulative_cost,
        "hourly_cost_estimate_usd": metrics_tracker.prometheus.cost_per_hour._value.get(),
        "response_quality_score": metrics_tracker.prometheus.response_quality_score.labels(
            agent_role="evaluator"
        )._value.get() or 0.0,
        "quality_evaluations_count": quality_evaluator.evaluation_count,
    }


from app.api.models import EvaluationRequest, EvaluationResponse

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_system(request: EvaluationRequest):
    """
    Run an automated evaluation over a batch of cases using LLM-as-a-judge.
    """
    logger.info(f"Running batch evaluation for {len(request.cases)} cases.")
    
    try:
        # Placeholder for batch evaluation logic
        # In a real system, this would use evaluator_judge service
        scores = []
        for case in request.cases:
            score, _ = await quality_evaluator.evaluate_response(
                query=case.get("query", ""),
                response=case.get("response", ""),
                agent_role="evaluator"
            )
            if score is not None:
                scores.append(score)
        
        average_score = sum(scores) / len(scores) if scores else 0.0
        
        return EvaluationResponse(
            average_score=average_score,
            total_cases=len(request.cases),
            scores=scores
        )
    except Exception as e:
        logger.error(f"Batch evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Evaluation processing failed.")
    
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
