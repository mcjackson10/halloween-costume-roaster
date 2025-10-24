#!/bin/bash
# Setup script for Halloween Costume Roaster on Raspberry Pi 5

set -e

echo "🎃 Halloween Costume Roaster Setup 🎃"
echo "======================================"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null && ! grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-picamera2 \
    portaudio19-dev \
    python3-pyaudio \
    libcamera-dev \
    libatlas-base-dev \
    ffmpeg \
    pulseaudio \
    pulseaudio-utils \
    alsa-utils

echo ""
echo "Step 3: Installing Python dependencies..."
# Check if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Using virtual environment: $VIRTUAL_ENV"
    pip install -r requirements.txt
else
    echo "Not in a virtual environment. Installing with pip3..."
    echo "Note: You may need to create a virtual environment first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  ./setup.sh"
    pip3 install -r requirements.txt
fi

echo ""
echo "Step 4: Camera configuration..."
if ! grep -q "camera_auto_detect=1" /boot/config.txt 2>/dev/null && ! grep -q "camera_auto_detect=1" /boot/firmware/config.txt 2>/dev/null; then
    echo "Camera may need to be enabled in raspi-config"
    read -p "Would you like to enable the camera now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo raspi-config nonint do_camera 0
    fi
fi

echo ""
echo "Step 5: API Key configuration..."
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your OpenAI API key"
    echo "   Get your key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Press Enter to continue..."
fi

echo ""
echo "Step 6: Testing components..."

echo "  - Testing camera..."
if libcamera-still -o test_setup.jpg --immediate 2>/dev/null; then
    echo "    ✓ Camera working!"
    rm -f test_setup.jpg
else
    echo "    ✗ Camera test failed - check connections and run 'sudo raspi-config'"
fi

echo "  - Testing microphone..."
if arecord -l | grep -q "card"; then
    echo "    ✓ Microphone detected!"
else
    echo "    ✗ No microphone detected - please connect a microphone"
fi

echo "  - Testing audio output..."
if aplay -l | grep -q "card"; then
    echo "    ✓ Audio output detected!"
else
    echo "    ✗ No audio output detected"
fi

echo ""
echo "======================================"
echo "Setup complete! 🎃"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Pair your Bluetooth speaker (use 'bluetoothctl')"
echo "3. Test the system: python3 halloween_roaster.py"
echo ""
echo "For detailed instructions, see README.md"
echo "======================================"
