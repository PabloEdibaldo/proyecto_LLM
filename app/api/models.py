from pydantic import BaseModel, Field
from typing import Optional

class AskRequest(BaseModel):
    query: str = Field(..., description="The market research question.")

class AskResponse(BaseModel):
    query: str
    response: str
    cached: bool = False

class FeedbackRequest(BaseModel):
    query: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comments: Optional[str] = None
