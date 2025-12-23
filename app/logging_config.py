import logging
import sys
from datetime import datetime


def setup_logging():
    """Configure application logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'seed_library_{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )

    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
