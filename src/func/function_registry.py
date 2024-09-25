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
        self.functions[name] = {"description": description}
        self.patterns[name] = re.compile(pattern, re.IGNORECASE)

    def get_function_descriptions(self) -> List[Dict[str, str]]:
        return [{"name": name, "description": info["description"]} 
                for name, info in self.functions.items()]

    def load_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                self.cache = data.get("cache", {})
                for function in data.get("functions", []):
                    self.register(function["name"], function["description"], function["pattern"])
        except FileNotFoundError:
            self.cache = {}

    def save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump({"functions": self.get_function_descriptions(), "cache": self.cache}, f, indent=4)

class HybridFunctionCaller:
    def __init__(self, registry: FunctionRegistry):
        self.registry = registry

    def rule_based_call(self, prompt: str) -> Tuple[str, float]:
        for name, pattern in self.registry.patterns.items():
            if pattern.search(prompt):
                return name, 1.0  # High confidence for exact matches

        # Check the cache if the prompt was previously processed
        if prompt in self.registry.cache:
            print(f"Using cached result for {prompt}")
            return self.registry.cache[prompt]  # Return cached result

        return "None", 0.0

    def llm_based_call(self, prompt: str) -> Tuple[str, float]:
        # Check cache first
        if prompt in self.registry.cache:
            return self.registry.cache[prompt] 

        # System message guiding the LLM
        sys_msg = (
            "You are an AI assistant responsible for selecting the most appropriate action "
            "based on the user's prompt. Use the following guidelines:\n"
            "- 'capture_webcam': Choose only if the user explicitly requests visual input or mentions needing the camera.\n"
            "- 'extract_clipboard': Select if the user refers to copied text or content from the clipboard.\n"
            "- 'take_screenshot': Choose if the user clearly mentions or implies needing to capture screen content.\n"
            "- 'None': Return if none of the above conditions are met.\n"
            "Respond with the function call using the provided schema."
        )

        # Messages to send to the LLM
        function_convo = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]

        # Call the LLM using GroqChat
        chat_completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",  # Use the appropriate model for GroqChat
            messages=function_convo,
        )

        response = chat_completion.choices[0].message.content.strip()
        print(response)
        # Extract the function call from the response
        try:
            if not response:
                raise ValueError("Empty response from LLM")

            selected_action = response
            confidence = 0.9  # Default high confidence for structured LLM responses
            
            # Cache the result
            self.registry.cache[prompt] = (selected_action, confidence)
            self.registry.save_cache()  # Save cache after updating
            
            return selected_action, confidence
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return "None", 0.0
        except ValueError as ve:
            print(ve)
            return "None", 0.0

    def call(self, prompt: str) -> Tuple[str, float]:
        if len(prompt.split()) <= 3:
            rule_based_result = self.rule_based_call(prompt)
            if rule_based_result[0] != "None":
                return rule_based_result
            
        rule_based_result = self.rule_based_call(prompt)
        
        if rule_based_result[0] != "None":
            return rule_based_result
        
        llm_result, llm_confidence = self.llm_based_call(prompt)
        
        if llm_confidence > 0.7:  # Adjust this threshold as needed
            return llm_result
        
        return "None", 0.0  # If neither method is confident
