#!/usr/bin/env python3
"""
Component Testing Script for Halloween Roaster
Tests each component individually to help with troubleshooting
"""

import sys
import os

def test_imports():
    """Test if all required packages are installed"""
    print("Testing package imports...")
    packages = {
        'openai': 'openai',
        'PIL': 'pillow',
        'speech_recognition': 'SpeechRecognition',
        'pygame': 'pygame',
        'gtts': 'gTTS',
    }

    # Only test picamera2 on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry Pi' in f.read() or 'BCM' in f.read():
                packages['picamera2'] = 'picamera2'
    except:
        pass

    failed = []
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError as e:
            print(f"  ✗ {package} - {e}")
            failed.append(package)

    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Run: pip3 install -r requirements.txt")
        return False
    else:
        print("✓ All packages installed!\n")
        return True

def test_api_key():
    """Test if API key is configured"""
    print("Testing API key configuration...")
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("  ✗ OPENAI_API_KEY not found")
        print("  Set it with: export OPENAI_API_KEY='your-key-here'")
        print("  Or create a .env file")
        return False
    elif api_key == "your-api-key-here":
        print("  ✗ API key is still placeholder value")
        return False
    else:
        print(f"  ✓ API key configured (length: {len(api_key)})\n")
        return True

def test_camera():
    """Test camera functionality"""
    print("Testing camera...")
    try:
        from picamera2 import Picamera2
        camera = Picamera2()
        camera.start()
        import time
        time.sleep(1)
        camera.stop()
        print("  ✓ Camera working!\n")
        return True
    except Exception as e:
        print(f"  ✗ Camera error: {e}")
        print("  Check camera connection and enable it in raspi-config\n")
        return False

def test_microphone():
    """Test microphone functionality"""
    print("Testing microphone...")
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        m = sr.Microphone()

        # List available microphones
        mic_list = sr.Microphone.list_microphone_names()
        print(f"  Available microphones: {len(mic_list)}")
        for i, name in enumerate(mic_list[:3]):  # Show first 3
            print(f"    {i}: {name}")

        print("  ✓ Microphone initialized!\n")
        return True
    except Exception as e:
        print(f"  ✗ Microphone error: {e}")
        print("  Check microphone connection\n")
        return False

def test_audio_output():
    """Test audio output"""
    print("Testing audio output...")
    try:
        import pygame
        pygame.mixer.init()
        print("  ✓ Audio output initialized!")

        # Check if we can create a test sound
        from gtts import gTTS
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_file = fp.name

        try:
            tts = gTTS(text="Testing audio", lang='en')
            tts.save(temp_file)
            print("  ✓ Text-to-speech working!")

            # Try to play (might fail if no audio device)
            try:
                pygame.mixer.music.load(temp_file)
                print("  ✓ Can load audio files!")
            except:
                print("  ⚠️  Can't play audio - check speaker connection")
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

        pygame.mixer.quit()
        print()
        return True
    except Exception as e:
        print(f"  ✗ Audio error: {e}\n")
        return False

def test_api_connection():
    """Test API connection with a simple request"""
    print("Testing OpenAI API connection...")
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your-api-key-here":
            print("  ✗ API key not configured properly")
            return False

        client = OpenAI(api_key=api_key)

        # Simple test request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'API working' if you can read this."
                }
            ]
        )

        response_text = response.choices[0].message.content
        print(f"  ✓ API connection successful!")
        print(f"  Response: {response_text}\n")
        return True
    except Exception as e:
        print(f"  ✗ API error: {e}")
        print("  Check your API key and internet connection\n")
        return False

def main():
    """Run all tests"""
    print("🎃 Halloween Roaster Component Tests 🎃")
    print("=" * 50)
    print()

    results = {}

    # Run tests
    results['imports'] = test_imports()
    results['api_key'] = test_api_key()

    # Only test hardware components on Raspberry Pi
    is_pi = False
    try:
        with open('/proc/cpuinfo', 'r') as f:
            content = f.read()
            is_pi = 'Raspberry Pi' in content or 'BCM' in content
    except:
        pass

    if is_pi:
        results['camera'] = test_camera()
    else:
        print("⚠️  Not on Raspberry Pi - skipping camera test\n")
        results['camera'] = None

    results['microphone'] = test_microphone()
    results['audio'] = test_audio_output()

    if results['api_key'] and results['imports']:
        results['api'] = test_api_connection()
    else:
        print("⚠️  Skipping API test (prerequisites not met)\n")
        results['api'] = None

    # Summary
    print("=" * 50)
    print("Test Summary:")
    print("=" * 50)

    for test, result in results.items():
        if result is True:
            print(f"  ✓ {test.capitalize()}")
        elif result is False:
            print(f"  ✗ {test.capitalize()}")
        else:
            print(f"  ⚠️  {test.capitalize()} (skipped)")

    print()

    # Overall status
    failed = [k for k, v in results.items() if v is False]
    if failed:
        print(f"❌ Some tests failed: {', '.join(failed)}")
        print("Check the error messages above for troubleshooting.")
        sys.exit(1)
    else:
        passed = [k for k, v in results.items() if v is True]
        if passed:
            print("✓ All tests passed! System ready to run.")
            sys.exit(0)
        else:
            print("⚠️  Tests skipped - run on Raspberry Pi for full testing")
            sys.exit(0)

if __name__ == "__main__":
    main()
