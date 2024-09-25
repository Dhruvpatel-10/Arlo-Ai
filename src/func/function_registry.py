import re
import os
import json
from typing import Dict, Any, List, Tuple
from common.config import CACHE_DIR
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

groq_api = os.getenv("GROQ_API_FUNC")
groq_client = Groq(api_key=groq_api)

os.makedirs(CACHE_DIR, exist_ok=True)
c_dir = os.path.join(CACHE_DIR, 'function_cache.json')

class FunctionRegistry:
    def __init__(self, cache_file=c_dir):
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.patterns: Dict[str, re.Pattern] = {}
        self.cache: Dict[str, Tuple[str, float]] = {}  # Cache for LLM results
        self.cache_file = cache_file
        self.load_cache()  # Load cache from file if it exists
        self.load_functions_from_json()

    def load_functions_from_json(self):
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                for function in data.get("functions", []):
                    self.register(function["name"], function["description"], function["pattern"])
                self.cache = data.get("cache", {})
        except FileNotFoundError:
            print(f"{self.cache_file} not found. No functions loaded.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    def register(self, name: str, description: str, pattern: str):
        # Store both description and pattern in self.functions
        self.functions[name] = {"description": description, "pattern": pattern}
        self.patterns[name] = re.compile(pattern, re.IGNORECASE)

    def get_function_descriptions(self) -> List[Dict[str, str]]:
        # Include pattern in the function descriptions
        return [{"name": name, "description": info["description"], "pattern": info["pattern"]} 
                for name, info in self.functions.items()]

    def load_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                self.cache = data.get("cache", {})
                for function in data.get("functions", []):
                    self.register(function["name"], function["description"], function.get("pattern", ""))
        except FileNotFoundError:
            self.cache = {}

    def save_cache(self):
        # Save both functions and cache to the cache_file
        with open(self.cache_file, 'w') as f:
            json.dump({"functions": self.get_function_descriptions(), "cache": self.cache}, f, indent=4)


class HybridFunctionCaller:
    def __init__(self, registry: FunctionRegistry):
        self.registry = registry

    def rule_based_call(self, prompt: str) -> Tuple[str, float]:
        for name, pattern in self.registry.patterns.items():
            if pattern.search(prompt):
                return name # High confidence for exact matches

        # Check the cache if the prompt was previously processed
        if prompt in self.registry.cache:
            return self.registry.cache[prompt]  # Return cached result

        return "None"

    def llm_based_call(self, prompt: str) -> Tuple[str, float]:
        # Check cache first
        if prompt in self.registry.cache:
            return self.registry.cache[prompt] 

        # System message guiding the LLM
        sys_msg = (
            '''You are an AI assistant tasked with selecting exactly one action from this list based on the user's input: capture_webcam, extract_clipboard, take_screenshot, open_word, open_excel, open_powerpoint, open_browser, open_youtube, None.
            Respond with only one action word, exactly as listed. Choose 'None' if no action clearly applies.
            Key rules:
            Select 'open_browser' only for explicit requests to open a web browser or search engine.
            Choose 'open_youtube' only for direct YouTube-related requests.
            For general information queries or topics not requiring a specific action, select 'None'.
            Do not infer actions. Only select an action if explicitly requested or clearly implied.
            Respond with the single chosen action word only. No explanations or additional text.
            Your entire response must be one word from the list or 'None'.'''
        )

        # Messages to send to the LLM
        function_convo = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]

        # Call the LLM using GroqChat
        chat_completion = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # Use the appropriate model for GroqChat
            messages=function_convo,
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
            return "None"

    def call(self, prompt: str) -> Tuple[str, float]:
        if len(prompt.split()) < 3:
            rule_based_result = self.rule_based_call(prompt)
            if rule_based_result[0] != "None":
                return rule_based_result
            
        rule_based_result = self.rule_based_call(prompt)
        
        if rule_based_result != "None":
            return rule_based_result
        
        llm_result = self.llm_based_call(prompt)
        
        if llm_result != "None":
            return llm_result
        
        return "None"  # If neither method is confident
