# Halloween Costume Roaster - Project Summary

## Overview
A complete Raspberry Pi 5 system that uses AI vision and conversation to create an interactive Halloween experience. The system automatically detects trick-or-treaters using computer vision, captures photos of their costumes, analyzes them using OpenAI's GPT-4o mini, and engages in playful roasting banter through voice interaction. Features automatic trace file generation that saves interaction logs locally for offline analysis.

## Project Structure

```
Halloween/
├── halloween_roaster.py          # Main application (executable)
├── test_components.py            # Component testing utility (executable)
├── setup.sh                      # Automated setup script (executable)
├── requirements.txt              # Python dependencies
├── halloween-roaster.service     # Systemd service file for auto-start
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignore patterns
├── README.md                     # Complete documentation
├── QUICKSTART.md                 # Quick start guide
├── PROJECT_SUMMARY.md            # This file
├── ARCHITECTURE.md               # System architecture documentation
├── CLAUDE.md                     # Claude Code project instructions
└── traces/                       # Local trace files
    ├── roast_YYYYMMDD_HHMMSS.jpg
    └── roast_YYYYMMDD_HHMMSS.json
```

## Key Features

### 1. Automatic Person Detection
- Uses OpenCV with Haar Cascade classifiers
- Continuously monitors camera feed at ~2 FPS
- Auto-triggers interactions when people enter frame
- Intelligent cooldown system (default 60s, configurable)
- Dual modes: Auto-detect (default) or manual trigger

### 2. Computer Vision
- Uses Raspberry Pi Camera Module to capture costume photos
- Integrates with GPT-4o mini vision capabilities
- Analyzes costumes in real-time
- 1920x1080 high-resolution image capture

### 3. AI Conversation
- Generates witty, family-friendly roasts
- Maintains conversation context
- Supports up to 3 back-and-forth exchanges per person
- Uses GPT-4o mini for cost-effective interactions

### 4. Voice Interaction
- Speech recognition via microphone
- High-quality text-to-speech using OpenAI TTS (onyx voice for spooky effect)
- Adjustable listening timeouts (default 8s)
- Google Speech Recognition for accurate transcription

### 5. Trace File Generation
- Automatic logging of each interaction
- Saves high-res image (~400 KB JPEG)
- JSON conversation log (~3 KB)
- Timestamp-based filenames for easy sorting
- Local storage in `traces/` directory
- ~500 KB total storage per trick-or-treater

### 6. Hardware Integration
- Camera: Raspberry Pi Camera Module v2/v3
- Audio Input: USB or compatible microphone
- Audio Output: Bluetooth speaker
- Platform: Raspberry Pi 5

## Technical Stack

### Hardware
- Raspberry Pi 5
- Camera Module (v2 or v3)
- USB Microphone
- Bluetooth Speaker

### Software
- **Python 3.9+**
- **OpenAI API** (GPT-4o mini for vision/conversation, TTS-1 for voice)
- **OpenCV** - Person detection with Haar Cascades
- **picamera2** - Camera interface
- **SpeechRecognition** - Voice input
- **pygame** - Audio playback
- **PIL** - Image processing
- **python-dotenv** - Environment variable management

### External Services
- OpenAI API for AI vision, conversation, and text-to-speech
- Google Speech Recognition API for voice-to-text

## Installation Steps

1. **Hardware Setup**
   - Connect camera module
   - Connect USB microphone
   - Pair Bluetooth speaker

2. **Software Installation**
   ```bash
   ./setup.sh
   ```

3. **Configuration**
   - Copy `.env.example` to `.env`
   - Add OpenAI API key

4. **Testing**
   ```bash
   python3 test_components.py
   ```

5. **Run**
   ```bash
   python3 halloween_roaster.py
   ```

## Usage Flow

### Auto-Detect Mode (Default)
1. System initializes (camera, microphone, speaker, person detection)
2. OpenCV continuously monitors camera feed at ~2 FPS
3. When person detected AND cooldown expired:
   - Camera captures high-res photo
   - AI analyzes costume and generates roast
   - Roast is spoken through speaker
   - System listens for verbal response (8s timeout)
   - If response detected, AI generates comeback
   - Conversation continues (up to 3 exchanges)
   - Trace files saved locally
4. 60-second cooldown starts
5. System resumes monitoring for next person

### Manual Mode
1. System initializes (camera, microphone, speaker)
2. Operator presses Enter when trick-or-treater arrives
3. Same interaction flow as auto-detect
4. No cooldown enforced between interactions

## Cost Estimate

### Per Interaction (approximately)
Using OpenAI APIs (very cost-effective):
- Image analysis (GPT-4o mini): ~$0.0002-0.0005
- Text generation (GPT-4o mini, 3 responses): ~$0.0001-0.0002 per response
- Text-to-speech (TTS-1, ~4 audio clips): ~$0.00006 per clip
- **Total: ~$0.001 per trick-or-treater**

### For 100 Trick-or-Treaters
- **Estimated API cost: ~$0.10**

### Storage Costs
- Local: Free (uses Raspberry Pi storage)
  - 100 trick-or-treaters = ~50 MB
  - 1000 trick-or-treaters = ~500 MB

## Customization Options

### Personality/Tone
Edit prompts in `halloween_roaster.py`:
- Line 85: Initial roast prompt
- Line 127: Conversation system prompt

### Interaction Length
- Modify `for i in range(3)` on line 164
- Adjust timeout in `listen_for_speech()` calls

### Camera Settings
- Resolution: Line 38-39
- Warm-up time: Line 42

### Audio Settings
- Speech timeout: Line 107
- Phrase time limit: Line 107

## Advanced Features

### Auto-Start on Boot
```bash
sudo cp halloween-roaster.service /etc/systemd/system/
sudo systemctl enable halloween-roaster
sudo systemctl start halloween-roaster
```

### Motion Detection (Future Enhancement)
Add PIR sensor to auto-trigger instead of manual Enter press

### Logging
The service file includes journal logging:
```bash
journalctl -u halloween-roaster -f
```

## Troubleshooting Guide

### Camera Issues
- Check connection: `vcgencmd get_camera`
- Enable in config: `sudo raspi-config`
- Test: `libcamera-still -o test.jpg`

### Microphone Issues
- List devices: `arecord -l`
- Test recording: `arecord -d 5 test.wav`
- Adjust levels: `alsamixer`

### Speaker Issues
- Check Bluetooth: `bluetoothctl info`
- List sinks: `pactl list sinks`
- Set default: `pactl set-default-sink <name>`

### API Issues
- Verify key: `echo $OPENAI_API_KEY`
- Check credits: https://platform.openai.com/usage
- Test connection: Run `test_components.py`

## Safety & Privacy

- Images are sent to OpenAI API (encrypted in transit via HTTPS)
- **Trace files**: Images and conversation logs are saved locally
  - Stored in `traces/` directory
  - Contains: Photo, timestamp, costume description, full conversation
- Speech processed by Google Speech Recognition API
- Audio generated using OpenAI TTS API
- **Privacy notice recommended**: Inform visitors about photo capture and data storage
- All interactions are family-friendly by design
- API keys should be kept secure (never commit to Git)

## Development Notes

### Testing Without Hardware
The application is designed for Raspberry Pi but includes graceful handling:
- `test_components.py` skips hardware tests on non-Pi systems
- Can test API integration separately

### Dependencies
All dependencies are pure Python except:
- `picamera2` - Raspberry Pi specific
- `PyAudio` - Requires system libraries

### Error Handling
- Graceful degradation on component failures
- Conversation continues even if speech not recognized
- Automatic retry on API failures
- Clean shutdown on Ctrl+C

## Future Enhancements

Potential additions:
- [x] ~~Motion-activated triggering~~ (Implemented with OpenCV person detection)
- [x] ~~Local image saving~~ (Implemented with trace files)
- [x] ~~Costume statistics/logging~~ (Implemented with JSON trace logs)
- [ ] Multi-language support
- [ ] Custom sound effects
- [ ] Web interface for monitoring
- [ ] Photo booth mode (print photos)
- [ ] Candy dispenser integration
- [ ] Real-time dashboard for viewing interactions
- [ ] Costume category statistics and analytics

## Credits

- Built with OpenAI's GPT-4o mini and TTS-1
- Uses Google Speech Recognition
- OpenCV for person detection
- Raspberry Pi Foundation for picamera2

## License

Provided as-is for educational and entertainment purposes.

---

**Project Status**: Ready for deployment
**Last Updated**: October 2025
**Target Platform**: Raspberry Pi 5 with Raspberry Pi OS

Happy Halloween! 🎃
