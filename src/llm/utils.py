from src.common.logger import logger
from blingfire import text_to_sentences
import logging  # Ensure you have a logger set up

def split_and_enqueue_response(response, text_queue):
    try:
        sentences = text_to_sentences(response).split('\n')
        for idx, sent in enumerate(sentences):
            stripped_sentence = sent.strip()
            if stripped_sentence:
                logging.info(f"Enqueuing sentence {idx}: {stripped_sentence}")
                text_queue.put((idx, stripped_sentence))  # Enqueue as (index, sentence)
    except Exception as e:
        logging.error(f"Error splitting and enqueuing response: {e}")
        # Fallback: Put the entire response with index -1
        text_queue.put((-1, response))
