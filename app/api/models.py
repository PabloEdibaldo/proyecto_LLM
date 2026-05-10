from pydantic import BaseModel, Field
from typing import Optional, List

class AskRequest(BaseModel):
    query: str = Field(..., description="The market research question.")
    user_id: Optional[str] = Field(None, description="Optional user identifier")

class AskResponse(BaseModel):
    query: str
    response: str
    cached: bool = False
    quality_score: Optional[float] = Field(None, description="Response quality score (0-100) if evaluated")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")

class FeedbackRequest(BaseModel):
    query: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comments: Optional[str] = None

class EvaluationCase(BaseModel):
    query: str
    response: str = Field(..., description="Response to evaluate")
    expected: Optional[str] = Field(None, description="Expected answer for comparison")

class EvaluationRequest(BaseModel):
    cases: List[EvaluationCase] = Field(..., description="List of cases to evaluate")

class EvaluationResponse(BaseModel):
    average_score: float
    total_cases: int
    scores: List[float]

class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"

class MetricsResponse(BaseModel):
    cache_hit_ratio: float
    total_cost_usd: float
    hourly_cost_estimate_usd: float
    response_quality_score: float
    quality_evaluations_count: int
