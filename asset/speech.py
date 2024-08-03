from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import threading
import time

class SpeechToTextListener:
    def __init__(
            self, 
            website_path: str = "https://realtime-stt-devs-do-code.netlify.app/", 
            language: str = "en-US",
            wait_time: int = 10):
        
        self.website_path = website_path
        self.language = language
        self.chrome_options = Options()
        self.chrome_options.add_argument("--use-fake-ui-for-media-stream")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--log-level=3")  
        self.chrome_options.add_argument("--disable-gpu")  
        self.chrome_options.add_argument("--no-sandbox")  
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, wait_time)
        self.stop_event = threading.Event()

    def stream(self, content: str):
        """Prints the given content to the console, overwriting previous output."""
        print("\rUser Speaking: " + f"{content}", end='', flush=True)

    def get_text(self) -> str:
        """Retrieves the transcribed text from the website."""
        return self.driver.find_element(By.ID, "convert_text").text

    def select_language(self):
        """Selects the language from the dropdown using JavaScript."""
        self.driver.execute_script(
            f"""
            var select = document.getElementById('language_select');
            select.value = '{self.language}';
            var event = new Event('change');
            select.dispatchEvent(event);
            """
        )

    def verify_language_selection(self):
        """Verifies if the language is correctly selected."""
        language_select = self.driver.find_element(By.ID, "language_select")
        selected_language = language_select.find_element(By.CSS_SELECTOR, "option:checked").get_attribute("value")
        return selected_language == self.language

    def main(self) -> Optional[str]:
        try:
            self.driver.get(self.website_path)
            
            self.wait.until(EC.presence_of_element_located((By.ID, "language_select")))
            
            self.select_language()

            if not self.verify_language_selection():
                print(f"Error: Failed to select the correct language. Selected: {self.verify_language_selection()}, Expected: {self.language}")
                return None

            self.driver.find_element(By.ID, "click_to_record").click()

            is_recording = self.wait.until(EC.presence_of_element_located((By.ID, "is_recording")))

            stream_thread = threading.Thread(target=self.update_stream)
            stream_thread.start()

            while True:
                is_recording_text = self.driver.find_element(By.ID, "is_recording").text
                if not is_recording_text.startswith("Recording: True"):
                    self.stop_event.set()  
                    break
                time.sleep(2) 

            stream_thread.join() 
            return self.get_text()
        except Exception as e:
            print(f"Error during main processing: {e}")
            return None

    def update_stream(self):
    
        while not self.stop_event.is_set():
            try:
                text = self.get_text()
                if text:
                    self.stream(text)
                time.sleep(1)  
            except Exception as e:
                print(f"Error during streaming update: {e}")
                break

    def listen(self, prints: bool = False) -> Optional[str]:
        while True:
            result = self.main()
            if result and len(result) != 0:
                print("\r" + " " * (len(result) + 16) + "\r", end="", flush=True)
                if prints: print("\rYOU SAID: " + f"{result}\n")
                break
        return result

if __name__ == "__main__":
    listener = SpeechToTextListener(language="en-US") 
    speech = listener.listen()
    print("FINAL EXTRACTION: ", speech)