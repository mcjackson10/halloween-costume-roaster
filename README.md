# 🎃 Halloween Costume Roaster

A fun Raspberry Pi 5 project that uses computer vision and AI to recognize Halloween costumes, roast trick-or-treaters with witty comments, and engage in playful banter through voice interaction.

## Features

- **Automatic Person Detection**: Uses OpenCV computer vision to continuously monitor for trick-or-treaters (~2 FPS)
- **Intelligent Cooldown System**: Prevents re-roasting the same person (default 60s, configurable)
- **Dual Operating Modes**: Auto-detect (default) or manual trigger mode
- **Costume Recognition**: Uses GPT-4o mini with vision capabilities to identify and analyze costumes
- **Witty Roasts**: Generates funny, family-friendly roasts about costumes
- **Voice Interaction**: Listens for responses and engages in back-and-forth conversation
- **Audio Output**: Speaks responses through a Bluetooth speaker
- **Camera Integration**: Captures photos using Raspberry Pi Camera Module
- **Trace File Generation**: Automatically saves interaction logs (image + conversation JSON) for offline analysis
- **Google Drive Integration**: Optional cloud upload of trace files to preserve Raspberry Pi storage

## Hardware Requirements

- Raspberry Pi 5
- Raspberry Pi Camera Module (v2 or v3 recommended)
- USB Microphone or compatible microphone
- Bluetooth Speaker (paired with Raspberry Pi)
- Power supply for Raspberry Pi

## Software Requirements

- Raspberry Pi OS (64-bit recommended)
- Python 3.9 or higher
- OpenCV 4.8 or higher (for person detection)
- Active internet connection (for LLM API calls and speech recognition)
- OpenAI API key

## Setup Instructions

### 1. Hardware Setup

**Camera Module:**
```bash
# Enable camera interface
sudo raspi-config
# Navigate to Interface Options > Camera > Enable

# Verify camera is detected
libcamera-hello --list-cameras
```

**Bluetooth Speaker:**
```bash
# Pair Bluetooth speaker
bluetoothctl
# In bluetoothctl:
# - scan on
# - pair <SPEAKER_MAC_ADDRESS>
# - connect <SPEAKER_MAC_ADDRESS>
# - trust <SPEAKER_MAC_ADDRESS>
# - exit

# Set as default audio output
pactl set-default-sink <SPEAKER_NAME>
```

**Microphone:**
```bash
# List audio devices
arecord -l

# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

### 2. Software Installation

**Update System:**
```bash
sudo apt update && sudo apt upgrade -y
```

**Install System Dependencies:**
```bash
# Install required system packages
sudo apt install -y python3-pip python3-picamera2 \
    portaudio19-dev python3-pyaudio \
    libcamera-dev libatlas-base-dev \
    ffmpeg libopencv-dev python3-opencv

# Install additional audio dependencies
sudo apt install -y pulseaudio pulseaudio-utils
```

**Install Python Dependencies:**
```bash
# Navigate to project directory
cd /path/to/Halloween

# Install Python packages
pip3 install -r requirements.txt
```

### 3. Configuration

**Set up API Key:**
```bash
# Add to ~/.bashrc or ~/.profile
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# Or create a .env file in the project directory
echo 'OPENAI_API_KEY=your-api-key-here' > .env
```

**Get OpenAI API Key:**
1. Sign up at https://platform.openai.com/
2. Navigate to API Keys section
3. Create a new API key
4. Copy and use in the configuration above

### 4. Test Components

**Test Camera:**
```bash
libcamera-still -o test.jpg
```

**Test Microphone:**
```bash
python3 -c "import speech_recognition as sr; r = sr.Recognizer(); m = sr.Microphone(); print('Microphone initialized successfully')"
```

**Test Speaker:**
```bash
python3 -c "from gtts import gTTS; import pygame; pygame.mixer.init(); tts = gTTS('Testing speaker'); tts.save('test.mp3'); pygame.mixer.music.load('test.mp3'); pygame.mixer.music.play(); import time; time.sleep(2)"
```

## Usage

### Running the Program

**Auto-Detect Mode (Default):**
```bash
# Automatically detects when people arrive
python3 halloween_roaster.py

# With custom cooldown (default is 60 seconds)
python3 halloween_roaster.py --cooldown 90

# With Google Drive upload (saves traces to cloud, deletes local copies)
python3 halloween_roaster.py --gdrive gdrive_credentials.json

# Combined flags
python3 halloween_roaster.py --cooldown 90 --gdrive gdrive_credentials.json
```

**Manual Mode:**
```bash
# Press Enter to trigger roasts manually
python3 halloween_roaster.py --manual

# Manual mode with Google Drive
python3 halloween_roaster.py --manual --gdrive gdrive_credentials.json
```

**View All Options:**
```bash
python3 halloween_roaster.py --help
```

### How It Works

**Auto-Detect Mode (Default):**
1. **Start the program** - System initializes camera, microphone, speaker, and person detection
2. **Continuous monitoring** - OpenCV monitors camera feed at ~2 FPS for people
3. **Person detected** - When someone enters the frame AND cooldown has expired:
   - **Camera captures** a high-resolution photo of their costume
   - **AI analyzes** the costume and generates a witty roast
   - **Roast is spoken** through the Bluetooth speaker
   - **System listens** for a response (8 second timeout)
   - **If they respond**, the AI generates a comeback and banter continues (up to 3 exchanges)
   - **Trace files saved** - Image and conversation log stored locally (or uploaded to Google Drive if enabled)
4. **Cooldown starts** - 60-second timer prevents re-roasting the same person
5. **Resume monitoring** - System returns to watching for the next trick-or-treater

**Manual Mode:**
1. **Start the program** - System initializes camera, microphone, and speaker
2. **Press Enter** when a trick-or-treater arrives
3. **Same interaction flow** as auto-detect (capture, analyze, roast, converse, save traces)
4. **Repeat** - Press Enter for the next person (no cooldown enforced)

### Example Interaction

```
Trick-or-treater: *arrives in skeleton costume*
System: "Oh look, a skeleton! Did you raid your biology classroom or just give up on creativity?
         At least your costume has more personality than you do!"

Trick-or-treater: "Hey, skeletons are classic!"
System: "Classic? Sure, if by classic you mean the same thing every third kid is wearing tonight!
         But hey, at least you'll blend in with the other 47 skeletons I'll see tonight!"
```

## Troubleshooting

### Camera Issues
```bash
# Check camera connection
vcgencmd get_camera

# Ensure camera is enabled in config
sudo raspi-config
```

### Audio Issues
```bash
# Check audio devices
aplay -l
pactl list sinks

# Restart pulseaudio
pulseaudio -k
pulseaudio --start
```

### Microphone Not Working
```bash
# Test with alsa
arecord -l
arecord -D hw:1,0 -d 5 -f cd test.wav

# Adjust microphone levels
alsamixer
```

### API Errors
- Verify API key is set correctly: `echo $OPENAI_API_KEY`
- Check internet connection
- Verify API credits at https://platform.openai.com/usage

### Speech Recognition Errors
- Ensure internet connection (Google Speech Recognition requires internet)
- Check microphone sensitivity in `alsamixer`
- Adjust ambient noise calibration in code if needed

## Customization

### Person Detection Sensitivity

Edit detection parameters in `halloween_roaster.py` (lines 122-127):

```python
# Adjust these values in the detect_person() method
people = cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,      # Lower = more sensitive (1.05-1.3)
    minNeighbors=3,       # Lower = more detections (2-5)
    minSize=(100, 100)    # Minimum person size in pixels
)
```

### Cooldown Duration

```bash
# Via command line (recommended)
python3 halloween_roaster.py --cooldown 90  # 90 seconds

# Or edit default in code (halloween_roaster.py, line ~50)
```

### Adjust Roast Style

Edit the prompts in `halloween_roaster.py`:

```python
# Line ~158 - Initial roast prompt
"text": "You are a snarky, witty Halloween costume critic..."

# Line ~206 - Conversation prompt
system_prompt = """You are a snarky, witty Halloween character..."""
```

### Change Conversation Length

Modify the range in line ~274:
```python
for i in range(3):  # Change 3 to desired number of exchanges
```

### Adjust Listening Timeout

Change timeout values (line ~276):
```python
user_speech = self.listen_for_speech(timeout=8)  # Seconds to wait
```

## Trace Files and Cloud Storage

### What Are Trace Files?

After each interaction, the system automatically saves detailed logs for offline analysis:

**Files Generated:**
- **Image**: `roast_YYYYMMDD_HHMMSS.jpg` (~400 KB)
  - 1920x1080 JPEG of the trick-or-treater
  - 85% quality (good balance of size/quality)

- **JSON Log**: `roast_YYYYMMDD_HHMMSS.json` (~3 KB)
  - Timestamp (ISO 8601 format)
  - Costume description from vision API
  - Complete conversation history
  - Number of exchanges
  - Operating mode (auto/manual)

**Total storage: ~500 KB per trick-or-treater**

### Storage Options

**1. Local Storage (Default)**
```bash
# Files saved to traces/ directory
python3 halloween_roaster.py
```
- Files remain on Raspberry Pi
- Must manually manage storage
- Good for testing or when internet is unavailable

**2. Google Drive Upload (Recommended for Halloween Night)**
```bash
# Automatically upload to cloud and delete local copies
python3 halloween_roaster.py --gdrive gdrive_credentials.json
```
- Files uploaded to Google Drive after each interaction
- Local copies deleted automatically after successful upload
- Preserves Raspberry Pi storage (important for long nights!)
- Requires one-time Google Drive setup (see below)

### Google Drive Setup (Optional)

For automatic trace file uploads to preserve Raspberry Pi storage:

**Quick Steps:**
1. Follow complete instructions in `GOOGLE_DRIVE_SETUP.md`
2. Create Google Cloud project and enable Drive API
3. Create service account and download credentials JSON
4. Share a Google Drive folder with the service account email
5. Run with `--gdrive gdrive_credentials.json` flag

**Benefits:**
- Preserves Raspberry Pi storage on busy Halloween nights
- Access trace files from any device
- Automatic backup of all interactions
- Graceful fallback if upload fails (keeps local files)

**Security Note:**
- Never commit `gdrive_credentials.json` to Git
- Keep credentials file secure (contains API access)
- Service account only has access to shared folder

## Advanced Configuration

### Auto-start on Boot

Create a systemd service:
```bash
sudo nano /etc/systemd/system/halloween-roaster.service
```

Add:
```ini
[Unit]
Description=Halloween Costume Roaster
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Halloween
Environment="OPENAI_API_KEY=your-key-here"
ExecStart=/usr/bin/python3 /home/pi/Halloween/halloween_roaster.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable halloween-roaster
sudo systemctl start halloween-roaster
```

## Cost Considerations

- OpenAI GPT-4o mini API calls are very cost-effective
- Each interaction uses approximately 2-4 API calls
- Image analysis: ~$0.0002-0.0005 per image
- Text generation: ~$0.0001-0.0002 per response
- Budget approximately $0.0007 per trick-or-treater (~$0.07 for 100 people)
- **95% cheaper than Claude 3.5 Sonnet**

## Safety and Privacy

- Images are sent to OpenAI's API for analysis
- Consider adding a privacy notice for visitors
- **Trace files**: Images and conversation logs are saved locally or uploaded to Google Drive
  - Local: Stored in `traces/` directory (~500 KB per visitor)
  - Cloud: Uploaded to Google Drive and local copies deleted
  - Contains: Photo, timestamp, costume description, conversation
- Speech is processed by Google's Speech Recognition API
- **Privacy considerations**: Inform visitors about photo capture and data storage

## License

This project is provided as-is for educational and entertainment purposes.

## Credits

- Built with OpenAI's GPT-4o mini
- Uses Google Speech Recognition
- Text-to-speech via gTTS

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Raspberry Pi camera documentation
3. Check OpenAI API documentation

Happy Halloween! 🎃👻
