import os
import time
import asyncio
from functools import wraps
from difflib import SequenceMatcher
from typing import List, Optional
from datetime import datetime
from src.utils.logger import setup_logging
import validators
from email_validator import validate_email, EmailNotValidError

logger = setup_logging()

class TimeUtils:
    """Time-related utility functions."""
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
            
        return " ".join(parts)

class FileUtils:
    """File handling utility functions."""
    
    @staticmethod
    def ensure_dir(directory: str) -> bool:
        """Ensure a directory exists, create if it doesn't."""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Directory creation error: {str(e)}")
            return False

    @staticmethod
    def safe_filename(filename: str) -> str:
        """Convert string to safe filename."""
        # Replace spaces with underscores and remove special characters
        safe_name = "".join(c for c in filename.replace(" ", "_") 
                          if c.isalnum() or c in "._-")
        return safe_name

    @staticmethod
    def get_file_size(file_path: str) -> Optional[str]:
        """Get human-readable file size."""
        try:
            size = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.1f}TB"
        except Exception as e:
            logger.error(f"File size error: {str(e)}")
            return None

class TextUtils:
    """Text processing utility functions."""
    
    @staticmethod
    def truncate(text: str, max_length: int = 100) -> str:
        """Truncate text to specified length with ellipsis."""
        return text[:max_length] + "..." if len(text) > max_length else text

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text using simple regex."""
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)

class ValidationUtils:
    """Input validation utility functions."""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address format."""
        try:
        # Validate and normalize the email
            validate_email(email)
            return True
        except EmailNotValidError as e:
            logger.error(f"Invalid email: {e}")
            return False

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format with error handling."""
        try:
            return validators.url(url)
        except validators.ValidationError as e:
            logger.error(f"URL validation error: {str(e)}")
            return False

class FuzzyCache:
    def __init__(self, similarity_threshold=0.85, ttl=3600):
        self.cache = {}
        self.similarity_threshold = similarity_threshold
        self.ttl = ttl

    def find_similar_prompt(self, prompt: str):
        normalized = prompt.lower().strip()
        for cached_prompt in self.cache:
            similarity = SequenceMatcher(None, normalized, cached_prompt.lower()).ratio()
            logger.debug(f"Comparing:\n  New: '{prompt}'\n  Cached: '{cached_prompt}'\n  Similarity: {similarity:.2f}")
            if similarity >= self.similarity_threshold:
                return cached_prompt, similarity
        return None

    def fuzzy_cached(self, func):
        @wraps(func)
        async def wrapper(prompt: str, *args, **kwargs):
            now = time.time()
            # Clean expired entries
            self.cache = {k: v for k, v in self.cache.items() if now - v[1] < self.ttl}

            # Check for similar prompt
            similar = self.find_similar_prompt(prompt)
            if similar:
                cached_prompt, similarity = similar
                result, _ = self.cache[cached_prompt]
                logger.debug(f"Cache hit for prompt '{prompt}' (similarity: {similarity:.2f})")
                return result

            # Execute function if no cache hit
            result = await func(prompt, *args, **kwargs)
            self.cache[prompt] = (result, now)
            return result
        return wrapper

def retry(max_attempts: int = 3, delay: float = 0.4):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt+1} failed for {func.__name__}: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)
            logger.error(f"All retry attempts failed for {func.__name__}: {last_error}")
            raise last_error
        return wrapper
    return decorator
