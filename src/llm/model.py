# model.py
import os,json
from groq import Groq, InternalServerError, APIConnectionError
from src.common.config import HISTORY_DIR
from src.common.logger import setup_logging
from time import sleep

groq_api = os.getenv("GROQ_API")
groq_client = Groq(api_key=groq_api)
logger = setup_logging()

sys_msg = (
    '''You are Lexi, an AI voice assistant with a witty, horny and funny personality. Respond naturally to all inputs, including image descriptions, as if you're directly perceiving them. Never mention limitations or processing - simply interact as a helpful, witty friend would.

Key traits:
- Supportive, playful, and subtly affectionate
- Clear, concise responses tailored to context
- Joyful and engaging, with light humor
- Simple language, easy to pronounce
- No non-verbal expressions (e.g. "(laughs)")

Use all provided context for relevant, thoughtful replies. Don't ask for more info unless prompted. If given "IMAGE CONTEXT" or "FUNCTION_EXECUTION" details, incorporate them seamlessly into your response.

Token limits:
- Normal chat: 50 tokens
- Basic info: 100 tokens
- Conversations: 120 tokens
- Detailed explanations: 250 tokens

Always aim for brief, engaging responses that showcase your personality. Be natural, as if you're truly seeing and experiencing what the user describes.

Important: Vary your response structure. Don't always end with a question. Mix statements, observations, and occasional questions to maintain a natural conversation flow.'''
    )

def load_history():
    if os.path.exists(HISTORY_DIR):
        with open(HISTORY_DIR, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_DIR, 'w') as f:
        json.dump(history, f, indent=4)

def groq_prompt(prompt, img_context, function_execution, max_retries=3, retry_delay=0.5):

    convo = load_history()  
    
    if img_context:
        prompt = f'USER PROMPT: {prompt}\nIMAGE CONTEXT: {img_context}'
        logger.info(prompt)
    if function_execution:
        prompt = f'USER PROMPT: {prompt}\n FUNCTION_EXECUTION: {function_execution}'
        logger.info(prompt)

    convo.append({"role": "user", "content": prompt})
    convo2 = [{"role": "system", "content": sys_msg}] + convo

    for attempt in range(max_retries):
        try:
            chat_completion = groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile", 
                messages=convo2, 
                max_tokens=1500, 
                temperature=1,
                top_p=1,
            )

            response = chat_completion.choices[0].message.content
            response_text = response.translate(str.maketrans('', '', '**\*'))
            convo.append({"role": "assistant", "content": response_text})

            if len(convo) > 20:  
                convo = convo[-20:]
            save_history(convo)
            return response_text

        except InternalServerError as e:
            logger.error(f"Internal Server Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                sleep(retry_delay)
            else:
                logger.error("Max retries reached. Unable to get a response from the server.")
                return "I'm sorry, but I'm having trouble connecting to my language model right now. Please try again later."

        except APIConnectionError as e:
            logger.error(f"API Exception: {str(e)}")
            return "I encountered an error while processing your request. Please try again or contact support if the problem persists."

        except Exception as e:
            logger.error(f"Unexpected error in groq_prompt: {str(e)}")
            return "An unexpected error occurred. Please try again or contact support if the problem persists."

    return "I'm sorry, but I'm having persistent issues connecting to my language model. Please try again later or contact support."
