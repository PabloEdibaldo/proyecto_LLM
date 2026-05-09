import pytest
from app.services.llm_factory import LLMFactory
from app.services.metrics import MetricsTracker

def test_llm_factory_evaluator():
    llm = LLMFactory.get_model("test query", purpose="evaluation")
    assert llm.model_name == "gpt-4o"

def test_llm_factory_researcher_short_query():
    llm = LLMFactory.get_model("short query", purpose="research")
    assert llm.model_name == "gpt-4o-mini"

def test_llm_factory_researcher_long_query():
    long_query = "a" * 600
    llm = LLMFactory.get_model(long_query, purpose="research")
    assert llm.model_name == "gpt-4o"

def test_metrics_tracker():
    tracker = MetricsTracker()
    
    tracker.add_usage("gpt-4o-mini", 1000)
    summary = tracker.get_summary()
    
    assert summary.total_requests == 1
    assert summary.total_tokens == 1000
    assert summary.total_cost == 0.00015
    
    tracker.add_usage("gpt-4o", 1000)
    summary = tracker.get_summary()
    
    assert summary.total_requests == 2
    assert summary.total_tokens == 2000
    assert summary.total_cost == 0.00515
