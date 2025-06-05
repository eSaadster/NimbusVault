import logging
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """Simple JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "service_name": getattr(record, "service_name", record.name),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)


class ServiceNameFilter(logging.Filter):
    """Injects service name into log records."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.service_name = self.service_name
        return True


def get_logger(service_name: str) -> logging.Logger:
    """Return a logger configured for the given service."""
    logger = logging.getLogger(service_name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.addFilter(ServiceNameFilter(service_name))
        logger.propagate = False
    return logger
