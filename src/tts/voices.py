# src/tts/voices.py

from dataclasses import dataclass

@dataclass
class Voice:
    name: str
    engine: str

VOICES = {
    # EdgeTTS Voices
    "Natasha_Edge": Voice(
        name="en-AU-NatashaNeural",
        engine="EdgeTTS",
    ),
    "Clara_Edge": Voice(
        name="en-CA-ClaraNeural",
        engine="EdgeTTS",
    ),
    "Libby_Edge": Voice(
        name="en-GB-LibbyNeural",
        engine="EdgeTTS",
    ),
    "Maisie_Edge": Voice(
        name="en-GB-MaisieNeural",
        engine="EdgeTTS",
    ),
    "Sonia_Edge": Voice(
        name="en-GB-SoniaNeural",
        engine="EdgeTTS",
    ),
    "Yan_Edge": Voice(
        name="en-HK-YanNeural",
        engine="EdgeTTS",
    ),
    "Emily_Edge": Voice(
        name="en-IE-EmilyNeural",
        engine="EdgeTTS",
    ),
    "Neerja_Edge": Voice(
        name="en-IN-NeerjaExpressiveNeural",
        engine="EdgeTTS",
    ),
    "Neerja2_Edge": Voice(
        name="en-IN-NeerjaNeural",
        engine="EdgeTTS",
    ),
    "Asilia_Edge": Voice(
        name="en-KE-AsiliaNeural",
        engine="EdgeTTS",
    ),
    "Ezinne_Edge": Voice(
        name="en-NG-EzinneNeural",
        engine="EdgeTTS",
    ),
    "Molly_Edge": Voice(
        name="en-NZ-MollyNeural",
        engine="EdgeTTS",
    ),
    "Rosa_Edge": Voice(
        name="en-PH-RosaNeural",
        engine="EdgeTTS",
    ),
    "Luna_Edge": Voice(
        name="en-SG-LunaNeural",
        engine="EdgeTTS",
    ),
    "Imani_Edge": Voice(
        name="en-TZ-ImaniNeural",
        engine="EdgeTTS",
    ),
    "Ana_Edge": Voice(
        name="en-US-AnaNeural",
        engine="EdgeTTS",
    ),
    "Aria_Edge": Voice(
        name="en-US-AriaNeural",
        engine="EdgeTTS",
    ),
    "Ava_Edge": Voice(
        name="en-US-AvaNeural",
        engine="EdgeTTS",
    ),
    "Ava2_Edge": Voice(
        name="en-US-AvaMultilingualNeural",
        engine="EdgeTTS",
    ),
    "Emma_Edge": Voice(
        name="en-US-EmmaMultilingualNeural",
        engine="EdgeTTS",
    ),
    "Emma2_Edge": Voice(
        name="en-US-EmmaNeural",
        engine="EdgeTTS",
    ),
    "Jenny_Edge": Voice(
        name="en-US-JennyNeural",
        engine="EdgeTTS",
    ),
    "Michelle_Edge": Voice(
        name="en-US-MichelleNeural",
        engine="EdgeTTS",
    ),
    "Leah_Edge": Voice(
        name="en-ZA-LeahNeural",
        engine="EdgeTTS",
    ),
    
    # SpeechifyTTS Voices
    "Erica_Speechify": Voice(
        name="erica",
        engine="SpeechifyTTS",
    ),
    "Sophia_Speechify": Voice(
        name="sophia",
        engine="SpeechifyTTS",
    ),
    "Jamie_Speechify": Voice(
        name="jamie",
        engine="SpeechifyTTS",
    ),
    "Emma_Speechify": Voice(
        name="emma",
        engine="SpeechifyTTS",
    ),
    "Lisa_Speechify": Voice(
        name="lisa",
        engine="SpeechifyTTS",
    ),
    "Jessica_Speechify": Voice(
        name="jessica",
        engine="SpeechifyTTS",
    ),
    "Aria_Speechify": Voice(
        name="aria",
        engine="SpeechifyTTS",
    ),
    "Carly_Speechify": Voice(
        name="carly",
        engine="SpeechifyTTS",
    ),
    "Sally_Speechify": Voice(
        name="sally",
        engine="SpeechifyTTS",
    ),
}

if __name__ == "__main__":
    print("VOICES Dictionary Contents:")
    for key, voice in VOICES.items():
        print(f"{key}: {voice}")
