import os
import time
import asyncio
import hashlib
import json
import validators
import inspect
from difflib import SequenceMatcher
from typing import List, Optional
from collections import OrderedDict
from datetime import datetime
from functools import wraps
from src.utils.logger import setup_logging
from email_validator import validate_email, EmailNotValidError

logger = setup_logging(module_name="Helpers")

class GenericUtils:
    @staticmethod
    def caller_info(skip_one_more: bool = False):
        """
        Get the filename and line number of the caller function.

        Returns:
            str: The caller filename and line number
        """
        stack = inspect.stack()
        depth = 2 if skip_one_more else 1

        for frame_info in stack[depth:]:  # Start from the selected depth
            # Skip frames from internal runpy and our own helpers module
            if "runpy" in frame_info.filename or "helpers.py" in frame_info.filename:
                continue
            return f"{GenericUtils.shorten_path(frame_info.filename)}:{frame_info.lineno}"
        return "Unknown caller"
    
    @staticmethod
    def retry(func=None, *, max_attempts=3, delay=0.4):
        """
        Decorator to retry a function multiple times on failure.

        :param func: The function to decorate
        :param max_attempts: The maximum number of attempts to make
        :param delay: The amount of time to wait between attempts
        :return: The decorated function

        Example usage:

        @retry
        async def do_something():
            # try to do something that may fail
            pass

        This will retry the function up to 3 times with a 0.4 second delay between attempts.
        """
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
        
        # This is the key part that allows @retry to work without parentheses
        if func is not None:
            return decorator(func)
        return decorator

    @staticmethod
    def shorten_path(full_path: str, project_name="Arlo-Ai") -> str:
        parts = full_path.split(os.sep)  # Split path by OS separator (/ or \)
        
        if project_name in parts:
            index = parts.index(project_name)
            return os.sep.join(parts[index + 1:])  # Join parts after "Arlo-Ai"
        
        return full_path    

class TimeUtils:
    """Time-related utility functions."""
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to a human-readable string."""
        if seconds < 1:
            return f"{seconds:.3g}s"  # 3 significant digits for small times
        
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

    @staticmethod
    def clear_json_with_backup(json_path: str):
        """
        Create a backup of the JSON file before clearing it.
        The backup file will have a .bak extension and will overwrite the previous backup.
        """
        try:
            # Define backup file path
            backup_path = str(json_path) + ".bak"
            caller_info = GenericUtils.caller_info()
            # Check if the original file exists before renaming
            if os.path.exists(json_path):
                os.replace(json_path, backup_path)  # Overwrite previous backup
            
            # Clear the JSON file by creating a new empty one
            with open(json_path, "w") as f:
                json.dump([], f)

            logger.info(f"JSON file cleared and backup created at {GenericUtils.shorten_path(backup_path)} by {caller_info}")
        
        except Exception as e:
            logger.error(f"JSON file clear error: {str(e)} by {caller_info}")

    @staticmethod
    def append_to_json(cache_file_path: str, entry_dict: dict):
        """
        Appends a new entry to the specified JSON file.

        If the file does not exist, it will be created. If the file exists but is not valid JSON,
        it will be reset to an empty list.

        Args:
            cache_file_path (str): The path to the JSON file.
            entry_dict (dict): The new entry to append to the list.

        Returns:
            None
        """
        try:
            # Load existing data if the file exists and is valid JSON
            if os.path.exists(cache_file_path) and os.path.getsize(cache_file_path) > 0:
                with open(cache_file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        if not isinstance(data, list):
                            data = []  # Reset if it's not a list
                    except json.JSONDecodeError:
                        data = []  # Reset if file is corrupted
            else:
                data = []

            # Append the new entry
            data.append(entry_dict)

            # Write back to the file
            with open(cache_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            caller_id = GenericUtils.caller_info()
            logger.info(f"Successfully appended new entry to {GenericUtils.shorten_path(cache_file_path)} by {caller_id}")
        except Exception as e:
            caller_id = GenericUtils.caller_info()
            logger.error(f"JSON file append error: {str(e)} || {caller_id}")

class TextUtils:
    """Text processing utility functions."""
    
    @staticmethod
    def truncate(text: str, max_length: int = 50) -> str:
        """Truncate text to specified length with ellipsis."""
        return text[:max_length] + "..." if len(text) > max_length else text

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text using simple regex."""
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def generate_id(text: str) -> str:
        """
        Generates a unique, consistent ID based on the query text.

        The ID is a 32-character hexadecimal string that is computed using
        the BLAKE2b hash function.

        Args:
            text (str): The input text to generate an ID for.

        Returns:
            str: A unique, consistent ID for the given text.
        """
        return hashlib.blake2b(text.strip().encode(), digest_size=32).hexdigest()
    

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
    cache = OrderedDict()  # Maintains LRU order globally
    similarity_threshold = 0.85
    ttl = 3600
    max_size = 100
    cache_lock = asyncio.Lock()  # Ensures thread safety
    normalized_keys = []  # Faster lookup for fuzzy matches

    @classmethod
    def _find_similar_prompt(cls, prompt: str):
        normalized = prompt.lower().strip()
        for index, cached_prompt in enumerate(cls.normalized_keys):
            similarity = SequenceMatcher(None, normalized, cached_prompt).ratio()
            if similarity >= cls.similarity_threshold:
                return list(cls.cache.keys())[index], similarity  # Return original key
        return None

    @classmethod
    async def _clean_expired(cls):
        """ Periodically removes expired cache items to prevent slowdowns. """
        now = time.time()
        async with cls.cache_lock:
            expired_keys = [k for k, v in cls.cache.items() if now - v[1] >= cls.ttl]
            for k in expired_keys:
                del cls.cache[k]
                cls.normalized_keys.remove(k.lower())  # Remove from lookup list

    @classmethod
    def fuzzy_cached(cls, func):
        @wraps(func)
        async def wrapper(prompt: str, *args, **kwargs):
            await cls._clean_expired()  # Periodic cleanup

            async with cls.cache_lock:
                similar = cls._find_similar_prompt(prompt)
                if similar:
                    cached_prompt, similarity = similar
                    cached_result, _ = cls.cache[cached_prompt]
                    logger.debug(f"✅ CACHE HIT for '{prompt}' (Matched: '{cached_prompt}', Similarity: {similarity:.2f})")
                    cls.cache.move_to_end(cached_prompt)  # Mark as recently used
                    return cached_result  # Return LLM response

            logger.debug(f"❌ CACHE MISS for '{prompt}' - Calling LLM API...")
            result = await func(prompt, *args, **kwargs)

            async with cls.cache_lock:
                if len(cls.cache) >= cls.max_size:
                    removed_key, _ = cls.cache.popitem(last=False)  # Remove oldest entry
                    cls.normalized_keys.pop(0)  # Remove from lookup list

                cls.cache[prompt] = (result, time.time())  # Store new response
                cls.normalized_keys.append(prompt.lower())  # Store normalized key
            return result
        return wrapper
    