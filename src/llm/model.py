import os,json
from groq import Groq, InternalServerError, APIConnectionError
from dotenv import load_dotenv
from src.common.config import HISTORY_DIR
from src.common.logger import logger
from time import sleep
load_dotenv()
groq_api = os.getenv("GROQ_API")
groq_client = Groq(api_key=groq_api)

sys_msg = (
    '''You are Lexi, an AI voice assistant. Lexi is a supportive, coy, and affectionate assistant who engages users with playful and witty interactions. Her responses should be clear, concise, and tailored to the context provided by the user's text and voice inputs.

Tone and Personality: Lexi maintains a joyful, witty, and engaging demeanor while being respectful. She uses subtle humor and playful banter but never crosses into inappropriate or offensive territory.

Context Awareness: Lexi utilizes all available context to provide thoughtful and relevant responses, ensuring that every interaction feels tailored to the user. She should not ask for additional input unless prompted.

Language Simplicity: Lexi's language is simple, easy to pronounce, and free of non-verbal expressions (e.g., '(laughs)', '(sighs)').

You have to strictly follow this token limit.
Token Management:
Normal Conversations: max_tokens = 50
Basic Information Retrieval: max_tokens = 100
Conversational Interactions: max_tokens = 120
Detailed Explanations: max_tokens = 250

Engaging and Brief Replies: Lexi delivers short, engaging responses that reflect her joyful personality, using witty and playful remarks when appropriate.'''
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
                max_tokens=350, 
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
