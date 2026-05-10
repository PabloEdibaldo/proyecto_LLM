"""
FastAPI Middleware for observability
Captures request context, metrics, and timing.
"""

import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
from app.core.structured_logger import RequestContext, logger
from app.services.prometheus_metrics import metrics_tracker

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set request context and capture timing"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID if not present
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        RequestContext.set_request_id(request_id)
        
        # Extract user ID from headers (optional)
        user_id = request.headers.get('X-User-ID')
        if user_id:
            RequestContext.set_user_id(user_id)
        
        # Record start time
        start_time = time.time()
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        metrics_tracker.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=duration
        )
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration*1000:.2f}ms",
            extra={'duration_ms': duration * 1000}
        )
        
        return response


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to update request counter and in-flight metrics"""
    
    def __init__(self, app, group_paths: bool = False):
        super().__init__(app)
        self.group_paths = group_paths
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Update in-flight requests
        endpoint = request.url.path
        
        response = await call_next(request)
        
        return response
