# file: data_schema.py
from typing import TypedDict, List
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal
from src.utils.helpers import TextUtils
from src.utils.logger import setup_logging

class ClassificationResult(TypedDict):
    id: str
    text: str
    classification: Literal['tool', 'conversation']

logger = setup_logging(module_name="DataManager")

@dataclass
class DataManager:
    """Manages the consistent storage and retrieval of classification results."""

    file_path: Path

    def save_result(self, text_id: str, prompt: str, classification: str) -> None:
        """Create and save a new classification result."""
        new_entry = ClassificationResult(
            id=text_id,
            text=prompt.strip(),
            classification=classification
        )

        data = self.load_data()
        data.append(new_entry)

        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Successfully saved classification result for prompt: {prompt[:30]}")
        except Exception as e:
            logger.error(f"Error saving classification result for prompt: {prompt[:30]} - {str(e)}")

    def load_data(self) -> List[ClassificationResult]:
        """Load existing classification results or initialize empty list."""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading data: {str(e)}, initializing empty list")
            return []

    def find_in_cache(self, prompt_ID: str) -> ClassificationResult | None:
        """
        Check if a prompt is already classified and return the classification result.
        If not found, return None
        """
        try:
            data = self.load_data()
            for entry in data:
                if entry["id"] == prompt_ID:
                    logger.info(f"Classification found in cache for Text: {entry['text']}")
                    return entry['classification']
            logger.info(f"No classification found in cache for Text: {entry['text']}")
            return None
        except Exception as e:
            logger.error(f"Error accessing cache for Text: {entry['text']} - {str(e)}")
            return None
    
if __name__ == "__main__":
    dm = DataManager(file_path="data/cache/prompt_classification_cache.json")
    prompt = "    Check today's weather in Mumbai.    "
    id = TextUtils.generate_id(prompt)
    result = dm.find_in_cache(id)
    print(result)
    print(type(result))