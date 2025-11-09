import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def setup_logging():
    """Configure logging to output to stdout/stderr"""
    log_level = os.getenv("LOG_LEVEL", "INFO")

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)
