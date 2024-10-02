# AI Assistant

This is an AI Assistant project named Lexi that uses speech recognition and text-to-speech functionalities.

## Features

- Speech recognition using a web-based real-time speech-to-text service
- Hotword detection
  > [!NOTE]
  >
  > ### This are some supported hotwords
  >
  > **'picovoice', 'terminator', 'americano', 'hey siri', 'bumblebee', 'ok google', 'blueberry', 'jarvis', 'pico clock', 'porcupine', 'grapefruit', 'hey google', 'alexa'**
- Text-to-speech synthesis

## Requirements

- Python 3.8+
- [Google Chrome](https://www.google.com/chrome/)

## Set Up a Virtual Environment

**Create the Virtual Environment**

```
python -m venv venv
```

**Activate the Virtual Environment**

- On Windows:

```
venv\Scripts\activate.ps1
```

- On macOS/Linux:

```
source venv/bin/activate
```

## Install Requirements.txt

```bash
pip install -r requirements.txt
```
## Run this in terminal
```bash
python -m spacy download en_core_web_sm
```

## Environment Variables

This project uses a `.env` file to manage environment-specific settings like API keys, secret tokens, etc. An example file `.env.example` is provided in the source code.

### Setting Up the `.env` File

1. **Copy the `.env.example` file to a new file named `.env`**:

   ```bash
   cp .env.example .env
   ```

2. **Open the `.env` file and update the environment variables as needed**:

   - Replace placeholders with your actual values (e.g., API keys, paths).

3. **Save the `.env` file**.

After setting up the `.env` file, the project will automatically load these variables when you run the application.

## Run

```
python run.py
```

**_If not working try to restart your IDE_**
