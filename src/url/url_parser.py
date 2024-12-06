import os
import re
import urllib.parse
import json
from typing import Dict, Any, Tuple, Optional
from functools import lru_cache
import groq
from common.config import URL_DIR, QUERY_DIR
from src.common.logger import setup_logging


GROQ_API = os.getenv("GROQ_URL")
logger = setup_logging()

class SearchQueryFinder:
    def __init__(self, queries_file: str = QUERY_DIR, urls_file: str = URL_DIR, groq_api_key: str = GROQ_API):
        self.queries = self._load_json(queries_file)
        self.urls = self._load_json(urls_file)
        self.groq_client = groq.Client(api_key=groq_api_key)
        self.PLATFORM_PATTERN = re.compile(r'Platform\s*:\s*(\w+)', re.IGNORECASE)
        self.QUERY_PATTERN = re.compile(r'Query\s*:\s*(.+)', re.IGNORECASE)

    @staticmethod
    @lru_cache(maxsize=32)
    def _load_json(filepath: str) -> Dict:
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
            self._save_json(QUERY_DIR, self.queries)
            logger.info(f"Cached new query: {new_query}")
            return self._construct_url(platform, query)

        return None

    def _llm_search(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Use LLM to extract the action. Returns platform and query.
        """
        logger.info(f"LLM searching for PLATFORM AND QUERY...")
        system_prompt = '''
Objective: Detect the search platform (e.g., YouTube, Facebook) from user input. Extract the search query if available. If no search query is specified, return "null" for the query.

Platform Detection:
Identify the platform directly mentioned in the input (e.g., YouTube, Facebook, GitHub, or any website). If no platform is explicitly mentioned, use "Google" as the default platform.

Query Extraction:
Remove phrases such as "search for", "look up", or "find" to extract the core search query. If no valid search query exists, return "null".

Return Format:
Always return the detected platform, even if no query is present. Ensure only this word "null" is returned if no search query is provided.

Expected Return Format:
Platform: <platform> (Do not default to Google if platform is present)
Query: <query> or "null"
Example 1:
Input: "search Python on YouTube"
Output:
    Platform: YouTube
    Query: Python

Example 2:
Input: "open Facebook"
Output:
    Platform: Facebook
    Query: null
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

            if query is not None and query.lower() in ['none', 'null', '']:
                query = None

            logger.info(f"PLATFORM: {platform} | QUERY: {query}")
            return platform, query

        except Exception as e:
            print(f"Error during LLM search: {e}")
            return None, None

    def _construct_url(self, platform: str, query: str, default_search_engine="google") -> str:
        platform = platform.lower()
        logger.info(f"Platform: {platform} | Query: {query}")
        try:
            url_info = self.urls[platform]  
            base_url = url_info["base_url"]
            search_path = url_info.get("search_path")
        except KeyError:
            base_url = None
            search_path = None

        if base_url and search_path and query:
            encoded_query = urllib.parse.quote(query)
            logger.info(f"Constructed URL with search query: {base_url}{search_path}{encoded_query}")
            return f"{base_url}{search_path}{encoded_query}"

        elif base_url and (not search_path or not query):
            # If query is None or search_path is empty, return base_url
            logger.debug(f"Constructed URL with just base URL: {base_url}")
            return base_url

        elif search_path is None:
            # Fallback to Google search
            google_url_info = self.urls.get(default_search_engine)
            if not google_url_info:
                logger.error(f"Default search engine '{default_search_engine}' not configured.")
                return None
            google_base_url = google_url_info["base_url"]
            google_search_path = google_url_info["search_path"]
            encoded_query = urllib.parse.quote(f"{platform} {query or ''}")
            logger.debug(f"Google fallback URL: {google_base_url}{google_search_path}{encoded_query}")
            return f"{google_base_url}{google_search_path}{encoded_query}"

        else:
            logger.error(f"Failed to construct URL: {platform} {query or ''}")
            return None