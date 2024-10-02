import re
import os
import json
from typing import Dict, Any, List, Tuple
from common.config import CACHE_DIR
from common.logger import logger
from groq import Groq
from dotenv import load_dotenv;load_dotenv()


groq_api = os.getenv("GROQ_API_FUNC")
os.makedirs(CACHE_DIR, exist_ok=True)
c_dir = os.path.join(CACHE_DIR, 'function_cache.json')

class FunctionRegistry:
    def __init__(self, cache_file=c_dir):
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.patterns: Dict[str, re.Pattern] = {}
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.cache_file = cache_file
        self.load_data()

    def load_data(self):
        try:
            logger.info(f"Loading data from {self.cache_file}")
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                # Load and register functions
                for function in data.get("functions", []):
                    self.register(function["name"], function["description"], function.get("pattern", ""))
                # Load cache
                self.cache = data.get("cache", {})

        except FileNotFoundError:
            logger.error(f"Cache file not found: {self.cache_file}")
            self.cache = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error loading data: {e}")

    def register(self, name: str, description: str, pattern: str):
        # Store both description and pattern in self.functions
        self.functions[name] = {"description": description, "pattern": pattern}
        self.patterns[name] = re.compile(pattern, re.IGNORECASE)

    def get_function_descriptions(self) -> List[Dict[str, str]]:
        # Include pattern in the function descriptions
        return [{"name": name, "description": info["description"], "pattern": info["pattern"]} 
                for name, info in self.functions.items()]

    def save_cache(self):
        # Save both functions and cache to the cache_file
        logger.info(f"Saving cache to {self.cache_file}")
        with open(self.cache_file, 'w') as f:

            json.dump({"functions": self.get_function_descriptions(), "cache": self.cache}, f, indent=4)


class HybridFunctionCaller:
    def __init__(self, registry: FunctionRegistry):
        self.registry = registry

    def rule_based_call(self, prompt: str) -> str:
        # Check cache first
        if prompt in self.registry.cache:
            logger.info(f"RETURNING FROM CACHE {prompt}")
            return self.registry.cache[prompt] 
        
        for name, pattern in self.registry.patterns.items():
            if pattern.search(prompt):
                return name 

        # Check the cache if the prompt was previously processed
        if prompt in self.registry.cache:
            return self.registry.cache[prompt]  # Return cached result

        return "Pass to the LLM"

    def llm_based_call(self, prompt: str) -> str:

        # System message guiding the LLM
        sys_msg = (
            '''You are an AI assistant tasked with selecting exactly one action from this list based on the user's input: capture_webcam, extract_clipboard, take_screenshot, open_word, open_excel, open_powerpoint, open_browser, None. Respond with only one action word, exactly as listed. Choose 'open_browser' for any request to open a specific website, search engine, or platform like YouTube. Respond with 'None' if no action clearly applies. You are not allowed to return any action that is not on the list. If the input does not explicitly map to an action in the list, return 'None.' Your response must contain exactly one word from the list. And also know that user prompt is forwarded to LLM any way so if the prompt is like a LLM can answer it then return 'None'. 
            '''
        )

        # Messages to send to the LLM
        function_convo = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]

        # Call the LLM using GroqChat
        groq_client = Groq(api_key=groq_api)
        chat_completion =  groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # Use the appropriate model for GroqChat
            messages=function_convo,
            temperature=0.1,
            max_tokens=50
        )

        response = chat_completion.choices[0].message.content.strip()
        # Extract the function call from the response
        try:
            if not response:
                raise ValueError("Empty response from LLM")

            selected_action = response
            # Cache the result
            self.registry.cache[prompt] = (selected_action)
            self.registry.save_cache()  # Save cache after updating
            
            return selected_action
        except ValueError as ve:
            print(ve)
            logger.error(f"Error: {ve}")
            return "None"

    def call(self, prompt: str) -> str:
        try:            
            rule_based_result = self.rule_based_call(prompt)
            logger.info(f"Rule-based result: {rule_based_result}")
            
            if rule_based_result != "Pass to the LLM":
                return rule_based_result
            
            llm_result = self.llm_based_call(prompt)
            logger.info(f"LLM-based result: {llm_result}")
            return llm_result
        
        except Exception as e:
            print(e)
            logger.error(f"Error: {e}")
            return "None"