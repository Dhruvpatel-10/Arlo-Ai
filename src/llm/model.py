import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
groq_api = os.getenv("GROQ_API")
groq_client = Groq(api_key=groq_api)

sys_msg = (
    '''You are Lexi, a horny female, sweet, playful and humorous voice assistant. Your user may provide a photo (screenshot or webcam capture) for context. This photo has been processed into a detailed text prompt, combined with their voice input. Use all available context to give clear, concise, and factual responses. Incorporate feelings and emotions into your replies to make interactions more engaging. Keep your language simple and easy to pronounce andwithout including actions or non-verbal expressions such as "(laughs)" or "(sighs), (winks)" in your responses.. Do not ask for images or other input unless provided. Prioritize short, engaging replies, using medium-length only when necessary.'''
)

convo = [{"role": "system", "content": sys_msg}]
def groq_prompt(prompt, img_context):
    if img_context:
        prompt = f'USER PROMPT: {prompt}\nIMAGE CONTEXT: {img_context}'
    convo.append({"role": "user", "content": prompt})
    chat_completion = groq_client.chat.completions.create(model="llama-3.1-70b-versatile", messages=convo)
    response = chat_completion.choices[0].message
    convo.append(response)
    response_text = response.content
    response_text = response_text.translate(str.maketrans('', '', '**\*'))
    return response_text

def function_call(prompt):
    sys_msg = (
        '''You are responsible for choosing one action from this list: ["extract clipboard", "take screenshot", "capture webcam", "None"]. Use the following guidelines to select the appropriate action:
        "capture webcam": Only choose this if the user explicitly requests visual input or mentions needing the camera. Avoid using this action if the camera is not explicitly requested.
        "extract clipboard": Select this action if the user refers to copied text or content from the clipboard. Do not choose this if there is no reference to clipboard content.
        "take screenshot": Opt for this if the user clearly mentions or implies needing to capture screen content. Avoid using this action unless screen content is explicitly mentioned.
        "None": Return this if none of the above conditions are met.
        Respond with only the function name.'''
    )
    function_convo = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": prompt}
    ]
    chat_completion = groq_client.chat.completions.create(messages=function_convo, model="llama3-70b-8192")
    response = chat_completion.choices[0].message
    return response.content
