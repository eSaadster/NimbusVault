import logging
import json
import sys
from datetime import datetime
from contextvars import ContextVar
from typing import Optional

request_id_ctx_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'level': record.levelname,
            'message': record.getMessage(),
        }
        request_id = request_id_ctx_var.get()
        if request_id:
            log_record['request_id'] = request_id
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def configure_logger(service_name: str, level: str = 'INFO') -> logging.Logger:
    logger = logging.getLogger(service_name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter(service_name)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger

async def request_id_middleware(request, call_next):
    request_id = request.headers.get('X-Request-ID')
    if not request_id:
        request_id = __import__('uuid').uuid4().hex
    request.state.request_id = request_id
    token = request_id_ctx_var.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_ctx_var.reset(token)
    response.headers['X-Request-ID'] = request_id
    return response

