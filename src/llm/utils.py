import src.common.config as config
from src.common.logger import logger
from blingfire import text_to_sentences

async def split_and_enqueue_response(response, text_queue):

    try:
        sentences = text_to_sentences(response).split('\n')
        for sent in sentences:
            stripped_sentence = sent.strip()
            if stripped_sentence:
                logger.success(f"Enqueuing sentence {config.global_index_counter}: {stripped_sentence}")
                await text_queue.put((config.global_index_counter, stripped_sentence))
                config.global_index_counter += 1
    except Exception as e:
        logger.error(f"Error splitting and enqueuing response: {e}")
        await text_queue.put((config.global_index_counter, response))
        config.global_index_counter += 1