import logging
from functools import wraps

from pyrogram.errors import FloodWait

from .etc import thread, wait_flood

# Enable logging
logger = logging.getLogger(__name__)


def retry(func):
    # FloodWait retry
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = None
        while True:
            try:
                result = func(*args, **kwargs)
            except FloodWait as e:
                wait_flood(e)
            except Exception as e:
                logger.warning(f"Retry error: {e}", exc_info=True)
                break
            else:
                break
        return result
    return wrapper


def threaded(daemon: bool = True):
    # Run with thread
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return thread(func, args, kwargs, daemon)
        return wrapper
    return decorator
