"""
Logging Configuration
Sets up structured logging for the application.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import structlog


def setup_logging(log_level: str = "INFO", log_dir: str = "./logs") -> None:
    """Setup structured logging."""
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Log file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"sunny_ai_{timestamp}.log"
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logger = structlog.get_logger()
    logger.info("Logging initialized", log_file=str(log_file), level=log_level)
