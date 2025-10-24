#!/usr/bin/env python3
"""
Halloween Costume Roaster - Raspberry Pi 5
Recognizes costumes, roasts trick-or-treaters, and engages in conversation
"""

import os
import time
import base64
import io
from pathlib import Path
from typing import Optional, Tuple
from openai import OpenAI
from picamera2 import Picamera2
from PIL import Image
import speech_recognition as sr
import pygame
from gtts import gTTS
import tempfile

class HalloweenRoaster:
    def __init__(self):
        """Initialize the Halloween Roaster system"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=self.api_key)

        # Initialize camera
        print("Initializing camera...")
        self.camera = Picamera2()
        camera_config = self.camera.create_still_configuration(
            main={"size": (1920, 1080)},
            buffer_count=2
        )
        self.camera.configure(camera_config)
        self.camera.start()
        time.sleep(2)  # Let camera warm up

        # Initialize speech recognition
        print("Initializing speech recognition...")
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Adjust for ambient noise
        with self.microphone as source:
            print("Calibrating microphone for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)

        # Initialize audio playback (for bluetooth speaker)
        print("Initializing audio playback...")
        pygame.mixer.init()

        # Conversation context
        self.conversation_history = []
        self.current_costume = None

        print("Halloween Roaster initialized and ready!")

    def capture_image(self) -> Tuple[Image.Image, bytes]:
        """Capture an image from the camera and return PIL Image and base64 encoded data"""
        print("Capturing image...")

        # Capture image as array
        image_array = self.camera.capture_array()

        # Convert to PIL Image
        pil_image = Image.fromarray(image_array)

        # Convert to JPEG and base64 encode
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        image_bytes = buffer.getvalue()
        image_base64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        return pil_image, image_base64

    def analyze_costume(self, image_base64: str) -> str:
        """Use GPT-4o mini to analyze the costume in the image"""
        print("Analyzing costume...")

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "You are a snarky, witty Halloween costume critic. Look at this person's costume and: 1) Identify what they're dressed as, 2) Give them a hilarious, playful roast about their costume (keep it fun and family-friendly, not mean-spirited). Be creative and funny! Keep your response under 3 sentences."
                        }
                    ],
                }
            ],
        )

        response_text = response.choices[0].message.content
        self.current_costume = response_text
        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })

        return response_text

    def listen_for_speech(self, timeout: int = 5) -> Optional[str]:
        """Listen for speech from the microphone"""
        print(f"Listening for speech (timeout: {timeout}s)...")

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)

            print("Processing speech...")
            text = self.recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text

        except sr.WaitTimeoutError:
            print("No speech detected")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return None

    def generate_response(self, user_input: str) -> str:
        """Generate a witty response to user's comeback"""
        print("Generating response...")

        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        system_prompt = """You are a snarky, witty Halloween character who just roasted someone's costume.
        They're talking back to you! Continue the playful banter. Keep it fun, family-friendly, and hilarious.
        You can reference their costume and what they say. Keep responses under 3 sentences so they're quick and punchy."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt}
            ] + self.conversation_history
        )

        response_text = response.choices[0].message.content
        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })

        return response_text

    def speak(self, text: str):
        """Convert text to speech and play through bluetooth speaker"""
        print(f"Speaking: {text}")

        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_file = fp.name

        try:
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_file)

            # Play audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

        finally:
            # Clean up temp file
            pygame.mixer.music.unload()
            time.sleep(0.1)
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def run_interaction(self):
        """Run a single interaction: capture, roast, and allow conversation"""
        print("\n" + "="*50)
        print("Starting new interaction...")
        print("="*50)

        # Reset conversation history for new person
        self.conversation_history = []

        # Capture and analyze costume
        pil_image, image_base64 = self.capture_image()
        roast = self.analyze_costume(image_base64)

        print(f"\nRoast: {roast}")
        self.speak(roast)

        # Allow up to 3 exchanges
        for i in range(3):
            print(f"\n--- Exchange {i+1}/3 ---")
            user_speech = self.listen_for_speech(timeout=8)

            if user_speech is None:
                if i == 0:
                    # No response to initial roast
                    farewell = "What's wrong? Cat got your tongue? Or did your costume make you speechless too?"
                    print(f"Farewell: {farewell}")
                    self.speak(farewell)
                break

            # Generate and speak response
            response = self.generate_response(user_speech)
            print(f"Response: {response}")
            self.speak(response)

        print("\nInteraction complete!")

    def run(self):
        """Main run loop"""
        print("\n🎃 Halloween Roaster is running! 🎃")
        print("Press Ctrl+C to exit")
        print("\nWaiting for trick-or-treaters...\n")

        try:
            while True:
                input("Press Enter when someone arrives (or Ctrl+C to exit)...")
                self.run_interaction()
                print("\nReady for next person...")

        except KeyboardInterrupt:
            print("\n\nShutting down Halloween Roaster...")
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up...")
        self.camera.stop()
        pygame.mixer.quit()
        print("Goodbye! 🎃")

def main():
    """Main entry point"""
    print("🎃 Halloween Costume Roaster 🎃")
    print("================================\n")

    try:
        roaster = HalloweenRoaster()
        roaster.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
