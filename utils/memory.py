"""
utils/memory.py — Memory Logging Helper for RecruitX

Provides a lightweight helper to log current process memory usage
at key stages of the application lifecycle. Used to monitor RAM
consumption on Render Free tier (512 MB limit).

Usage:
    from utils.memory import log_memory

    log_memory("startup")
    log_memory("after model load")
"""

import logging
import os

logger = logging.getLogger(__name__)


def log_memory(stage: str) -> None:
    """
    Log current process RSS memory usage in MB.

    Args:
        stage: A label describing the current lifecycle stage
               (e.g., "startup", "after model load", "first request").
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        rss_mb = process.memory_info().rss / (1024 * 1024)
        logger.info("[MEMORY] %s: %.1f MB RSS", stage, rss_mb)
    except ImportError:
        logger.debug("[MEMORY] psutil not installed — skipping memory log for '%s'", stage)
    except Exception as e:
        logger.warning("[MEMORY] Failed to log memory at '%s': %s", stage, e)
