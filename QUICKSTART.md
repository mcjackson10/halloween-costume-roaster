# Quick Start Guide

Get your Halloween Roaster up and running in 5 steps!

## Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS installed
- Camera module connected
- USB microphone connected
- Bluetooth speaker paired

## Installation

### 1. Run Setup Script
```bash
cd /path/to/Halloween
./setup.sh
```

### 2. Configure API Key
```bash
# Copy the example environment file
cp .env.example .env

# Edit the file and add your API key
nano .env
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Test Components
```bash
python3 test_components.py
```

This will verify:
- All packages are installed
- API key is configured
- Camera is working
- Microphone is detected
- Audio output is working
- API connection is successful

### 4. Pair Bluetooth Speaker

If not already paired:
```bash
bluetoothctl
# Then run these commands:
scan on
# Wait for your speaker to appear, then:
pair XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
exit
```

### 5. Run the Program
```bash
python3 halloween_roaster.py
```

## Usage

1. Press **Enter** when a trick-or-treater arrives
2. The camera captures their photo
3. The AI analyzes and roasts their costume
4. If they respond, the conversation continues
5. Repeat for the next person!

## Troubleshooting

### "Camera not detected"
```bash
# Enable camera in raspi-config
sudo raspi-config
# Go to: Interface Options > Camera > Enable
# Reboot
sudo reboot
```

### "Microphone not working"
```bash
# List audio input devices
arecord -l

# Test recording
arecord -d 3 test.wav
aplay test.wav
```

### "No sound from speaker"
```bash
# Check Bluetooth connection
bluetoothctl info

# Set as default output
pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX
```

### "API key error"
```bash
# Verify it's set
echo $OPENAI_API_KEY

# Or check .env file
cat .env
```

## Tips

- Position the camera at chest/face height for best costume recognition
- Place microphone close to where people will stand
- Keep speaker volume moderate (people will be close)
- Test everything before Halloween night!
- Have fun with it!

## Need More Help?

See the full [README.md](README.md) for detailed documentation.

---

Happy Halloween! 🎃
