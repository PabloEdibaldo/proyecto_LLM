from pydantic import BaseModel
from typing import Dict
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from typing import Any

class MetricsSummary(BaseModel):
    total_requests: int
    total_cost: float
    total_tokens: int
    rag_fast_usage: int = 0
    rag_precise_usage: int = 0
    evaluation_history: list[float] = []

class MetricsTracker:
    def __init__(self):
        self.total_requests = 0
        self.total_cost = 0.0
        self.total_tokens = 0
        self.rag_fast_usage = 0
        self.rag_precise_usage = 0
        self.evaluation_history = []
        
        # Simple cost estimation (approximate per 1K tokens, using generic blended rates)
        # gpt-3.5-turbo / gpt-4o-mini is much cheaper than gpt-4o
        self.cost_per_1k_tokens = {
            "gpt-3.5-turbo": 0.0015,
            "gpt-4o-mini": 0.00015,
            "gpt-4o": 0.005,
            "gpt-4-turbo": 0.01
        }
        
    def record_evaluation(self, score: float):
        self.evaluation_history.append(round(score, 4))
        
    def record_rag_usage(self, strategy: str):
        if strategy == "fast":
            self.rag_fast_usage += 1
        elif strategy == "precise":
            self.rag_precise_usage += 1

    def add_usage(self, model_name: str, tokens: int):
        self.total_tokens += tokens
        self.total_requests += 1
        
        # Estimate cost
        rate = 0.002 # default fallback
        for key in self.cost_per_1k_tokens:
            if key in model_name.lower():
                rate = self.cost_per_1k_tokens[key]
                break
                
        self.total_cost += (tokens / 1000.0) * rate

    def get_summary(self) -> MetricsSummary:
        return MetricsSummary(
            total_requests=self.total_requests,
            total_cost=round(self.total_cost, 6),
            total_tokens=self.total_tokens,
            rag_fast_usage=self.rag_fast_usage,
            rag_precise_usage=self.rag_precise_usage,
            evaluation_history=self.evaluation_history
        )

# Singleton metrics tracker
metrics_tracker = MetricsTracker()

class TokenCostCallbackHandler(BaseCallbackHandler):
    """Callback Handler that tracks token usage and updates metrics."""
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Collect token usage."""
        if not response.llm_output:
            return
            
        token_usage = response.llm_output.get("token_usage", {})
        total_tokens = token_usage.get("total_tokens", 0)
        model_name = response.llm_output.get("model_name", "unknown")
        
        if total_tokens > 0:
            metrics_tracker.add_usage(model_name, total_tokens)
