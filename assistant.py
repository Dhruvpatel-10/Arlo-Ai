from asset.LLM import groq_prompt, function_call, vision_prompt
from asset.LLM import take_screenshot, web_cam_capture, get_clipboard_text
from asset.LLM.clean import combine_last_two_paragraphs, split_text_into_paragraphs
from asset.TTS.play import generate_audio_files
import queue


while True:
    user_prompt = input("\nUSER: ")
    call = function_call(user_prompt)
    visual_context = None

    if 'take screenshot' in call:
        print('\n[INFO] Taking screenshot...')
        take_screenshot()
        visual_context = vision_prompt(prompt=user_prompt, photo_path='asset/LLM/images/screenshot.jpg')
            
    elif 'capture webcam' in call:
        print('\n[INFO] Capturing webcam...')
        web_cam_capture()
        visual_context = vision_prompt(prompt=user_prompt, photo_path='asset/LLM/images/webcam.jpg')
            
    elif 'extract clipboard' in call:
        print('\n[INFO] Extracting clipboard text...')
        clipboard_text = get_clipboard_text()
        if clipboard_text:
            user_prompt = f'{user_prompt}\n\nCLIPBOARD CONTENT: {clipboard_text}'
            visual_context = None

    response = groq_prompt(prompt=user_prompt, img_context=visual_context)
    print("\n" + "="*50)
    print(f"ASSISTANT: {response}")
    print("="*50)
    text_queue = queue.Queue()
    paragraphs = split_text_into_paragraphs(response)
    paragraphs = combine_last_two_paragraphs(paragraphs)

    for para in paragraphs:
        text_queue.put(para)    

    generate_audio_files(text_queue)
    