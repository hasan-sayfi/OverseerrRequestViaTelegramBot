"""
Error handling utilities for the Overseerr Telegram Bot.
Provides standardized error handling, retry mechanisms, and user-friendly error messages.
"""
import logging
import asyncio
import functools
from typing import Optional, Callable, Any, Tuple
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for bot operations."""
    
    @staticmethod
    def get_user_friendly_message(error: Exception) -> str:
        """Convert technical errors to user-friendly messages."""
        if isinstance(error, Timeout):
            return "⏱️ **Connection timeout.** The server is taking too long to respond. Please try again later."
        
        elif isinstance(error, ConnectionError):
            return "🌐 **Connection failed.** Unable to reach the Overseerr server. Please check your connection."
        
        elif isinstance(error, requests.HTTPError):
            status_code = getattr(error.response, 'status_code', None)
            if status_code == 401:
                return "🔐 **Authentication failed.** Invalid API key or session expired."
            elif status_code == 403:
                return "🚫 **Access denied.** You don't have permission for this action."
            elif status_code == 404:
                return "❓ **Not found.** The requested item could not be found."
            elif status_code == 500:
                return "⚠️ **Server error.** The Overseerr server encountered an internal error."
            else:
                return f"❌ **Request failed** (Error {status_code}). Please try again later."
        
        elif isinstance(error, RequestException):
            return "🔌 **Network error.** Please check your internet connection and try again."
        
        else:
            return "❌ **Unexpected error occurred.** Please try again later."
    
    @staticmethod
    def log_error(operation: str, error: Exception, context: dict = None):
        """Log detailed error information for debugging."""
        context_str = f" Context: {context}" if context else ""
        logger.error(f"Error in {operation}: {type(error).__name__}: {error}{context_str}")
        
        # Log stack trace for unexpected errors
        if not isinstance(error, (RequestException, ValueError, KeyError)):
            logger.exception(f"Unexpected error in {operation}")


def with_retry(max_attempts: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator to add retry logic to functions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each failed attempt
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry certain errors
                    if isinstance(e, (requests.HTTPError,)) and hasattr(e, 'response'):
                        if e.response.status_code in [401, 403, 404]:
                            break
                    
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry certain errors
                    if isinstance(e, (requests.HTTPError,)) and hasattr(e, 'response'):
                        if e.response.status_code in [401, 403, 404]:
                            break
                    
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def safe_api_call(operation: str) -> Callable:
    """
    Decorator for safe API calls with standardized error handling.
    
    Args:
        operation: Description of the operation for logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Tuple[bool, Any, Optional[str]]:
            """
            Returns:
                Tuple of (success: bool, result: Any, error_message: Optional[str])
            """
            try:
                result = func(*args, **kwargs)
                return True, result, None
            except Exception as e:
                ErrorHandler.log_error(operation, e, {"args": args, "kwargs": kwargs})
                user_message = ErrorHandler.get_user_friendly_message(e)
                return False, None, user_message
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Tuple[bool, Any, Optional[str]]:
            """
            Returns:
                Tuple of (success: bool, result: Any, error_message: Optional[str])
            """
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return True, result, None
            except Exception as e:
                ErrorHandler.log_error(operation, e, {"args": args, "kwargs": kwargs})
                user_message = ErrorHandler.get_user_friendly_message(e)
                return False, None, user_message
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator
