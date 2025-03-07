from typing import Optional
from src.utils.logger import setup_logging

logger = setup_logging()

class AssistantError(Exception):
    """Base exception class for all assistant-related errors."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        logger.error(f"{self.__class__.__name__}: {message}")
        if original_error:
            logger.error(f"Original error: {str(original_error)}")

    def __str__(self):
        return f"{self.__class__.__name__}: {self.args[0]}"  

class AudioError(AssistantError):
    """Raised when there are issues with audio processing."""
    pass

class STTError(AssistantError):
    """Raised when there are issues with speech-to-text conversion."""
    pass

class TTSError(AssistantError):
    """Raised when there are issues with text-to-speech conversion."""
    pass

class WakeWordError(AssistantError):
    """Raised when there are issues with wake word detection."""
    pass

class LLMError(AssistantError):
    """Raised when there are issues with the language model."""
    pass

class FunctionError(AssistantError):
    """Raised when there are issues with function execution."""
    pass

class ConfigError(AssistantError):
    """Raised when there are issues with configuration."""
    pass

class StateError(AssistantError):
    """Raised when there are issues with state management."""
    pass

class EventBusError(AssistantError):
    """Raised when there are issues with event handling."""
    pass

class AccessKeyError(AssistantError):
    """Raised when there are issues with access key"""
    pass

def handle_assistant_error(func):
    """Decorator for handling assistant errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AssistantError as e:
            # Already logged in the constructor
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return None
    return wrapper

# Error status codes for API responses
ERROR_CODES = {
    'AUDIO_ERROR': 1001,
    'STT_ERROR': 1002,
    'TTS_ERROR': 1003,
    'WAKE_WORD_ERROR': 1004,
    'LLM_ERROR': 1005,
    'FUNCTION_ERROR': 1006,
    'CONFIG_ERROR': 1007,
    'STATE_ERROR': 1008,
    'EVENT_BUS_ERROR': 1009,
    'UNKNOWN_ERROR': 9999
}

def create_error_response(error: AssistantError) -> dict:
    """Creates a standardized error response for API endpoints."""
    error_type = error.__class__.__name__.upper().replace('ERROR', '_ERROR')
    error_code = ERROR_CODES.get(error_type, ERROR_CODES['UNKNOWN_ERROR'])
    
    return {
        'success': False,
        'error': {
            'code': error_code,
            'type': error_type,
            'message': str(error),
            'details': str(error.original_error) if error.original_error else None
        }
    }