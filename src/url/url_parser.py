import os
import re
import urllib.parse
import json
from typing import Dict, Any, Tuple, Optional
from functools import lru_cache
from dotenv import load_dotenv;load_dotenv()
import groq
from common.config import CACHE_DIR
from src.common.logger import logger

# Define cache directories
U_DIR = os.path.join(CACHE_DIR, 'urls.json')
Q_DIR = os.path.join(CACHE_DIR, 'queries.json')
GROQ_API = os.getenv("GROQ_URL")

class SearchQueryFinder:
    def __init__(self, queries_file: str = Q_DIR, urls_file: str = U_DIR, groq_api_key: str = GROQ_API):
        self.queries = self._load_json(queries_file)
        self.urls = self._load_json(urls_file)
        self.groq_client = groq.Client(api_key=groq_api_key)
        self.PLATFORM_PATTERN = re.compile(r'Platform\s*:\s*(\w+)', re.IGNORECASE)
        self.QUERY_PATTERN = re.compile(r'Query\s*:\s*(.+)', re.IGNORECASE)

    @staticmethod
    @lru_cache(maxsize=32)
    def _load_json(filepath: str) -> Dict:
        """ Efficient JSON loader with caching """
        logger.info(f"Loading {filepath}")
        with open(filepath, 'r') as f:
            return json.load(f)

    def _save_json(self, filepath: str, data: Any):
        logger.info(f"Saving {filepath}")
        """ Efficient JSON saver """
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def find_query(self, prompt: str) -> Optional[str]:
        """
        Finds the platform, query, and constructs the URL based on the prompt.
        If not found in cached queries, it uses LLM for query extraction.
        """
        # Check cached queries first
        cached_result = next((query['action'] for query in self.queries if query['prompt'].lower() == prompt.lower()), None)
        if cached_result:
            logger.info(f"Found cached result: {cached_result}")
            return self._construct_url(cached_result['platform'], cached_result['query'])

        # Call LLM if query not found in cache
        platform, query = self._llm_search(prompt)
        
        # Cache the new result and return the constructed URL
        if platform:
            new_query = {"prompt": prompt, "action": {"platform": platform, "query": query}}
            self.queries.append(new_query)
            self._save_json(Q_DIR, self.queries)
            logger.info(f"Cached new query: {new_query}")
            return self._construct_url(platform, query)

        return None

    def _llm_search(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Use LLM to extract the action. Returns platform and query.
        """
        logger.info(f"LLM searching for PLATFORM AND QUERY...")
        system_prompt = '''
        Objective:
        Extract the search platform and query from user input. If no valid query is found, return 'None' for the query.
        Instructions:
        Detect platforms (e.g., Google, YouTube). Default to "Google" if none specified.
        Extract the query, removing phrases like "search for" or "look up."
        If no valid query exists, set the query to 'None.'
        Return the result in the format:
        Platform: <platform>
        Query: <query or 'None'>
        Example:
        Input: "search Python on YouTube"
        Output:
        Platform: YouTube
        Query: Python
        '''

        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            chat_completion = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=conversation,
            )

            response = chat_completion.choices[0].message.content.strip()

            # Use regex to extract Platform and Query
            platform_match = self.PLATFORM_PATTERN.search(response)
            query_match = self.QUERY_PATTERN.search(response)

            platform = platform_match.group(1).strip().lower() if platform_match else None
            query = query_match.group(1).strip() if query_match and query_match.group(1).lower() != 'none' else None
            logger.info(f"PLATFORM: {platform} | QUERY: {query}")
            return platform, query

        except Exception as e:
            print(f"Error during LLM search: {e}")
            return None, None

    def _construct_url(self, platform: str, query: str, default_search_engine="google") -> str:
        """
        Constructs a search URL for the specified platform and query.
        Falls back to a Google search for the platform if the platform doesn't have a search path.
        """
        platform = platform.lower()
        logger.info(f"Platform: {platform} | Query: {query}")
        url_info = self.urls.get(platform, self.urls[default_search_engine])
        base_url = url_info["base_url"]
        search_path = url_info.get("search_path", "")

        if search_path and query:
            encoded_query = urllib.parse.quote(query)
            logger.info(f"Inside IF Constructed URL: {base_url}{search_path}{encoded_query}")
            return f"{base_url}{search_path}{encoded_query}"
        elif not search_path and query:
            # If there's no search path, use Google to search for "platform query"
            google_url_info = self.urls[default_search_engine]
            google_base_url = google_url_info["base_url"]
            google_search_path = google_url_info["search_path"]
            encoded_query = urllib.parse.quote(f"{platform} {query}")
            logger.info(f"INSIDE ELIF Constructed URL: {google_base_url}{google_search_path}{encoded_query}")
            return f"{google_base_url}{google_search_path}{encoded_query}"
        else:
            logger.info(f"INSIDE ELSE Constructed URL: {base_url}")
            return f"{base_url}"