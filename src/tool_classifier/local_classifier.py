import asyncio
import chromadb
import time
import numpy as np
import os
from typing import List, Tuple, Dict, Any, Union
from sentence_transformers import SentenceTransformer
from src.tool_classifier.classifier_helper.data_schema import DataManager, ClassificationResult
from src.utils.config import PROMPT_CLASSIFER_PATH, CLASSIFIER_MODEL, CHROMADB_PATH
from src.utils.helpers import FileUtils, TimeUtils
from huggingface_hub import snapshot_download
from sklearn.metrics.pairwise import cosine_similarity
from src.utils.logger import setup_logging

class LOCAL_CLASSIFIER:
    def __init__(self, cosine_threshold: float = 0.4) -> None:
        """Initialize the Query Classifier with the specified threshold.
        
        Args:
            cosine_threshold: Similarity threshold for classification (default: 0.4)
        """
        self.logger = setup_logging(module_name="Query_Classifier")
        self.prompt_json_cache = PROMPT_CLASSIFER_PATH
        self.chromadb_path = CHROMADB_PATH
        self.classifier_model = CLASSIFIER_MODEL
        self.cosine_threshold = cosine_threshold

        # Initialize core components
        self.model = None
        self.db_connected = None
        self.collection_chromadb = None
        self.data_manager = DataManager(PROMPT_CLASSIFER_PATH)
        self.file_change_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize and return the sentence transformer model."""
        self._download_model()

        model_init_task = asyncio.create_task(self._load_model())

        db_init_task = asyncio.create_task(self._load_db())

        await asyncio.gather(model_init_task, db_init_task)
        
        self.collection_chromadb = self.db_connected.get_or_create_collection(name="prompt_embeddings")

    async def _load_model(self):
        self.model = SentenceTransformer(model_name_or_path=str(self.classifier_model), device='cpu')
        return

    async def _load_db(self):
        self.db_connected = chromadb.PersistentClient(path=str(self.chromadb_path))
        return
    
    def _download_model(self, repo_id: str = 'sentence-transformers/all-MiniLM-L6-v2') -> bool:
        """Download the model if it doesn't exist locally.
        
        Args:
            repo_id: HuggingFace model repository ID
            
        Returns:
            bool: True if download was needed and successful, False if model already exists
        """
        if os.path.exists(self.classifier_model) and os.listdir(self.classifier_model):
            return False
            
        self.logger.info("Downloading the classifier model...")
        snapshot_download(
            repo_id=repo_id,
            local_dir=self.classifier_model
        )
        self.logger.info("Classifier model downloaded successfully.")
        return True

    async def update_chromadb(self, json_path: str = PROMPT_CLASSIFER_PATH) -> Union[bool, int]:
        """Update ChromaDB with new data from JSON file.
        
        Args:
            json_path: Path to JSON file containing new data
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        async with self.file_change_lock:
            try:
                new_data = self.data_manager.load_data()
                if not new_data:
                    self.logger.warning("No new data to add.")
                    return True

                # Get existing IDs and prepare new data
                existing_ids = self._get_existing_ids()
                texts_to_add, classifications_to_add, new_ids = self._prepare_new_data(new_data, existing_ids)

                if not texts_to_add:
                    self.logger.warning(f"No new items in file: {json_path}.")
                    FileUtils.clear_json_with_backup(json_path)
                    return True

                # Compute and store embeddings
                embeddings = self._compute_embeddings(texts_to_add)
                self._store_embeddings(texts_to_add, classifications_to_add, new_ids, embeddings)
                
                FileUtils.clear_json_with_backup(json_path)
                return new_ids.count()

            except Exception as e:
                self.logger.error(f"Error during ChromaDB update: {str(e)}")
                return False

    def _get_existing_ids(self) -> set:
        """Retrieve only existing IDs from ChromaDB efficiently."""
        if self.collection_chromadb.count() == 0:
            return set()

        result = self.collection_chromadb.get(include=["metadatas"])  # Fetching minimal data
        return set(result["ids"]) if "ids" in result else set()  # Extracting only IDs
 
    
    def _prepare_new_data(self, new_data: List[Dict[str, Any]], existing_ids: set) -> Tuple[List[str], List[str], List[str]]:
        """Prepare new data for adding to ChromaDB."""
        texts_to_add = []
        classifications_to_add = []
        new_ids = []

        for item in new_data:
            if item["id"] not in existing_ids:
                texts_to_add.append(item["text"])
                classifications_to_add.append(item["classification"])
                new_ids.append(item["id"])

        return texts_to_add, classifications_to_add, new_ids

    def _compute_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for the given texts."""
        start_time = time.time()
        embeddings = self.model.encode(texts, convert_to_numpy=True).tolist()
        embedding_time = time.time() - start_time
        self.logger.info(f"Embedding time: {embedding_time:.4f} seconds for {len(texts)} items")
        return embeddings

    def _store_embeddings(self, texts: List[str], classifications: List[str], 
                         ids: List[str], embeddings: List[List[float]]) -> None:
        """Store embeddings and metadata in ChromaDB."""
        self.collection_chromadb.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=[{"text": text, "classification": cls} 
                      for text, cls in zip(texts, classifications)]
        )
        self.logger.info("New embeddings stored in ChromaDB successfully")

    async def classify_query_locally(self, prompt_ID: str, query: str) -> Union[ClassificationResult, bool]:
        """Classify a query using the local model and ChromaDB.        
        Args:
            prompt_ID: The ID of the prompt
            query: The text to classify
            
        Returns:
            Optional[ClassificationResult]: Classification result if successful, None otherwise
        """
        st = time.time()
    
    # Get existing IDs
        existing_ids = self._get_existing_ids()
        
        # If prompt_ID exists, get the classification directly
        if prompt_ID in existing_ids:
            # Fetch only the document with the matching prompt_ID
            result = self.collection_chromadb.get(ids=[prompt_ID], include=["metadatas"])

            if result and result["metadatas"]:
                classification = result["metadatas"][0].get("classification")
                self.logger.info(f"Found existing classification for Query in DB: {query}, Classification: {classification} | Retrival time: {TimeUtils.format_duration(time.time() - st)}")

                return classification

        print("== TRYING QUERY ==")
        start = time.time()
        query_embedding = self.model.encode(query, convert_to_numpy=True).reshape(1, -1)
        # Search in ChromaDB
        results = self.collection_chromadb.query(
            query_embeddings=[query_embedding.flatten().tolist()],
            n_results=1,
            include=["embeddings", "metadatas"]
        )

        retrieval_time = time.time() - start
        retrieval_time = TimeUtils.format_duration(retrieval_time)

        if results["ids"][0]:

            best_match = results["metadatas"][0][0]
            stored_embedding = np.array(results["embeddings"][0][0]).reshape(1, -1)
            cosine_sim = cosine_similarity(query_embedding, stored_embedding)[0][0]

            if cosine_sim < self.cosine_threshold:
                self.logger.info(f"Query: '{query}'")
                self.logger.info(f"This is not a match | best match: '{best_match['text']}', Classification: '{best_match['classification']}' | cosine similarity: {cosine_sim:.4f} | Retrieval time: {retrieval_time}")
                return None
            else:
                self.logger.info(f"Query: '{query}'")
                self.logger.info(f" - Matched: '{best_match['text']}', Classification: '{best_match['classification']}'")
                self.logger.info(f" - Cosine similarity: {cosine_sim:.4f}, Retrieval time: {retrieval_time} seconds\n")
                self.data_manager.save_result(text_id=prompt_ID, prompt=query, classification=best_match['classification'])
                return best_match['classification']

if __name__ == "__main__":
    query_classifier = LOCAL_CLASSIFIER()
    test_queries = [
        "This is a test query",
        "I love using AI",
        "Please classify this",
        "I want to watch a movie",
        "I'm feeling sad today",
        "how are you doing today"
    ]
    async def main():
        await query_classifier.initialize()
        for i in test_queries:
            if i == "how are you doing today":
                data = await query_classifier.classify_query_locally(prompt_ID="0910dd6f63706fc6e712a68db8fcc0b57689077d23594a9b518487ab71c88e68", query=i)
                print(data)
                continue
            data = await query_classifier.classify_query_locally(prompt_ID="test", query=i)
            print(data)

    asyncio.run(main())
    # asyncio.run(main(queries=tool_queries))

    # print(f"\n\n Number of IDs in ChromaDB: {len(data.get('ids'))}")