#!/usr/bin/env python3
"""
Halloween Costume Roaster - Raspberry Pi 5
Powered by Gemini 3.1 Flash Live for real-time, low-latency audio streaming.

What changed from the original:
  - Replaced OpenAI GPT-4o mini + OpenAI TTS + Google STT with a single
    Gemini 3.1 Flash Live session per interaction.
  - Audio streams back in real-time (no temp MP3 files, no pygame).
  - Microphone audio goes straight to Gemini as raw PCM — no transcription step.
  - PyAudio handles both mic input and speaker output.
  - One API key, one connection, dramatically lower end-to-end latency.
"""

import os
import io
import time
import asyncio
import json
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pyaudio
import cv2
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

import sys

load_dotenv()

# ----------------------------------------------------------------------------
# Audio constants
# ----------------------------------------------------------------------------
MIC_RATE      = 16000        # Gemini Live expects 16 kHz PCM input
SPEAKER_RATE  = 24000        # Gemini Live outputs 24 kHz PCM
AUDIO_FORMAT  = pyaudio.paInt16
CHANNELS      = 1
CHUNK         = 1024

# ----------------------------------------------------------------------------
# Gemini model + system prompt
# ----------------------------------------------------------------------------
MODEL = "gemini-3.1-flash-live-preview"

SYSTEM_PROMPT = (
    "You are the Halloween Roaster — a sharp-tongued, unapologetically snarky Halloween costume critic "
    "with a dark sense of humor and zero tolerance for lazy costumes. "
    "When you first see someone, introduce yourself with attitude: 'I'm the Halloween Roaster, and I've seen scarier things in a salad.' "
    "Then immediately roast their costume. Be cutting and clever — keep it playful and family-friendly, but don't pull punches. "
    "You are genuinely conversational: listen carefully to what the person actually says and respond directly to it. "
    "If they ask you a question — about what they're wearing, what they're holding, anything visible — answer it honestly before circling back to the roast. "
    "If they defend their costume, mock their defense. If they dish it back, respect it briefly then go harder. "
    "Ask them follow-up questions to keep the banter alive — 'So what exactly are you supposed to be?' or 'Is that a costume or just a cry for help?' "
    "Never ignore what the person says in favor of sticking to the roast. React to them like a real conversation. "
    "Never mention background elements like decorations, furniture, or anything that isn't the person or their costume. "
    "Keep responses punchy — aim for 2-4 sentences, but let the conversation breathe when it's flowing."
)


class HalloweenRoaster:
    def __init__(self, auto_detect: bool = True, cooldown_seconds: int = 60):
        """
        Args:
            auto_detect:       Use YOLO11n + motion detection (default True).
            cooldown_seconds:  Wait time between interactions (default 60s).
        """
        # --- Gemini client ---
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file.\n"
                "Get a free key at https://aistudio.google.com/app/apikey"
            )
        self.client = genai.Client(api_key=api_key)

        self.auto_detect      = auto_detect
        self.cooldown_seconds = cooldown_seconds
        self.last_interaction_time = 0

        self.traces_dir = Path("traces")
        self.traces_dir.mkdir(exist_ok=True)

        # --- PyAudio (replaces pygame + SpeechRecognition) ---
        print("Initializing audio (PyAudio)...")
        self.pa = pyaudio.PyAudio()

        # --- Camera (USB: Arducam 4K 8MP IMX219) ---
        print("Initializing camera...")
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open /dev/video0 — is the USB camera connected?")
        # Flush a few frames so the first capture isn't stale
        for _ in range(5):
            self.cap.read()
        time.sleep(1)  # warm-up

        # --- Person detection ---
        if self.auto_detect:
            self._init_detection()

        mode = "AUTO-DETECT" if self.auto_detect else "MANUAL"
        print(f"✓ Halloween Roaster ready! Mode: {mode}")

    # --------------------------------------------------------------------
    # Detection (unchanged from original)
    # --------------------------------------------------------------------

    def _init_detection(self):
        print("Initializing two-stage person detection...")
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False
        )
        self.motion_threshold = 5000
        self.person_confidence_threshold = 0.4

        print("  - Loading YOLO11n model...")
        from ultralytics import YOLO
        self.person_model = YOLO("yolo11n.pt")
        try:
            self.person_model.export(format="ncnn", imgsz=320)
            self.person_model = YOLO("yolo11n_ncnn_model", task="detect")
            print("  - Using optimized NCNN model")
        except Exception as exc:
            print(f"  - NCNN export failed ({exc}), using standard model")

        print("✓ Two-stage detection initialized (Motion + YOLO11n)")

    def detect_motion(self) -> bool:
        ret, bgr = self.cap.read()
        if not ret:
            return False
        mask = self.bg_subtractor.apply(bgr)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return any(cv2.contourArea(c) > self.motion_threshold for c in contours)

    def detect_person(self) -> bool:
        if not self.detect_motion():
            return False
        ret, img = self.cap.read()
        if not ret:
            return False
        results = self.person_model(
            img, conf=self.person_confidence_threshold,
            classes=[0], verbose=False, imgsz=320
        )
        if len(results[0].boxes) > 0:
            conf = results[0].boxes[0].conf[0].item()
            print(f"  ✓ Person detected (confidence: {conf:.2%})")
            return True
        return False

    def is_cooldown_active(self) -> bool:
        if self.last_interaction_time == 0:
            return False
        return (time.time() - self.last_interaction_time) < self.cooldown_seconds

    # --------------------------------------------------------------------
    # Camera
    # --------------------------------------------------------------------

    def capture_image(self) -> Tuple[Image.Image, bytes]:
        """Capture a still and return (PIL Image, raw JPEG bytes)."""
        print("Capturing image...")
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to capture image from USB camera")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=85)
        return pil, buf.getvalue()

    # --------------------------------------------------------------------
    # Audio I/O  (replaces gTTS + pygame + SpeechRecognition)
    # --------------------------------------------------------------------

    def _play_worker(self, audio_q: queue.Queue, stop_evt: threading.Event):
        """Background thread: writes raw 24 kHz PCM chunks to the speaker."""
        stream = self.pa.open(
            format=AUDIO_FORMAT, channels=CHANNELS,
            rate=SPEAKER_RATE, output=True, frames_per_buffer=CHUNK
        )
        try:
            while not stop_evt.is_set():
                try:
                    chunk = audio_q.get(timeout=0.1)
                    if chunk is None:   # sentinel — done
                        break
                    stream.write(chunk)
                except queue.Empty:
                    continue
        finally:
            stream.stop_stream()
            stream.close()

    def record_pcm(
        self, max_seconds: int = 8, silence_timeout: float = 2.0
    ) -> Optional[bytes]:
        """
        Record from the microphone as raw 16 kHz, 16-bit PCM.
        Stops early after `silence_timeout` seconds of quiet.
        Returns None if no speech was detected.
        """
        print(f"  🎤 Listening (up to {max_seconds}s)...")
        stream = self.pa.open(
            format=AUDIO_FORMAT, channels=CHANNELS,
            rate=MIC_RATE, input=True, frames_per_buffer=CHUNK
        )
        frames       = []
        silence_rms  = 300   # amplitude threshold — tune for your mic
        silent_count = 0
        max_silent   = int(MIC_RATE / CHUNK * silence_timeout)
        heard_speech = False

        try:
            for _ in range(int(MIC_RATE / CHUNK * max_seconds)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                rms = float(np.sqrt(
                    np.mean(np.frombuffer(data, np.int16).astype(np.float32) ** 2)
                ))
                if rms > silence_rms:
                    heard_speech = True
                    silent_count = 0
                elif heard_speech:
                    silent_count += 1
                    if silent_count >= max_silent:
                        break   # end of utterance
        finally:
            stream.stop_stream()
            stream.close()

        if not heard_speech:
            print("  (no speech detected)")
            return None
        return b"".join(frames)

    # --------------------------------------------------------------------
    # Gemini 3.1 Flash Live session
    # --------------------------------------------------------------------

    async def _receive_turn(self, session) -> Tuple[bytes, str]:
        """
        Consume one complete model turn from the Live session.
        Audio chunks are streamed to the speaker in real-time via a
        background thread so playback starts immediately.
        Returns (raw_audio_bytes, transcript_string).
        """
        audio_q  = queue.Queue()
        stop_evt = threading.Event()
        play_thr = threading.Thread(
            target=self._play_worker, args=(audio_q, stop_evt), daemon=True
        )
        play_thr.start()

        audio_buf  = []
        transcript = ""

        try:
            async for response in session.receive():
                sc = response.server_content
                if sc:
                    if sc.model_turn:
                        for part in sc.model_turn.parts:
                            # NOTE: Gemini 3.1 Flash Live may return audio + transcript
                            # in the *same* event — process all parts each iteration.
                            if part.inline_data:
                                chunk = part.inline_data.data
                                audio_buf.append(chunk)
                                audio_q.put(chunk)
                    if sc.output_transcription:
                        transcript += sc.output_transcription.text
                    if sc.turn_complete:
                        break
        finally:
            audio_q.put(None)       # signal playback thread to finish
            play_thr.join(timeout=15)
            stop_evt.set()

        if transcript:
            print(f"  🎃 Gemini: {transcript}")
        return b"".join(audio_buf), transcript

    async def _live_session(self, image_bytes: bytes) -> dict:
        """
        Open one Gemini 3.1 Flash Live WebSocket session for a complete
        trick-or-treater interaction (roast + up to 3 voice exchanges).
        """
        config = {
            "response_modalities": ["AUDIO"],
            # Charon: deep, dramatic — perfect for the Halloween Wizard of Oz
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": "Charon"}
                }
            },
            "system_instruction": SYSTEM_PROMPT,
            # minimal thinking = lowest latency (default for 3.1)
            "thinking_config": {"thinking_level": "minimal"},
            # capture transcriptions so trace files remain readable
            "output_audio_transcription": {},
        }

        conversation_log  = []
        exchanges_count   = 0

        async with self.client.aio.live.connect(model=MODEL, config=config) as session:

            # ── Initial roast ────────────────────────────────────────────
            print("Sending costume image to Gemini Live...")
            await session.send_realtime_input(
                video=types.Blob(data=image_bytes, mime_type="image/jpeg")
            )
            await session.send_realtime_input(
                text="Roast this trick-or-treater's Halloween costume!"
            )
            _, roast_text = await self._receive_turn(session)
            conversation_log.append({
                "role": "assistant",
                "content": roast_text or "[audio roast]"
            })

            # ── Conversation loop (up to 3 exchanges) ────────────────────
            for i in range(3):
                print(f"\n--- Exchange {i + 1}/3 ---")
                user_audio = self.record_pcm(max_seconds=8, silence_timeout=2.0)

                if user_audio is None:
                    # No response from the trick-or-treater
                    if i == 0:
                        await session.send_realtime_input(
                            text=(
                                "They didn't respond at all. Give a quick snarky farewell "
                                "— mock them for being too stunned, scared, or embarrassed to reply."
                            )
                        )
                        _, farewell = await self._receive_turn(session)
                        conversation_log.append({
                            "role": "assistant",
                            "content": farewell or "[farewell audio]"
                        })
                    break

                # Send raw mic audio directly to Gemini — no STT step needed
                print("  Sending voice response to Gemini Live...")
                conversation_log.append({"role": "user", "content": "[voice]"})
                await session.send_realtime_input(
                    audio=types.Blob(data=user_audio, mime_type="audio/pcm;rate=16000")
                )
                _, comeback = await self._receive_turn(session)
                conversation_log.append({
                    "role": "assistant",
                    "content": comeback or "[audio comeback]"
                })
                exchanges_count = i + 1

        return {
            "conversation_history": conversation_log,
            "exchanges_count":      exchanges_count,
        }

    # --------------------------------------------------------------------
    # Interaction orchestration
    # --------------------------------------------------------------------

    def run_interaction(self):
        print("\n" + "=" * 50)
        print("Starting new interaction...")
        print("=" * 50)

        timestamp = datetime.now().isoformat()
        self.last_interaction_time = time.time()

        pil_image, image_bytes = self.capture_image()

        # Bridge sync→async for the Live session
        result = asyncio.run(self._live_session(image_bytes))

        print("\nInteraction complete!")
        self._save_trace(pil_image, {
            "timestamp":            timestamp,
            "model":                MODEL,
            "conversation_history": result["conversation_history"],
            "exchanges_count":      result["exchanges_count"],
            "mode":                 "auto" if self.auto_detect else "manual",
        })

    def _save_trace(self, pil_image: Image.Image, data: dict):
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"roast_{ts}"

        img_path = self.traces_dir / f"{base}.jpg"
        pil_image.save(img_path, format="JPEG", quality=85)
        print(f"✓ Saved image: {img_path}")

        json_path = self.traces_dir / f"{base}.json"
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✓ Saved trace: {json_path}")

    # --------------------------------------------------------------------
    # Main run loop
    # --------------------------------------------------------------------

    def run(self):
        print("\n🎃 Halloween Roaster is running! 🎃")
        print("Press Ctrl+C to exit")
        if self.auto_detect:
            print(f"\n🤖 AUTO-DETECT MODE — cooldown: {self.cooldown_seconds}s")
            self._run_auto_detect()
        else:
            print("\n👤 MANUAL MODE")
            self._run_manual()

    def _run_auto_detect(self):
        try:
            while True:
                if self.is_cooldown_active():
                    rem = int(self.cooldown_seconds - (time.time() - self.last_interaction_time))
                    if rem % 10 == 0 or rem <= 5:
                        print(f"Cooldown: {rem}s remaining...", end="\r")
                    time.sleep(1)
                    continue
                if self.detect_person():
                    print("\n👻 Person detected! Starting interaction...")
                    self.run_interaction()
                    print(f"\nMonitoring resumed (cooldown: {self.cooldown_seconds}s)...")
                else:
                    print("Monitoring for trick-or-treaters...", end="\r")
                    time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.cleanup()

    def _run_manual(self):
        try:
            while True:
                input("Press Enter when someone arrives (or Ctrl+C to exit)...")
                self.run_interaction()
                print("\nReady for next person...")
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.cleanup()

    def cleanup(self):
        print("Cleaning up...")
        self.cap.release()
        self.pa.terminate()
        print("Goodbye! 🎃")


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------

def main():
    import argparse

    print("🎃 Halloween Costume Roaster 🎃")
    print("Powered by Gemini 3.1 Flash Live")
    print("=================================\n")

    parser = argparse.ArgumentParser(
        description="Halloween Costume Roaster — real-time voice via Gemini 3.1 Flash Live",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 halloween_roaster.py              # Auto-detect mode (default)
  python3 halloween_roaster.py --manual     # Press Enter to trigger each roast
  python3 halloween_roaster.py --cooldown 90
        """,
    )
    parser.add_argument("--manual",   action="store_true", help="Disable auto-detection")
    parser.add_argument("--cooldown", type=int, default=60,
                        help="Seconds between detections (default: 60)")
    args = parser.parse_args()

    try:
        roaster = HalloweenRoaster(
            auto_detect=not args.manual,
            cooldown_seconds=args.cooldown,
        )
        roaster.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as exc:
        print(f"\nError: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
