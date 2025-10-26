# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Raspberry Pi 5 project that uses computer vision and AI to recognize Halloween costumes, roast trick-or-treaters with witty comments, and engage in playful banter through voice interaction. Features automatic person detection using OpenCV and supports both manual and autonomous modes. Uses OpenAI's GPT-4o mini for vision analysis and conversation generation. Includes optional Google Drive integration to automatically save interaction traces (images + conversation logs) to the cloud for offline analysis while preserving local storage.

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

# Enable Google Drive upload (saves traces to cloud, deletes local copies)
python3 halloween_roaster.py --gdrive gdrive_credentials.json

# Combined flags
python3 halloween_roaster.py --cooldown 90 --gdrive gdrive_credentials.json

# View all options
python3 halloween_roaster.py --help
```

### Testing
```bash
# Test all components
python3 test_components.py

# Test individual hardware components
libcamera-still -o test.jpg          # Test camera
arecord -d 5 test.wav                # Test microphone
aplay test.wav                       # Test speaker
```

### Configuration
```bash
# Set API key (required)
export OPENAI_API_KEY="your-key-here"

# Or create .env file
echo 'OPENAI_API_KEY=your-key-here' > .env
```

## Architecture

### Single-Class Design
The entire application is contained in the `HalloweenRoaster` class (halloween_roaster.py:23-351). This monolithic design was chosen for simplicity and ease of deployment on a Raspberry Pi.

### Core Components

1. **Camera Integration** (halloween_roaster.py:87-103)
   - Uses Picamera2 for Raspberry Pi camera
   - Captures 1920x1080 images for roasts
   - Converts to PIL Image and base64 for API transmission

2. **Person Detection** (halloween_roaster.py:105-129)
   - OpenCV Haar Cascade for detecting people in frame
   - Continuous monitoring at ~2 FPS (0.5s intervals)
   - Uses fullbody or upperbody cascade classifiers
   - Min size 100x100px to avoid false positives

3. **Cooldown System** (halloween_roaster.py:131-137)
   - Prevents re-roasting same person multiple times
   - Default 60 seconds, configurable via `--cooldown` flag
   - Tracks `last_interaction_time` timestamp

4. **Vision Analysis** (halloween_roaster.py:139-172)
   - Sends base64-encoded images to GPT-4o mini vision API
   - Single API call per costume with image + text prompt
   - Generates family-friendly roasts (max 3 sentences)

5. **Voice Interaction** (halloween_roaster.py:174-196)
   - Google Speech Recognition via `speech_recognition` library
   - Configurable timeout (default 8s for responses)
   - Adjusts for ambient noise on initialization

6. **Conversation Management** (halloween_roaster.py:197-224)
   - Maintains conversation history in `self.conversation_history`
   - Up to 3 exchanges per trick-or-treater (halloween_roaster.py:274)
   - Stateless between different visitors

7. **Audio Output** (halloween_roaster.py:246-272)
   - gTTS for text-to-speech generation
   - pygame for audio playback to Bluetooth speaker
   - Uses temporary files (auto-cleaned)

8. **Trace File Generation** (halloween_roaster.py:274-299)
   - Saves interaction data as JSON + image
   - Timestamp-based filenames (roast_YYYYMMDD_HHMMSS)
   - Local storage in `traces/` directory
   - ~500 KB per interaction (image + JSON)

9. **Google Drive Integration** (google_drive_uploader.py, optional)
   - Service Account authentication
   - Automatic folder creation/discovery
   - Upload multiple files per interaction
   - Automatic cleanup after successful upload
   - Graceful fallback if upload fails
   - Initialized only when `--gdrive` flag provided

### Interaction Flow

**Auto-Detect Mode** (default):
1. Continuous camera monitoring (0.5s intervals)
2. When person detected AND cooldown expired:
   - Trigger `run_interaction()` automatically
   - Capture high-res image → Analyze costume → Speak roast
   - Listen for response (8s timeout)
   - Generate comeback if they respond
   - Repeat up to 3 times
3. Start cooldown timer, resume monitoring
4. Conversation history resets for next person

**Manual Mode** (`--manual` flag):
1. Wait for user to press Enter
2. Same interaction flow as auto-detect
3. No cooldown enforced

### Trace File Generation

After each interaction, the system saves detailed logs for offline analysis:

**Files Generated:**
1. **Image**: `roast_YYYYMMDD_HHMMSS.jpg` (~400 KB)
   - 1920x1080 JPEG of the trick-or-treater
   - 85% quality (good balance of size/quality)

2. **JSON Log**: `roast_YYYYMMDD_HHMMSS.json` (~3 KB)
   - Timestamp (ISO 8601 format)
   - Costume description from vision API
   - Complete conversation history
   - Number of exchanges
   - Operating mode (auto/manual)

**Storage Options:**

1. **Local Only** (default):
   - Files saved to `traces/` directory
   - Must manually manage storage
   - Use for testing or when internet is unavailable

2. **Google Drive Upload** (`--gdrive` flag):
   - Files uploaded to cloud after each interaction
   - Local copies deleted automatically after successful upload
   - Preserves Raspberry Pi storage
   - Requires Google Drive service account credentials
   - See `GOOGLE_DRIVE_SETUP.md` for detailed setup instructions

**Implementation:**
- Trace generation: halloween_roaster.py:274-299
- Google Drive upload: halloween_roaster.py:301-335
- Integration point: halloween_roaster.py:379-392

## Key Implementation Details

### API Usage
- **Model**: `gpt-4o-mini` for both vision and text
- **Vision call**: Image + text prompt, max 1024 tokens
- **Text calls**: Conversation history + system prompt
- **Cost**: ~$0.0007 per trick-or-treater

### Hardware Dependencies
- **Camera**: Picamera2 library (Raspberry Pi specific)
- **Person Detection**: OpenCV with Haar Cascade classifiers
- **Microphone**: Via `speech_recognition` library
- **Speaker**: Bluetooth via pygame mixer
- All require specific Raspberry Pi setup (see README.md:29-65)

### State Management
- `self.conversation_history`: List of messages for current person
- `self.current_costume`: Last analyzed costume description
- `self.last_interaction_time`: Timestamp for cooldown tracking
- `self.auto_detect`: Boolean for mode selection
- `self.cooldown_seconds`: Configurable cooldown duration
- `self.drive_uploader`: GoogleDriveUploader instance (None if disabled)
- `self.traces_dir`: Path to local traces directory (Path object)
- Conversation history resets at start of each `run_interaction()`

### Error Handling
- Camera/API errors are fatal (raised exceptions)
- Speech recognition timeouts are graceful (returns None)
- Audio errors during playback are handled with cleanup
- Google Drive upload failures are non-fatal (keeps local files as backup)
- Missing credentials file prints warning and continues without upload

## Customization Points

### Person Detection Sensitivity
- Haar Cascade parameters at halloween_roaster.py:122-127
- `scaleFactor`: Lower = more sensitive (1.05-1.3)
- `minNeighbors`: Lower = more detections (2-5)
- `minSize`: Minimum person size in pixels

### Cooldown Duration
- Default: 60 seconds
- Command line: `--cooldown <seconds>`
- Prevents re-roasting same trick-or-treater

### Roast Style
- Initial roast prompt: halloween_roaster.py:158
- Conversation system prompt: halloween_roaster.py:206-208

### Conversation Length
- Change `range(3)` at halloween_roaster.py:274

### Timeouts
- Speech listening: `listen_for_speech(timeout=8)` at halloween_roaster.py:276
- Phrase time limit: halloween_roaster.py:180
- Person detection check interval: halloween_roaster.py:328 (0.5s)

### Farewell Message
- When no response to initial roast: halloween_roaster.py:281

### Operating Mode
- Auto-detect (default): Continuous monitoring
- Manual mode: `--manual` flag for Enter key trigger

## Testing Strategy

The `test_components.py` script tests each subsystem independently:
1. Package imports
2. API key configuration
3. Camera (Raspberry Pi only)
4. Microphone availability
5. Audio output and TTS
6. OpenAI API connectivity

Run this before deploying to catch configuration issues early.

## Raspberry Pi Specific Notes

- Camera must be enabled via `raspi-config`
- Bluetooth speaker requires pairing via `bluetoothctl`
- PulseAudio manages audio routing
- System dependencies installed via apt (see setup.sh:25-35)
- OpenCV requires system libraries (`libopencv-dev`, `python3-opencv`)
- Virtual environment recommended to avoid system Python conflicts
- Haar Cascade XML files included with OpenCV installation

## Google Drive Configuration (Optional)

For automatic trace file uploads to preserve Raspberry Pi storage:

1. **Setup**: Follow complete instructions in `GOOGLE_DRIVE_SETUP.md`
2. **Quick steps**:
   - Create Google Cloud project
   - Enable Drive API
   - Create service account
   - Download credentials JSON
   - Share folder with your personal Gmail
3. **Usage**: `python3 halloween_roaster.py --gdrive credentials.json`
4. **Storage**: ~500 KB per trick-or-treater uploaded to cloud
5. **Cleanup**: Local files deleted automatically after successful upload

Without `--gdrive` flag, files remain in local `traces/` directory.

## API Key Security

- Never commit API keys to repository
- Use environment variables or .env file
- API key validation happens at initialization (halloween_roaster.py:36-38)
- Never commit Google Drive credentials (gdrive_credentials.json) to repository
