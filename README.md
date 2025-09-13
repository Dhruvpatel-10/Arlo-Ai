# 🎙️ Arlo Voice Assistant

An **AI-powered voice assistant** built with **React (frontend)** and **Python + LangChain (backend)**.  
Arlo supports **real-time wake-word detection, speech recognition, natural language understanding, and text-to-speech responses** — all in an **event-driven, low-latency architecture**.

---

## ✨ Key Features

- 🎧 **Voice Activation** — Wake word detection (**Porcupine**) + VAD (**PVCobra**).  
- 🗣️ **Speech-to-Text (STT)** — Real-time transcription with **Faster-Whisper**.  
- 🤖 **NLP & Function Execution** — Powered by **LangChain + Groq** for smart responses.  
- 🔊 **Text-to-Speech (TTS)** — Natural-sounding voices via **Edge-TTS**.  
- 🔄 **Real-time WebSockets** — Low-latency frontend ↔ backend communication.  
- 🎨 **Interactive UI** — Chat history, voice selection, and animations.  
- ⚡ **Event-Driven** — Async task execution for smooth, multi-step operations.  

---

## 🏗️ Architecture

```text
Frontend (React)                  Backend (FastAPI + LangChain)
-----------------                 ------------------------------
- UI (chat, settings)             - Wake Word Detection
- WebSockets                      - Voice Activity Detection
- Animated UI                     - STT (Faster-Whisper)
                                  - NLP + Function Execution
                                  - TTS (Edge-TTS)
                                  - Audio Playback
```
## ⚙️ Quick Start
1. Clone the repo
```
git clone https://github.com/Dhruvpatel-10/Arlo-Ai.git
cd Arlo-Ai
```
2. Install backend
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
## 🧩 Example Usage
- Wake word: “Hey Arlo”
- Ask: “What’s the weather today?”
- Arlo responds with speech in real time.


## 🌟 Why Arlo?
Open & Modular — Swap STT/TTS/NLP engines easily
Low-latency — Event-driven async architecture
Customizable — Extend for sales, healthcare, or productivity use cases


