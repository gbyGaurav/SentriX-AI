import logging
import sys
import contextvars
from app.core.config import settings

correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar('correlation_id', default='-')

class CustomFormatter(logging.Formatter):
    def format(self, record):
        record.correlation_id = correlation_id.get()
        return super().format(record)

def setup_logging():
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(level)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomFormatter(
        '%(asctime)s - %(name)s - [%(correlation_id)s] - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
