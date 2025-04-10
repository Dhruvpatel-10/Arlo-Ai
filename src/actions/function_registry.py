# function_registry.py
import re
import os
from typing import Dict, Any, Tuple
from src.utils.logger import setup_logging
from src.utils.config import FUNC_LLM_MODEL
from groq import AsyncGroq

logger = setup_logging()

class FunctionRegistry:
    def __init__(self):
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.patterns: Dict[str, re.Pattern] = {}
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.func_api_key = os.getenv("GROQ_FUNC_CALL_API")

    async def llm_based_call(self, prompt: str) -> str:
        sys_msg = '''
        You are an AI assistant tasked with selecting exactly one action from this list based on the user's input: capture_webcam, extract_clipboard, take_screenshot, open_word, open_excel, open_powerpoint, open_browser, None. Use capture_webcam when the user wants to capture a photo from their webcam or asks something like how they look or what’s behind them. Use extract_clipboard when the user wants to extract text from their clipboard. Use take_screenshot when the user wants to take a screenshot of their screen. Use open_word when the user wants to open Microsoft Word. Use open_excel when the user wants to open Microsoft Excel. Use open_powerpoint when the user wants to open Microsoft PowerPoint. Use web_search for retrieving the latest general information based on a query. Use news_search for searching news-related content. Use open_browser when the user wants to open a specific website, search engine, or platform. Choose open_browser only when explicitly asked to open a specific website or platform. Use web_search when the user asks for the latest information about a general topic. Use news_search when the user asks for the latest news. Return None if no action clearly applies or if the request can be answered directly by an LLM. Do not return any action not listed. Your response must contain exactly one word from the list, with no extra text.
            '''
        function_convo = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]

        # Instantiate the async Groq client
        groq_client = AsyncGroq(api_key=self.func_api_key)

        try:
            # Call the async chat completion API
            chat_completion = await groq_client.chat.completions.create(
                model=FUNC_LLM_MODEL,
                messages=function_convo,
                temperature=0.1,
                top_p=0.1,
                max_tokens=50
            )

            response = chat_completion.choices[0].message.content.strip()
            logger.info(f"Response from Function LLM: {response}")
            if not response:
                raise ValueError("Empty response from LLM")
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "None"

    async def call(self, prompt: str) -> str:
        try:            
            llm_result = await self.llm_based_call(prompt)
            logger.info(f"LLM-based result: {llm_result}")
            return llm_result
        except Exception as e:
            logger.error(f"Error: {e}")
            return "None"
