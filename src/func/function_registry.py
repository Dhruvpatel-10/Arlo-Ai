# function_registry.py
import re
import os
import json
import aiofiles
from typing import Dict, Any, List, Tuple
from common.config import FUNC_CACHE_DIR
from common.logger import setup_logging
from groq import AsyncGroq

groq_api = os.getenv("GROQ_FUNC_CALL_API")
logger = setup_logging()

class FunctionRegistryAndCaller:
    def __init__(self, cache_file=FUNC_CACHE_DIR):
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.patterns: Dict[str, re.Pattern] = {}
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.cache_file = cache_file

    @classmethod
    async def create(cls, cache_file=FUNC_CACHE_DIR):
        self = cls(cache_file)
        await self.load_data()
        return self

    async def load_data(self):
        try:
            async with aiofiles.open(self.cache_file, 'r') as f:
                content = await f.read()
                if content.strip():  # Ensure the file isn't empty
                    data = json.loads(content)
                    for function in data.get("functions", []):
                        self.register(function["name"], function["description"], function.get("pattern", ""))
                    self.cache = data.get("cache", {})
                else:
                    logger.warning(f"Cache file {self.cache_file} is empty.")
        except FileNotFoundError:
            logger.error(f"Cache file not found: {self.cache_file}")
            self.cache = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error loading data: {e}")
            self.cache = {}

    def register(self, name: str, description: str, pattern: str):
        self.functions[name] = {"description": description, "pattern": pattern}
        self.patterns[name] = re.compile(pattern, re.IGNORECASE)

    def get_function_descriptions(self) -> List[Dict[str, str]]:
        return [{"name": name, "description": info["description"], "pattern": info["pattern"]} 
                for name, info in self.functions.items()]

    async def save_cache(self):
        try:
            logger.info(f"Saving cache to {self.cache_file}")
            async with aiofiles.open(self.cache_file, 'w') as f:
                cache_data = {
                    "functions": self.get_function_descriptions(),
                    "cache": self.cache
                }
                await f.write(json.dumps(cache_data, indent=4))
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def rule_based_call(self, prompt: str) -> str:
        if prompt in self.cache:
            logger.info(f"RETURNING FROM CACHE {prompt}")
            return self.cache[prompt]
        
        for name, pattern in self.patterns.items():
            if pattern.search(prompt):
                return name

        return "Pass to the LLM"

    async def llm_based_call(self, prompt: str) -> str:
        sys_msg = '''You are an AI assistant tasked with selecting exactly one action from this list based on the user's input: capture_webcam, extract_clipboard, take_screenshot, open_word, open_excel, open_powerpoint, open_browser, None. Respond with only one action word, exactly as listed. Choose 'open_browser' for any request to open a specific website, search engine, or platform. Respond with 'None' if no action clearly applies. You are not allowed to return any action that is not on the list. If the input does not explicitly map to an action in the list, return 'None.' Your response must contain exactly one word from the list. And also know that user prompt is forwarded to LLM any way so if the prompt is like a LLM can answer it then return 'None'. 
            '''
        function_convo = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]

        # Instantiate the async Groq client
        groq_client = AsyncGroq(api_key=groq_api)

        try:
            # Call the async chat completion API
            chat_completion = await groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=function_convo,
                temperature=0.1,
                top_p=0.1,
                max_tokens=50
            )

            response = chat_completion.choices[0].message.content.strip()
            logger.info(f"Response from Function LLM: {response}")
            if not response:
                raise ValueError("Empty response from LLM")
            
            self.cache[prompt] = response
            await self.save_cache() 
            return response
        
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "None"

    async def call(self, prompt: str) -> str:
        try:            
            rule_based_result = self.rule_based_call(prompt)
            logger.info(f"Rule-based result: {rule_based_result}")
            
            if rule_based_result != "Pass to the LLM":
                return rule_based_result
            
            llm_result = await self.llm_based_call(prompt)  # Awaiting LLM-based call
            logger.info(f"LLM-based result: {llm_result}")
            return llm_result
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return "None"
