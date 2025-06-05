import logging
import json
import sys
from datetime import datetime
from contextvars import ContextVar
from typing import Optional

# Context variable for request ID tracking
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

class JsonFormatter(logging.Formatter):
    """JSON log formatter with service name and optional request ID support."""
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add request ID if available in context
        request_id = request_id_ctx_var.get()
        if request_id:
            log_record["request_id"] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)

class ServiceNameFilter(logging.Filter):
    """Injects service name into log records for backward compatibility."""
    
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.service_name = self.service_name
        return True

def get_logger(service_name: str, level: str = "INFO") -> logging.Logger:
    """Return a logger configured for the given service (legacy interface)."""
    return configure_logger(service_name, level)

def configure_logger(service_name: str, level: str = "INFO") -> logging.Logger:
    """Configure and return a logger for the given service."""
    logger = logging.getLogger(service_name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Configure handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter(service_name)
    handler.setFormatter(formatter)
    
    # Add filter for backward compatibility
    service_filter = ServiceNameFilter(service_name)
    logger.addFilter(service_filter)
    
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    
    return logger

async def request_id_middleware(request, call_next):
    """Middleware to track request IDs across async operations."""
    request_id = request.headers.get('X-Request-ID')
    if not request_id:
        import uuid
        request_id = uuid.uuid4().hex
    
    request.state.request_id = request_id
    token = request_id_ctx_var.set(request_id)
    
    try:
        response = await call_next(request)
    finally:
        request_id_ctx_var.reset(token)
    
    response.headers['X-Request-ID'] = request_id
    return response