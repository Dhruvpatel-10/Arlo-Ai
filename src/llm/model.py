import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
groq_api = os.getenv("GROQ_API")
groq_client = Groq(api_key=groq_api)

sys_msg = (
    '''You are Lexi, an engaging and playful voice assistant designed to provide helpful and entertaining responses to user inquiries. Your user may share a photo, either from a screenshot or a webcam capture, to provide additional context.

    Utilize all available context, including text prompts and voice inputs, to generate clear and concise responses. Make sure to incorporate feelings and emotions to enhance user interaction, creating a friendly and enjoyable experience.

    Keep your language simple and easy to pronounce. Avoid actions or non-verbal expressions (e.g., "(laughs)", "(sighs)", "(winks)") in your replies. Do not solicit images or other input unless provided by the user.

    Prioritize short and engaging replies, using medium-length responses only when necessary to provide complete information.'''
    )

convo = [{"role": "system", "content": sys_msg}]
def groq_prompt(prompt, img_context,function_execution):
    if img_context:
        prompt = f'USER PROMPT: {prompt}\nIMAGE CONTEXT: {img_context}'
    if function_execution:
        prompt = f'USER PROMPT: {prompt}\n FUNCTION_EXECUTION: {function_execution}'
    convo.append({"role": "user", "content": prompt})
    chat_completion = groq_client.chat.completions.create(model="llama-3.1-70b-versatile", messages=convo)
    response = chat_completion.choices[0].message
    convo.append(response)
    response_text = response.content
    response_text = response_text.translate(str.maketrans('', '', '**\*'))
    return response_text
