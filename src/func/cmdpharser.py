from func.function_define import *
from src.common.logger import setup_logging

logger = setup_logging()

def process_command(command: str,user_prompt: str = None, url: str = None) -> str:

    command = command.lower()  
    logger.info(f"COMMAND: {command}")
    visual_context = None  # Initialize visual context
    f_exe = None  # Initialize function execution result

    # Command for taking a screenshot
    if 'take_screenshot' in command:
        print('\n[INFO] Taking screenshot...')
        screenshot_path = take_screenshot()  # Function to take screenshot
        logger.info(f"SCREENSHOT PATH: {screenshot_path} TAKEN")
        visual_context = vision_prompt(prompt=user_prompt, photo_path=screenshot_path)
        return f_exe, visual_context  # Only visual context, no function execution

    # Command for capturing webcam
    elif 'capture_webcam' in command:
        print('\n[INFO] Capturing webcam...')
        webcam_path = web_cam_capture()  # Function to capture webcam image
        logger.info(f"WEBCAM PATH: {webcam_path} TAKEN")
        visual_context = vision_prompt(prompt=user_prompt, photo_path=webcam_path)
        return f_exe, visual_context  # Only visual context, no function execution

    # Command for extracting clipboard text
    elif 'extract_clipboard' in command:
        print('\n[INFO] Extracting clipboard text...')
        clipboard_text = get_clipboard_text()  # Get text from clipboard
        logger.info(f"CLIPBOARD TEXT: {clipboard_text} EXTRACTED")
        if clipboard_text:
            visual_context = f'\n\nCLIPBOARD CONTENT: {clipboard_text}'
        return f_exe, visual_context  # Return clipboard content as visual context

    # Command for opening Microsoft Word
    elif "open_word" in command:
        f_exe = open_word()  # Execute Word and store result
        logger.info(f"WORD EXECUTION: {f_exe}")
        return f_exe, visual_context  # Function execution result, no visual context

    # Command for opening Microsoft Excel
    elif "open_excel" in command:
        f_exe = open_excel()  # Execute Excel and store result
        logger.info(f"EXCEL EXECUTION: {f_exe}")
        return f_exe, visual_context  # Function execution result, no visual context

    # Command for opening Microsoft PowerPoint
    elif "open_powerpoint" in command:
        f_exe = open_powerpoint()
        logger.info(f"POWERPOINT EXECUTION: {f_exe}")
        return f_exe, visual_context

    # Command for opening default browser
    elif "open_browser" in command:
        logger.info(f"BROWSER EXECUTION")
        f_exe = handle_browser(url=url)
        return f_exe, visual_context
    else:
        return f_exe, visual_context  
