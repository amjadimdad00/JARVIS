import os
import hashlib
import asyncio
import pygame
import edge_tts
from dotenv import dotenv_values
import random

# Load environment variables
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice")

# Initialize pygame mixer once
pygame.mixer.init()

# Single speech file
SPEECH_FILE = os.path.join("Data", "speech.mp3")
os.makedirs("Data", exist_ok=True)

# Keep track of last spoken text
_last_text_hash = None

# Async TTS generation
async def generate_tts(text: str) -> None:
    global _last_text_hash
    current_hash = hashlib.md5(text.encode()).hexdigest()

    # Only regenerate if text changed
    if current_hash != _last_text_hash:
        # Stop any currently playing audio before overwriting
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.quit()
        pygame.mixer.init()

        # Remove old file if exists
        if os.path.exists(SPEECH_FILE):
            os.remove(SPEECH_FILE)

        communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
        await communicate.save(SPEECH_FILE)
        _last_text_hash = current_hash

# Play audio file
def play_audio(stop_func=lambda r=None: True):
    try:
        pygame.mixer.music.load(SPEECH_FILE)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if stop_func() is False:
                pygame.mixer.music.stop()
                break
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Audio playback error: {e}")

# Main TTS function
def TTS(text: str, stop_func=lambda r=None: True):
    try:
        asyncio.run(generate_tts(text))
        play_audio(stop_func)
    except Exception as e:
        print(f"TTS Error: {e}")

# Smart text-to-speech for long texts
def TextToSpeech(text: str, stop_func=lambda r=None: True):
    sentences = text.split(".")
    responses = [
        "The rest of the answer is chilling on the chat screen, waiting for you, sir.",
        "You can spy the rest of the text on the chat screen, sir.",
        "The remaining part of the wisdom is now on the chat screen, sir.",
        "Sir, the chat screen is holding the rest of the story just for you.",
        "The sequel of this text has premiered on the chat screen, sir.",
        "Sir, more brilliance awaits you on the chat screen.",
        "The rest of the text has gone on a coffee break at the chat screen, sir—check it out.",
        "Sir, the chat screen has reserved the next part of the text just for you."
    ]

    if len(sentences) > 4 and len(text) > 250:
        first_part = ". ".join(sentences[:2]) + ". " + random.choice(responses)
        TTS(first_part, stop_func)
    else:
        TTS(text, stop_func)

# Example usage
if __name__ == "__main__":
    while True:
        user_input = input("Enter text: ")
        TextToSpeech(user_input)
