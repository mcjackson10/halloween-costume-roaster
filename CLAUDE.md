# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Raspberry Pi 5 project that uses computer vision and AI to recognize Halloween costumes, roast trick-or-treaters with witty comments, and engage in real-time voice banter. Features two-stage automatic person detection (motion + YOLO11n) and supports both manual and autonomous modes. Uses **Google Gemini 3.1 Flash Live** for vision analysis, conversation generation, and real-time audio streaming. Saves interaction traces (images + conversation logs) locally for offline analysis.

## Development Commands

### Setup
```bash
# Initial setup (Raspberry Pi)
./setup.sh

# Or manual virtual environment setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Auto-detect mode (default) - automatically detects people
python3 halloween_roaster.py

# Manual mode - press Enter to trigger
python3 halloween_roaster.py --manual

# Custom cooldown (seconds between detections)
python3 halloween_roaster.py --cooldown 90

# View all options
python3 halloween_roaster.py --help
```

### Testing
```bash
# Test all components
python3 test_components.py

# Test person detection logic (unit tests, no hardware required)
python3 test_person_detection.py

# Test individual hardware components
arecord -d 5 test.wav                # Test microphone
aplay test.wav                       # Test speaker
```

### Configuration
```bash
# Set API key (required) — get a free key at https://aistudio.google.com/app/apikey
export GOOGLE_API_KEY="your-key-here"

# Or create .env file (either variable name works)
echo 'GOOGLE_API_KEY=your-key-here' > .env
# Alternative:
echo 'GEMINI_API_KEY=your-key-here' > .env
```

## Architecture

### Single-Class Design
The entire application is contained in the `HalloweenRoaster` class (halloween_roaster.py:67-468). This monolithic design was chosen for simplicity and ease of deployment on a Raspberry Pi.

### Module-Level Constants (halloween_roaster.py:38-64)

```python
MIC_RATE     = 16000   # Gemini Live expects 16 kHz PCM input
SPEAKER_RATE = 24000   # Gemini Live outputs 24 kHz PCM
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS     = 1
CHUNK        = 1024
MODEL        = "gemini-3.1-flash-live-preview"
SYSTEM_PROMPT = "..."  # ~1200-char personality prompt
```

### Core Components

1. **Constructor / Initialization** (halloween_roaster.py:68-113)
   - Loads `GOOGLE_API_KEY` or `GEMINI_API_KEY` from `.env`
   - Creates `genai.Client` for Gemini API
   - Initializes PyAudio for audio I/O
   - Opens USB camera via OpenCV `VideoCapture(0, CAP_V4L2)` at 1920x1080/30fps (MJPEG)
   - Flushes 5 warm-up frames and waits 1s before use
   - Conditionally initializes two-stage person detection

2. **Two-Stage Person Detection** (halloween_roaster.py:119-161)
   - Stage 1 — Motion (`detect_motion`, line 139): MOG2 background subtractor; triggers if any contour area > 5000 px
   - Stage 2 — Person (`detect_person`, line 147): YOLO11n with confidence threshold 0.4, class filter `[0]` (person), imgsz 320
   - Initialization (`_init_detection`, line 119): Attempts NCNN export of YOLO11n for faster CPU inference; falls back to standard PyTorch model on failure

3. **Cooldown System** (halloween_roaster.py:163-166)
   - `is_cooldown_active()` checks elapsed time since `last_interaction_time`
   - Default 60 seconds, configurable via `--cooldown` flag
   - Countdown printed every 10s and during final 5s

4. **Camera Capture** (halloween_roaster.py:172-182)
   - `capture_image()` reads a frame from the OpenCV capture
   - Converts BGR → RGB → PIL Image → JPEG bytes (quality=85)
   - Returns `(PIL Image, raw JPEG bytes)` tuple

5. **Audio I/O with PyAudio** (halloween_roaster.py:188-247)
   - **Playback** (`_play_worker`, line 188): Background thread consuming a `queue.Queue` of raw 24 kHz PCM chunks and writing them to the speaker stream in real time
   - **Recording** (`record_pcm`, line 207): Records from mic at 16 kHz; stops after `silence_timeout` (2.0s default) of sub-threshold audio (RMS < 300); returns `None` if no speech detected

6. **Gemini Live Session** (halloween_roaster.py:253-379)
   - **`_receive_turn(session)`** (line 253, async): Consumes one complete model turn; spawns playback thread for real-time audio output; collects audio bytes + output transcription; times out after 30s
   - **`_live_session(image_bytes)`** (line 301, async): Opens a single WebSocket session via `client.aio.live.connect()`; sends costume image + text prompt for the initial roast; runs up to 3 voice exchange rounds; sends raw mic PCM directly to Gemini (no STT step); signals end-of-user-audio with `audio_stream_end=True`

7. **Interaction Orchestration** (halloween_roaster.py:385-418)
   - `run_interaction()` (line 385): Captures image, bridges sync→async with `asyncio.run(_live_session(...))`, saves trace
   - `_save_trace()` (line 407): Writes `traces/roast_YYYYMMDD_HHMMSS.jpg` and `traces/roast_YYYYMMDD_HHMMSS.json`

8. **Main Loop** (halloween_roaster.py:424-468)
   - `run()` (line 424): Delegates to `_run_auto_detect()` or `_run_manual()`
   - `_run_auto_detect()` (line 434): Polls with 0.5s sleep; detects person after cooldown expires; triggers `run_interaction()`
   - `_run_manual()` (line 454): Blocks on `input()` waiting for Enter; no cooldown enforced
   - `cleanup()` (line 464): Releases OpenCV capture and terminates PyAudio

### Interaction Flow

**Auto-Detect Mode** (default):
1. Continuous camera monitoring (0.5s poll interval)
2. When cooldown has expired and a person is detected:
   - Capture 1920x1080 JPEG
   - Open Gemini Live WebSocket session
   - Send image + trigger text → receive and play roast audio
   - Up to 3 voice exchanges: record mic → send PCM to Gemini → play comeback audio
   - If no response on first exchange: send snarky farewell prompt → play farewell
3. Save trace files; start cooldown timer; resume monitoring

**Manual Mode** (`--manual` flag):
1. Wait for user to press Enter
2. Same interaction flow as auto-detect
3. No cooldown enforced

### Gemini Live Session Configuration

```python
config = {
    "response_modalities": ["AUDIO"],
    "speech_config": {
        "voice_config": {
            "prebuilt_voice_config": {"voice_name": "Charon"}  # deep/dramatic
        }
    },
    "system_instruction": SYSTEM_PROMPT,
    "thinking_config": {"thinking_level": "minimal"},  # lowest latency
    "output_audio_transcription": {},  # enables transcript for trace files
}
```

### Trace File Generation (halloween_roaster.py:407-418)

After each interaction, two files are written to `traces/`:

**`roast_YYYYMMDD_HHMMSS.jpg`** (~400 KB)
- 1920x1080 JPEG at 85% quality

**`roast_YYYYMMDD_HHMMSS.json`** (~3 KB)
```json
{
  "timestamp": "2024-10-31T20:15:30.123456",
  "model": "gemini-3.1-flash-live-preview",
  "conversation_history": [
    {"role": "assistant", "content": "roast text or [audio roast]"},
    {"role": "user",      "content": "[voice]"},
    {"role": "assistant", "content": "comeback text or [audio comeback]"}
  ],
  "exchanges_count": 1,
  "mode": "auto"
}
```

## Key Implementation Details

### API Usage
- **Model**: `gemini-3.1-flash-live-preview` for vision, conversation, STT, and TTS
- **Single connection per interaction**: one WebSocket session handles everything
- **Audio format in**: 16 kHz, 16-bit, mono PCM (`audio/pcm;rate=16000`)
- **Audio format out**: 24 kHz, 16-bit, mono PCM
- **No separate STT step**: raw mic audio goes directly to Gemini
- **No separate TTS step**: Gemini streams audio back in real time

### Hardware Dependencies
- **Camera**: USB camera via OpenCV `VideoCapture` (not Picamera2/CSI)
  - Tested with Arducam 4K 8MP IMX219 USB
  - Opens as `/dev/video0` with `CAP_V4L2` backend and `MJPG` codec
- **Person Detection**: OpenCV MOG2 + YOLO11n (via `ultralytics`)
- **Microphone**: Direct PyAudio stream at 16 kHz
- **Speaker**: Direct PyAudio stream at 24 kHz

### State Management
- `self.client`: Gemini API client (persistent across interactions)
- `self.cap`: OpenCV VideoCapture (persistent)
- `self.pa`: PyAudio instance (persistent)
- `self.auto_detect`: Boolean for mode selection
- `self.cooldown_seconds`: Configurable cooldown duration
- `self.last_interaction_time`: Timestamp for cooldown tracking
- `self.traces_dir`: `Path("traces")` for output files
- `self.bg_subtractor`, `self.person_model`: Detection objects (auto-detect only)
- Conversation history is **local to each `_live_session()` call** — no instance-level conversation state persists between interactions

### Error Handling
- Missing API key: raises `ValueError` at init
- Camera not found: raises `RuntimeError` at init
- Gemini response timeout: prints warning, moves on (30s limit per turn)
- No user speech detected: returns `None` from `record_pcm()`; triggers farewell on first exchange, skips subsequent exchanges
- YOLO11n NCNN export failure: falls back to standard model silently

## Customization Points

### Person Detection Sensitivity
- Motion threshold: `self.motion_threshold = 5000` (halloween_roaster.py:124) — lower to detect smaller motion
- YOLO11n confidence: `self.person_confidence_threshold = 0.4` (halloween_roaster.py:125) — lower for more detections
- YOLO11n input size: `imgsz=320` in `detect_person()` (halloween_roaster.py:154) — higher for accuracy, lower for speed

### Roast Personality
- System prompt: `SYSTEM_PROMPT` constant (halloween_roaster.py:52-64)
- Voice: `"voice_name": "Charon"` in `_live_session()` (halloween_roaster.py:311) — other options: Puck, Kore, Fenrir, Aoede, etc.

### Conversation Length
- Change `range(3)` in `_live_session()` (halloween_roaster.py:341) to allow more/fewer exchanges

### Timeouts
- Per-turn Gemini response timeout: `timeout=30.0` in `_receive_turn()` (halloween_roaster.py:253)
- Max mic recording: `max_seconds=8` in `record_pcm()` calls (halloween_roaster.py:343)
- Silence detection: `silence_timeout=2.0` in `record_pcm()` calls (halloween_roaster.py:343)
- Silence RMS threshold: `silence_rms = 300` (halloween_roaster.py:221) — raise if background is noisy

### Cooldown Duration
- Default: 60 seconds
- Command line: `--cooldown <seconds>`

### Operating Mode
- Auto-detect (default): Continuous monitoring with YOLO11n
- Manual mode: `--manual` flag for Enter key trigger

## Testing Strategy

**`test_components.py`** tests each subsystem independently:
1. Package imports
2. API key configuration (checks for `GOOGLE_API_KEY` / `GEMINI_API_KEY`)
3. Camera (hardware test)
4. Microphone availability
5. Audio output and TTS
6. Gemini API connectivity

**`test_person_detection.py`** runs logic-only unit tests (no hardware required):
1. Cooldown timing logic
2. Mode selection (auto vs manual)
3. Detection parameter validation

Run `test_components.py` before deploying to catch configuration issues early.

## Raspberry Pi Specific Notes

- USB camera connects as `/dev/video0`; confirm with `ls /dev/video*`
- Bluetooth speaker pairs via `bluetoothctl`; PulseAudio routes audio
- YOLO11n NCNN export speeds up inference on CPU — requires `ultralytics` package
- System dependencies installed via apt (see setup.sh)
- OpenCV requires system libraries (`libopencv-dev`, `python3-opencv`)
- Virtual environment recommended to avoid system Python conflicts
- Systemd service file (`halloween-roaster.service`) available for auto-start on boot

## API Key Security

- Never commit API keys to repository
- Use environment variables or `.env` file
- Both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are accepted (halloween_roaster.py:75)
- Get a free key at https://aistudio.google.com/app/apikey
