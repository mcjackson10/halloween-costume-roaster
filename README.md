# 🎃 Halloween Costume Roaster

A fun Raspberry Pi 5 project that uses computer vision and AI to recognize Halloween costumes, roast trick-or-treaters with witty comments, and engage in playful banter through voice interaction.

## Features

- **Costume Recognition**: Uses GPT-4o mini with vision capabilities to identify and analyze costumes
- **Witty Roasts**: Generates funny, family-friendly roasts about costumes
- **Voice Interaction**: Listens for responses and engages in back-and-forth conversation
- **Audio Output**: Speaks responses through a Bluetooth speaker
- **Camera Integration**: Captures photos using Raspberry Pi Camera Module

## Hardware Requirements

- Raspberry Pi 5
- Raspberry Pi Camera Module (v2 or v3 recommended)
- USB Microphone or compatible microphone
- Bluetooth Speaker (paired with Raspberry Pi)
- Power supply for Raspberry Pi

## Software Requirements

- Raspberry Pi OS (64-bit recommended)
- Python 3.9 or higher
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
    ffmpeg

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

```bash
python3 halloween_roaster.py
```

### How It Works

1. **Start the program** - The system initializes camera, microphone, and speaker
2. **Press Enter** when a trick-or-treater arrives
3. **Camera captures** a photo of their costume
4. **AI analyzes** the costume and generates a witty roast
5. **Roast is spoken** through the Bluetooth speaker
6. **System listens** for a response (8 second timeout)
7. **If they respond**, the AI generates a comeback and the banter continues (up to 3 exchanges)
8. **Repeat** for the next person

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

### Adjust Roast Style

Edit the prompts in `halloween_roaster.py`:

```python
# Line 85 - Initial roast prompt
"text": "You are a snarky, witty Halloween costume critic..."

# Line 127 - Conversation prompt
system_prompt = """You are a snarky, witty Halloween character..."""
```

### Change Conversation Length

Modify the range in line 164:
```python
for i in range(3):  # Change 3 to desired number of exchanges
```

### Adjust Listening Timeout

Change timeout values:
```python
user_speech = self.listen_for_speech(timeout=8)  # Seconds to wait
```

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

### Motion Detection

For automatic triggering when someone approaches, you could add a PIR motion sensor and modify the code to trigger on motion instead of manual Enter press.

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
- Images are not saved locally by default
- Speech is processed by Google's Speech Recognition API

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
