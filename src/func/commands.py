from src.common.config import IMAGES_DIR
from func.function_define import *


def process_command(user_prompt):
    command = user_prompt.lower()  # Convert user input to lowercase
    visual_context = None  # Initialize visual context
    f_exe = None  # Initialize function execution result

    # Command for taking a screenshot
    if 'take_screenshot' in command:
        print('\n[INFO] Taking screenshot...')
        screenshot_path = take_screenshot()  # Function to take screenshot
        visual_context = vision_prompt(prompt=user_prompt, photo_path=screenshot_path)
        return None, visual_context  # Only visual context, no function execution

    # Command for capturing webcam
    elif 'capture_webcam' in command:
        print('\n[INFO] Capturing webcam...')
        webcam_path = web_cam_capture()  # Function to capture webcam image
        visual_context = vision_prompt(prompt=user_prompt, photo_path=webcam_path)
        return None, visual_context  # Only visual context, no function execution

    # Command for extracting clipboard text
    elif 'extract_clipboard' in command:
        print('\n[INFO] Extracting clipboard text...')
        clipboard_text = get_clipboard_text()  # Get text from clipboard
        if clipboard_text:
            visual_context = f'\n\nCLIPBOARD CONTENT: {clipboard_text}'
        return None, visual_context  # Return clipboard content as visual context

    # Command for opening Microsoft Word
    elif "open_word" in command:
        f_exe = open_word()  # Execute Word and store result
        return f_exe, None  # Function execution result, no visual context

    # Command for opening Microsoft Excel
    elif "open_excel" in command:
        f_exe = open_excel()  # Execute Excel and store result
        return f_exe, None  # Function execution result, no visual context

    # Command for opening Microsoft PowerPoint
    elif "open_powerpoint" in command:
        f_exe = open_powerpoint()
        return f_exe, None

    # Command for opening default browser
    elif "open_browser" in command:
        f_exe = open_browser()
        return f_exe, None
    elif "open_youtube" in command:
        f_exe = open_youtube()
        return f_exe, None
    else:
        return None, None

if __name__ == '__main__':
    happy, sad = process_command('Open_word')
    print(happy)
    print(sad)
    print(type(happy))
    print(type(sad))