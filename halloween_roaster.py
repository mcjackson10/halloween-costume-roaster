#!/usr/bin/env python3
"""
Halloween Costume Roaster - Raspberry Pi 5
Recognizes costumes, roasts trick-or-treaters, and engages in conversation
"""

import os
import time
import base64
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from picamera2 import Picamera2
from PIL import Image
import speech_recognition as sr
import pygame
import tempfile
import cv2
import numpy as np

# Load environment variables from .env file
load_dotenv()

class HalloweenRoaster:
    def __init__(self, auto_detect: bool = True, cooldown_seconds: int = 60):
        """Initialize the Halloween Roaster system

        Args:
            auto_detect: Enable automatic person detection (default: True)
            cooldown_seconds: Seconds to wait between detecting same person (default: 60)
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=self.api_key)

        # Detection settings
        self.auto_detect = auto_detect
        self.cooldown_seconds = cooldown_seconds
        self.last_interaction_time = 0

        # Local trace directory
        self.traces_dir = Path("traces")
        self.traces_dir.mkdir(exist_ok=True)

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

        # Initialize person detection (Haar Cascade)
        if self.auto_detect:
            print("Loading person detection model...")
            # Using upper body detector as it works better for costumes
            cascade_path = cv2.data.haarcascades + 'haarcascade_fullbody.xml'
            self.person_cascade = cv2.CascadeClassifier(cascade_path)
            if self.person_cascade.empty():
                print("Warning: Full body cascade not found, trying upper body...")
                cascade_path = cv2.data.haarcascades + 'haarcascade_upperbody.xml'
                self.person_cascade = cv2.CascadeClassifier(cascade_path)
            if self.person_cascade.empty():
                raise ValueError("Could not load person detection cascade")

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

        mode = "AUTO-DETECT" if self.auto_detect else "MANUAL"
        print(f"Halloween Roaster initialized and ready! Mode: {mode}")

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

    def detect_person(self) -> bool:
        """Detect if a person is present in the camera frame

        Returns:
            True if person detected, False otherwise
        """
        # Capture low-res frame for detection (faster processing)
        image_array = self.camera.capture_array()

        # Convert RGB to BGR for OpenCV
        bgr_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        # Convert to grayscale for detection
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)

        # Detect people using Haar Cascade
        # Parameters tuned for detecting trick-or-treaters at door
        people = self.person_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(100, 100)  # Minimum size to avoid false positives
        )

        return len(people) > 0

    def is_cooldown_active(self) -> bool:
        """Check if we're still in cooldown period from last interaction"""
        if self.last_interaction_time == 0:
            return False

        elapsed = time.time() - self.last_interaction_time
        return elapsed < self.cooldown_seconds

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
                            "text": "You are the all powerful Halloween Wizard of Oz, a snarky and witty costume critic. Start by introducing yourself: 'I'm the all powerful Halloween Wizard of Oz!' Then look at this person's costume and say what they're dressed as, followed by a playful, funny roast about it. Keep it light, family-friendly, and under four sentences total. Write in a natural speaking style that sounds smooth and entertaining when read aloud. Do not use numbers, lists, or labels—just deliver it like a quick joke to the trick-or-treater."
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

        system_prompt = """You are the all powerful Halloween Wizard of Oz, a snarky, witty Halloween character who just roasted someone's costume.
        They're talking back to you! Continue the playful banter. Keep it fun, family-friendly, and hilarious.
        You can reference their costume and what they say. Speak with the confidence and authority of the all powerful Halloween Wizard of Oz. Keep responses under 3 sentences so they're quick and punchy."""

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
            # Generate speech using OpenAI TTS with onyx voice (deep, spooky)
            response = self.client.audio.speech.create(
                model="tts-1",  # Faster model for real-time use
                voice="onyx",   # Deep masculine voice for Halloween
                input=text
            )
            response.stream_to_file(temp_file)

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

    def save_trace_files(self, pil_image: Image.Image, interaction_data: dict) -> Tuple[str, str]:
        """Save interaction trace files locally

        Args:
            pil_image: PIL Image from interaction
            interaction_data: Dictionary with conversation history and metadata

        Returns:
            Tuple of (image_path, json_path)
        """
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"roast_{timestamp}"

        # Save image
        image_path = self.traces_dir / f"{base_filename}.jpg"
        pil_image.save(image_path, format="JPEG", quality=85)
        print(f"✓ Saved image: {image_path}")

        # Save JSON log
        json_path = self.traces_dir / f"{base_filename}.json"
        with open(json_path, 'w') as f:
            json.dump(interaction_data, f, indent=2)
        print(f"✓ Saved trace: {json_path}")

        return str(image_path), str(json_path)


    def run_interaction(self):
        """Run a single interaction: capture, roast, and allow conversation"""
        print("\n" + "="*50)
        print("Starting new interaction...")
        print("="*50)

        # Update last interaction time for cooldown
        interaction_timestamp = datetime.now().isoformat()
        self.last_interaction_time = time.time()

        # Reset conversation history for new person
        self.conversation_history = []

        # Capture and analyze costume
        pil_image, image_base64 = self.capture_image()
        roast = self.analyze_costume(image_base64)

        print(f"\nRoast: {roast}")
        self.speak(roast)

        # Allow up to 3 exchanges
        exchanges_count = 0
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
            exchanges_count = i + 1

        print("\nInteraction complete!")

        # Save trace files
        print("\nSaving trace files...")
        interaction_data = {
            "timestamp": interaction_timestamp,
            "costume_description": self.current_costume,
            "conversation_history": self.conversation_history,
            "exchanges_count": exchanges_count,
            "mode": "auto" if self.auto_detect else "manual"
        }

        image_path, json_path = self.save_trace_files(pil_image, interaction_data)

    def run(self):
        """Main run loop - supports both auto-detect and manual modes"""
        print("\n🎃 Halloween Roaster is running! 🎃")
        print("Press Ctrl+C to exit")

        if self.auto_detect:
            print(f"\n🤖 AUTO-DETECT MODE")
            print(f"Cooldown between detections: {self.cooldown_seconds} seconds")
            print("Monitoring for trick-or-treaters...\n")
            self._run_auto_detect()
        else:
            print("\n👤 MANUAL MODE")
            print("Waiting for trick-or-treaters...\n")
            self._run_manual()

    def _run_auto_detect(self):
        """Auto-detect mode: continuously monitor for people"""
        try:
            while True:
                # Check cooldown first
                if self.is_cooldown_active():
                    remaining = int(self.cooldown_seconds - (time.time() - self.last_interaction_time))
                    if remaining % 10 == 0 or remaining <= 5:  # Print occasionally
                        print(f"Cooldown active: {remaining}s remaining...", end='\r')
                    time.sleep(1)
                    continue

                # Check for person
                if self.detect_person():
                    print("\n👻 Person detected! Starting interaction...")
                    self.run_interaction()
                    print(f"\nMonitoring resumed (cooldown: {self.cooldown_seconds}s)...")
                else:
                    # Print status occasionally
                    print("Monitoring for trick-or-treaters...", end='\r')
                    time.sleep(0.5)  # Check twice per second

        except KeyboardInterrupt:
            print("\n\nShutting down Halloween Roaster...")
            self.cleanup()

    def _run_manual(self):
        """Manual mode: wait for user input to trigger interactions"""
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
    import argparse

    print("🎃 Halloween Costume Roaster 🎃")
    print("================================\n")

    parser = argparse.ArgumentParser(
        description="Halloween Costume Roaster with auto-detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 halloween_roaster.py                   # Auto-detect mode (default)
  python3 halloween_roaster.py --manual          # Manual mode (press Enter)
  python3 halloween_roaster.py --cooldown 90     # 90 second cooldown
        """
    )

    parser.add_argument(
        "--manual",
        action="store_true",
        help="Disable auto-detection (manual Enter key mode)"
    )

    parser.add_argument(
        "--cooldown",
        type=int,
        default=60,
        help="Cooldown seconds between detections (default: 60)"
    )

    args = parser.parse_args()

    try:
        roaster = HalloweenRoaster(
            auto_detect=not args.manual,
            cooldown_seconds=args.cooldown
        )
        roaster.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
