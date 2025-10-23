# Halloween Costume Roaster - Project Summary

## Overview
A complete Raspberry Pi 5 system that uses AI vision and conversation to create an interactive Halloween experience. The system captures photos of trick-or-treaters' costumes, analyzes them using Claude AI, and engages in playful roasting banter through voice interaction.

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
└── PROJECT_SUMMARY.md            # This file
```

## Key Features

### 1. Computer Vision
- Uses Raspberry Pi Camera Module to capture costume photos
- Integrates with Claude 3.5 Sonnet vision capabilities
- Analyzes costumes in real-time

### 2. AI Conversation
- Generates witty, family-friendly roasts
- Maintains conversation context
- Supports up to 3 back-and-forth exchanges per person

### 3. Voice Interaction
- Speech recognition via microphone
- Text-to-speech output via Bluetooth speaker
- Adjustable listening timeouts

### 4. Hardware Integration
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
- **Anthropic API** (Claude 3.5 Sonnet)
- **picamera2** - Camera interface
- **SpeechRecognition** - Voice input
- **gTTS** - Text-to-speech
- **pygame** - Audio playback
- **PIL** - Image processing

### External Services
- Anthropic API for AI vision and conversation
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
   - Add Anthropic API key

4. **Testing**
   ```bash
   python3 test_components.py
   ```

5. **Run**
   ```bash
   python3 halloween_roaster.py
   ```

## Usage Flow

1. System initializes (camera, microphone, speaker)
2. Operator presses Enter when trick-or-treater arrives
3. Camera captures photo
4. AI analyzes costume and generates roast
5. Roast is spoken through speaker
6. System listens for verbal response (8s timeout)
7. If response detected, AI generates comeback
8. Conversation continues (up to 3 exchanges)
9. System resets for next person

## Cost Estimate

### Per Interaction (approximately)
- Image analysis: $0.01-0.03
- Text generation (3 responses): $0.01-0.02
- **Total: ~$0.05-0.10 per trick-or-treater**

### For 100 Trick-or-Treaters
- **Estimated cost: $5-10**

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
- Verify key: `echo $ANTHROPIC_API_KEY`
- Check credits: https://console.anthropic.com/
- Test connection: Run `test_components.py`

## Safety & Privacy

- Images are sent to Anthropic API (encrypted in transit)
- No local image storage by default
- Speech processed by Google API
- Consider posting privacy notice for visitors
- All interactions are family-friendly by design

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
- [ ] Motion-activated triggering (PIR sensor)
- [ ] Local image saving with privacy mode
- [ ] Costume statistics/logging
- [ ] Multi-language support
- [ ] Custom sound effects
- [ ] Web interface for monitoring
- [ ] Photo booth mode (save and print photos)
- [ ] Candy dispenser integration

## Credits

- Built with Claude AI (Anthropic)
- Uses Google Speech Recognition
- gTTS for text-to-speech
- Raspberry Pi Foundation for picamera2

## License

Provided as-is for educational and entertainment purposes.

---

**Project Status**: Ready for deployment
**Last Updated**: October 2025
**Target Platform**: Raspberry Pi 5 with Raspberry Pi OS

Happy Halloween! 🎃
