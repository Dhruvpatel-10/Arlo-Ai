import os
import json
from typing import Optional, Dict, Any
from groq import Groq
from pydantic import BaseModel
from src.utils.config import PROMPT_CLASSIFER_PATH, LLM_PROMPT_CLASSIFIER_MODEL
from src.utils.logger import setup_logging
from src.tool_classifier.classifier_helper.data_schema import DataManager

class CLASSIFIER_DATA(BaseModel):
    """Pydantic model for classification results."""
    classification: str  # "tool" or "conversation"
    confidence: float  # Between 0 and 1

    @property
    def as_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "classification": self.classification,
            "confidence": self.confidence
        }

class LLM_CLASSIFIER:
    def __init__(self) -> None:
        """Initialize the LLM Classifier."""
        self.logger = setup_logging(module_name="LLM_Classifier")
        self.prompt_json_cache = PROMPT_CLASSIFER_PATH
        self._initialize_groq_client()
        self.data_manager = DataManager(file_path=self.prompt_json_cache)
        
    def _initialize_groq_client(self) -> None:
        """Initialize the Groq client with API key."""
        self.groq_api = os.getenv("GROQ_URL")
        if not self.groq_api:
            raise ValueError("GROQ_URL environment variable not set")
        self.groq = Groq(api_key=self.groq_api)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        
        base_prompt = """You are a prompt classifier. Categorize queries as either 'tool' or 'conversation' with a confidence score.
        - 'tool': Queries that request specific actions, manipulations, or information about code/tools
        - 'conversation': General discussion, opinions, or non-tool-related queries
        Provide confidence between 0.0 and 1.0"""
        return base_prompt + f" The JSON object must use the schema: {json.dumps(CLASSIFIER_DATA.model_json_schema(), indent=2)}"
    
    def _get_llm_response(self, query: str) -> Any:
        """Get response from Groq LLM.
        
        Args:
            query: The text to classify
            
        Returns:
            Raw LLM response
        """
        system_prompt = self._get_system_prompt()
        response = self.groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
            model=LLM_PROMPT_CLASSIFIER_MODEL,
            temperature=0.2,
            max_completion_tokens=100,
            stream=False,
            response_format={"type": "json_object"},
        )
        return CLASSIFIER_DATA.model_validate_json(response.choices[0].message.content)
    
    def _get_classification(self, query: str) -> Optional[CLASSIFIER_DATA]:
        """
        Classifies a user query as either 'tool' or 'conversation' using a Groq LLM.

        Args:
            query: The user input text to classify
            
        Returns:
            CLASSIFIER_DATA object containing classification and confidence score,
            or None if classification fails
        """
        try:
            chat_completion = self._get_llm_response(query)
            self.logger.info(f"LLM Classification: {chat_completion.classification} (confidence: {chat_completion.confidence:.2f})")
            return chat_completion.classification
        except Exception as e:
            self.logger.error(f"Classification failed for query: {query[:50]}... Error: {str(e)}")
            return None    

    def handle_llm_classification(self, prompt_ID: str, query: str) -> Optional[str]:
        """Handle the classification process and save results.
        
        Args:
            query: Text to classify
            text_id: Optional identifier for the text
            
        Returns:
            str: Classification result if successful, None otherwise
        """
        llm_result = self._get_classification(query=query)
        
        if llm_result is not None:
            self.data_manager.save_result(text_id=prompt_ID,prompt=query, classification=llm_result)
            return llm_result
        return None

if __name__ == '__main__':
    from dotenv import load_dotenv; load_dotenv()
    prompt = "I'm thinking about a book I read where the main character uses voice commands to control their smart home. Would that kind of technology work well in real life? Have you ever tried using voice assistants yourself?"

    llm = LLM_CLASSIFIER()
    result = llm._get_classification(prompt)
    print(result)
    print(type(result))