"""
Advanced Prometheus Metrics Module
Handles collection, tracking, and exposition of application metrics.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY
from typing import Dict, List, Optional
from enum import Enum
import time
from app.core.logger import logger

# ============================================================================
# METRIC TYPES AND ENUMS
# ============================================================================

class QueryType(Enum):
    """Types of queries handled by the system"""
    RAG = "rag"
    WEB_SEARCH = "web_search"
    HYBRID = "hybrid"

class AgentRole(Enum):
    """Agent roles in the system"""
    RESEARCHER = "researcher"
    EVALUATOR = "evaluator"

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

class PrometheusMetrics:
    """Singleton for managing all Prometheus metrics"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Request counters
        self.request_total = Counter(
            'api_requests_total',
            'Total API requests',
            ['endpoint', 'method', 'status']
        )
        
        self.request_success = Counter(
            'api_requests_success_total',
            'Total successful API requests',
            ['endpoint', 'agent_role']
        )
        
        # Latency histograms
        self.request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration in seconds',
            ['endpoint', 'method'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
        )
        
        self.agent_latency = Histogram(
            'agent_execution_duration_seconds',
            'Agent execution latency (p50, p99)',
            ['agent_role'],
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0)
        )
        
        self.llm_call_duration = Histogram(
            'llm_call_duration_seconds',
            'LLM API call duration',
            ['model', 'agent_role'],
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0)
        )
        
        # Token metrics
        self.tokens_used = Counter(
            'tokens_used_total',
            'Total tokens consumed',
            ['model', 'token_type']  # token_type: input, output
        )
        
        self.tokens_by_agent = Counter(
            'tokens_by_agent_total',
            'Tokens used by agent',
            ['agent_role']
        )
        
        # Cost metrics
        self.api_cost_total = Gauge(
            'api_cost_total_usd',
            'Total API cost in USD'
        )
        
        self.cost_per_hour = Gauge(
            'api_cost_per_hour_usd',
            'Estimated API cost per hour in USD'
        )
        
        self.cost_by_model = Counter(
            'api_cost_by_model_usd',
            'API cost by model in USD',
            ['model']
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits'
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses'
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio (0-1)'
        )
        
        # Query type metrics
        self.query_type_total = Counter(
            'queries_by_type_total',
            'Queries by type',
            ['query_type']
        )
        
        # Response quality metrics
        self.response_quality_score = Gauge(
            'response_quality_score',
            'Response quality score (0-100)',
            ['agent_role']
        )
        
        self.response_quality_samples = Counter(
            'response_quality_samples_total',
            'Number of quality samples evaluated',
            ['quality_level']  # quality_level: excellent, good, fair, poor
        )
        
        # Error metrics
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'agent_role']
        )
        
        # Requests in flight
        self.requests_in_flight = Gauge(
            'requests_in_flight',
            'Number of requests currently being processed',
            ['endpoint']
        )
        
        # Queue metrics
        self.queue_size = Gauge(
            'queue_size',
            'Size of request queue',
            ['queue_name']
        )
        
        logger.info("Prometheus metrics initialized successfully")


# ============================================================================
# METRICS TRACKER (High-level API)
# ============================================================================

class MetricsTracker:
    """High-level interface for recording application metrics"""
    
    def __init__(self):
        self.prometheus = PrometheusMetrics()
        self.cumulative_cost = 0.0
        self.request_count_for_hourly = 0
        self.cost_for_hourly = 0.0
        self.hourly_reset_time = time.time()
    
    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record HTTP request"""
        self.prometheus.request_total.labels(
            endpoint=endpoint, method=method, status=status_code
        ).inc()
        
        self.prometheus.request_duration.labels(
            endpoint=endpoint, method=method
        ).observe(duration)
    
    def record_agent_execution(self, agent_role: str, duration: float, success: bool):
        """Record agent execution metrics"""
        self.prometheus.agent_latency.labels(
            agent_role=agent_role
        ).observe(duration)
        
        if success:
            self.prometheus.request_success.labels(
                endpoint='agent', agent_role=agent_role
            ).inc()
    
    def record_llm_call(self, model: str, agent_role: str, duration: float, 
                       input_tokens: int, output_tokens: int, cost: float):
        """Record LLM API call metrics"""
        self.prometheus.llm_call_duration.labels(
            model=model, agent_role=agent_role
        ).observe(duration)
        
        self.prometheus.tokens_used.labels(
            model=model, token_type='input'
        ).inc(input_tokens)
        
        self.prometheus.tokens_used.labels(
            model=model, token_type='output'
        ).inc(output_tokens)
        
        self.prometheus.tokens_by_agent.labels(
            agent_role=agent_role
        ).inc(input_tokens + output_tokens)
        
        self.cumulative_cost += cost
        self.cost_for_hourly += cost
        self.prometheus.api_cost_total.set(self.cumulative_cost)
        self.prometheus.cost_by_model.labels(model=model).inc(cost)
        
        # Update hourly cost estimate
        self._update_hourly_cost()
    
    def _update_hourly_cost(self):
        """Update estimated hourly cost"""
        now = time.time()
        elapsed = now - self.hourly_reset_time
        
        if elapsed >= 3600:  # Reset every hour
            self.cost_for_hourly = 0.0
            self.hourly_reset_time = now
        
        if elapsed > 0:
            estimated_hourly = (self.cost_for_hourly / elapsed) * 3600
            self.prometheus.cost_per_hour.set(estimated_hourly)
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.prometheus.cache_hits.inc()
        self._update_cache_ratio()
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.prometheus.cache_misses.inc()
        self._update_cache_ratio()
    
    def _update_cache_ratio(self):
        """Update cache hit ratio"""
        hits = self.prometheus.cache_hits._value.get()
        misses = self.prometheus.cache_misses._value.get()
        total = hits + misses
        
        if total > 0:
            ratio = hits / total
            self.prometheus.cache_hit_ratio.set(ratio)
    
    def record_query_type(self, query_type: str):
        """Record query type"""
        self.prometheus.query_type_total.labels(query_type=query_type).inc()
    
    def record_response_quality(self, score: float, agent_role: str = 'evaluator'):
        """Record response quality score (0-100)"""
        self.prometheus.response_quality_score.labels(
            agent_role=agent_role
        ).set(score)
        
        # Categorize quality level
        if score >= 80:
            quality_level = 'excellent'
        elif score >= 60:
            quality_level = 'good'
        elif score >= 40:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        self.prometheus.response_quality_samples.labels(
            quality_level=quality_level
        ).inc()
    
    def record_error(self, error_type: str, agent_role: str = 'unknown'):
        """Record error"""
        self.prometheus.errors_total.labels(
            error_type=error_type, agent_role=agent_role
        ).inc()
    
    def set_requests_in_flight(self, endpoint: str, count: int):
        """Set number of requests in flight"""
        self.prometheus.requests_in_flight.labels(endpoint=endpoint).set(count)
    
    def set_queue_size(self, queue_name: str, size: int):
        """Set queue size"""
        self.prometheus.queue_size.labels(queue_name=queue_name).set(size)
    
    def get_metrics_dict(self) -> Dict:
        """Get current metrics as dictionary (for /metrics endpoint)"""
        return {
            'cache_hit_ratio': self.prometheus.cache_hit_ratio._value.get(),
            'total_cost': self.cumulative_cost,
            'hourly_cost_estimate': self.prometheus.cost_per_hour._value.get(),
            'response_quality_score': self.prometheus.response_quality_score.labels(
                agent_role='evaluator'
            )._value.get(),
        }


# Global instance
metrics_tracker = MetricsTracker()


def get_metrics_prometheus() -> bytes:
    """Generate Prometheus-format metrics"""
    return generate_latest(REGISTRY)
