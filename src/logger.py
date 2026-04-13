import logging
import os
from datetime import datetime

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("voice-agent")


def log_event(stage: str, message: str, latency_ms: float = None):
    entry = f"[{stage}] {message}"
    if latency_ms is not None:
        entry += f" | latency={latency_ms:.2f}ms"
    logger.info(entry)