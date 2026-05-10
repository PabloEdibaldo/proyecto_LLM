"""
Structured JSON Logging Module
Provides centralized logging with request context propagation.
"""

import logging
import json
import uuid
import time
from datetime import datetime
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger
from typing import Optional, Any, Dict
import sys

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id_var: ContextVar[str] = ContextVar('session_id', default='')

# ============================================================================
# REQUEST CONTEXT MANAGEMENT
# ============================================================================

class RequestContext:
    """Manages request-scoped context"""
    
    @staticmethod
    def set_request_id(request_id: str):
        """Set request ID"""
        request_id_var.set(request_id)
    
    @staticmethod
    def get_request_id() -> str:
        """Get current request ID"""
        return request_id_var.get() or str(uuid.uuid4())
    
    @staticmethod
    def set_user_id(user_id: Optional[str]):
        """Set user ID (will be anonymized)"""
        user_id_var.set(user_id)
    
    @staticmethod
    def get_user_id() -> Optional[str]:
        """Get user ID"""
        return user_id_var.get()
    
    @staticmethod
    def generate_session_id():
        """Generate new session ID"""
        session_id = str(uuid.uuid4())
        session_id_var.set(session_id)
        return session_id


# ============================================================================
# CUSTOM JSON FORMATTER
# ============================================================================

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    
    def add_fields(self, log_record: Dict, record: logging.LogRecord, message_dict: Dict):
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Add request context
        log_record['request_id'] = RequestContext.get_request_id()
        log_record['user_id'] = RequestContext.get_user_id()  # Will be anonymized by log shipper
        log_record['session_id'] = session_id_var.get()
        
        # Add performance metrics if available
        if hasattr(record, 'duration_ms'):
            log_record['duration_ms'] = record.duration_ms
        
        if hasattr(record, 'llm_model'):
            log_record['llm_model'] = record.llm_model
        
        if hasattr(record, 'tokens_used'):
            log_record['tokens_used'] = record.tokens_used
        
        if hasattr(record, 'cost_usd'):
            log_record['cost_usd'] = record.cost_usd
        
        if hasattr(record, 'agent_role'):
            log_record['agent_role'] = record.agent_role
        
        if hasattr(record, 'query_type'):
            log_record['query_type'] = record.query_type
        
        # Remove redundant fields
        log_record.pop('message', None)
        log_record.pop('asctime', None)


# ============================================================================
# LOGGER FACTORY
# ============================================================================

def setup_logger(name: str, log_level: str = 'INFO', use_json: bool = True) -> logging.Logger:
    """
    Setup and return a logger with JSON formatting
    
    Args:
        name: Logger name (usually __name__)
        log_level: Logging level
        use_json: Whether to use JSON format
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    if use_json:
        # JSON formatter for Loki/ELK
        json_handler = logging.StreamHandler(sys.stdout)
        json_formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
        json_handler.setFormatter(json_formatter)
        logger.addHandler(json_handler)
    else:
        # Standard formatter for development
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# ============================================================================
# CONVENIENCE LOGGING FUNCTIONS
# ============================================================================

def log_llm_call(
    logger: logging.Logger,
    model: str,
    agent_role: str,
    duration_ms: float,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    success: bool = True
):
    """Log an LLM API call with all relevant metrics"""
    extra = {
        'llm_model': model,
        'agent_role': agent_role,
        'duration_ms': duration_ms,
        'tokens_used': input_tokens + output_tokens,
        'cost_usd': cost_usd,
    }
    
    if success:
        logger.info(
            f"LLM call: {model} ({agent_role}) - {duration_ms:.2f}ms - "
            f"{input_tokens}in/{output_tokens}out tokens - ${cost_usd:.4f}",
            extra=extra
        )
    else:
        logger.error(
            f"LLM call failed: {model} ({agent_role}) - {duration_ms:.2f}ms",
            extra=extra
        )


def log_agent_execution(
    logger: logging.Logger,
    agent_role: str,
    duration_ms: float,
    success: bool = True,
    error: Optional[str] = None
):
    """Log agent execution"""
    extra = {
        'agent_role': agent_role,
        'duration_ms': duration_ms,
    }
    
    if success:
        logger.info(
            f"Agent execution: {agent_role} - {duration_ms:.2f}ms",
            extra=extra
        )
    else:
        logger.error(
            f"Agent execution failed: {agent_role} - Error: {error}",
            extra=extra
        )


def log_query(
    logger: logging.Logger,
    query: str,
    query_type: str,
    duration_ms: float,
    cached: bool = False
):
    """Log query processing"""
    extra = {
        'query_type': query_type,
        'duration_ms': duration_ms,
    }
    
    if cached:
        logger.info(f"Query (cached): {query[:100]}... - {query_type}", extra=extra)
    else:
        logger.info(
            f"Query processed: {query[:100]}... - {query_type} - {duration_ms:.2f}ms",
            extra=extra
        )


# ============================================================================
# GLOBAL LOGGER INSTANCE
# ============================================================================

logger = setup_logger('app')
