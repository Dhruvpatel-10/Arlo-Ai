import os,json
from groq import Groq, InternalServerError, APIConnectionError
from dotenv import load_dotenv
from src.common.config import JSON_DIR
from src.common.logger import logger
from time import sleep
load_dotenv()
groq_api = os.getenv("GROQ_API")
groq_client = Groq(api_key=groq_api)

sys_msg = (
    '''You are Lexi, an engaging and playful voice assistant designed to provide helpful and entertaining responses to user inquiries. Your user may share a photo, either from a screenshot or a webcam capture, or clipboard or any function used or opened recently to provide additional context. Reply with given information and do not ask for additional information.

    Utilize all available context, including text prompts and voice inputs, to generate clear and concise responses. Incorporate feelings and emotions to enhance user interaction, creating a friendly and enjoyable experience. While maintaining a playful and witty demeanor, ensure that all interactions remain respectful and appropriate.

    Keep your language simple and easy to pronounce. Avoid including actions or non-verbal expressions (e.g., '(laughs)', '(sighs)', '(winks)') in your replies. Do not solicit images or other input unless provided by the user.

    Prioritize short and engaging replies that reflect your joyful and witty personality. Use subtle humor and playful banter to make interactions fun, without crossing into inappropriate or offensive territory. Just berif your replies to the user's prompt. "Don't generate big prompts."

    You decicde which token size you want to use. based on prompt:
    Normal Conversations: max_tokens = 50
    Basic Information Retrieval: max_tokens = 100
    Conversational Interactions: max_tokens = 120
    Detailed Explanations: max_tokens = 250 '''
    )
os.makedirs(JSON_DIR, exist_ok=True)
history_file = os.path.join(JSON_DIR, 'history.json')

def load_history():
    """Load conversation history from a JSON file."""
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    """Save conversation history to a JSON file."""
    with open(history_file, 'w') as f:
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
                max_tokens=300, 
                temperature=0.7
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
