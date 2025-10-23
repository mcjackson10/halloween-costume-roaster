# System Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Halloween Roaster System                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐        ┌──────────────────┐
│  Camera Module   │───────▶│  Raspberry Pi 5  │
│   (Pi Camera)    │        │                  │
└──────────────────┘        │  ┌────────────┐  │
                            │  │   Main     │  │
┌──────────────────┐        │  │  Python    │  │
│   Microphone     │───────▶│  │   App      │  │
│   (USB/Built-in) │        │  └────────────┘  │
└──────────────────┘        │         │        │
                            │         │        │
┌──────────────────┐        │         ▼        │
│ Bluetooth Speaker│◀───────│  ┌────────────┐  │
│   (Audio Out)    │        │  │   Audio    │  │
└──────────────────┘        │  │  Output    │  │
                            │  └────────────┘  │
                            └──────────────────┘
                                     │
                                     │ Internet
                                     ▼
                            ┌──────────────────┐
                            │  External APIs   │
                            │                  │
                            │  • Anthropic API │
                            │    (Claude)      │
                            │                  │
                            │  • Google Speech │
                            │    Recognition   │
                            └──────────────────┘
```

## Data Flow

```
1. CAPTURE PHASE
   ┌─────────────┐
   │ Trick-or-   │
   │  treater    │
   │  arrives    │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐      ┌──────────────┐
   │  Camera     │─────▶│ Capture Photo│
   │  Module     │      │  (JPEG)      │
   └─────────────┘      └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ Base64 Encode│
                        │   + Resize   │
                        └──────┬───────┘
                               │
2. ANALYSIS PHASE                │
          ┌────────────────────────┘
          ▼
   ┌─────────────────┐
   │ Send to Claude  │
   │  Vision API     │
   │                 │
   │ Prompt:         │
   │ "Analyze costume│
   │  and roast it!" │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Claude analyzes │
   │ • Identifies    │
   │   costume       │
   │ • Generates     │
   │   witty roast   │
   └────────┬────────┘
            │
3. OUTPUT PHASE         │
          ┌─────────────┘
          ▼
   ┌─────────────────┐
   │  Text-to-Speech │
   │     (gTTS)      │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Play via pygame │
   │   to Bluetooth  │
   │    Speaker      │
   └─────────────────┘
            │
4. INTERACTION PHASE    │
          ┌─────────────┘
          ▼
   ┌─────────────────┐
   │  Listen for     │
   │  Response       │
   │  (8s timeout)   │
   └────────┬────────┘
            │
            ▼
      ┌────┴────┐
      │Response?│
      └────┬────┘
           │
    Yes ───┴─── No
     │              │
     ▼              ▼
┌─────────────┐  ┌──────────┐
│  Google     │  │  End     │
│  Speech API │  │  Session │
│  converts   │  └──────────┘
│  to text    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Send to Claude  │
│ with context    │
│                 │
│ Prompt:         │
│ "Respond to     │
│  their comeback"│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate witty  │
│   comeback      │
└────────┬────────┘
         │
         └─────┐
               │
         (Repeat OUTPUT PHASE)
         (Up to 3 exchanges)
```

## Class Structure

```
HalloweenRoaster
│
├─── __init__()
│    ├─ Initialize Anthropic client
│    ├─ Initialize camera (Picamera2)
│    ├─ Initialize speech recognition
│    ├─ Initialize audio playback (pygame)
│    └─ Set up conversation context
│
├─── capture_image()
│    ├─ Capture from camera
│    ├─ Convert to PIL Image
│    └─ Return image + base64
│
├─── analyze_costume(image_base64)
│    ├─ Send image to Claude API
│    ├─ Get costume analysis + roast
│    └─ Update conversation history
│
├─── listen_for_speech(timeout)
│    ├─ Listen via microphone
│    ├─ Process with Google Speech API
│    └─ Return transcribed text
│
├─── generate_response(user_input)
│    ├─ Add to conversation history
│    ├─ Send to Claude API
│    └─ Get witty comeback
│
├─── speak(text)
│    ├─ Convert text to speech (gTTS)
│    ├─ Save to temp file
│    ├─ Play via pygame
│    └─ Clean up temp file
│
├─── run_interaction()
│    ├─ Capture & analyze costume
│    ├─ Speak initial roast
│    └─ Handle 3 conversation exchanges
│
├─── run()
│    ├─ Main loop
│    └─ Wait for Enter keypress
│
└─── cleanup()
     ├─ Stop camera
     └─ Quit audio
```

## State Machine

```
┌─────────────┐
│   IDLE      │◀──────────────────┐
│  (Waiting)  │                   │
└──────┬──────┘                   │
       │ Press Enter              │
       ▼                          │
┌─────────────┐                   │
│  CAPTURING  │                   │
│   (Photo)   │                   │
└──────┬──────┘                   │
       │                          │
       ▼                          │
┌─────────────┐                   │
│  ANALYZING  │                   │
│  (Claude)   │                   │
└──────┬──────┘                   │
       │                          │
       ▼                          │
┌─────────────┐                   │
│  SPEAKING   │                   │
│  (Roast)    │                   │
└──────┬──────┘                   │
       │                          │
       ▼                          │
┌─────────────┐                   │
│  LISTENING  │                   │
│  (8s max)   │                   │
└──────┬──────┘                   │
       │                          │
    ┌──┴───┐                      │
    │Heard?│                      │
    └──┬───┘                      │
       │                          │
  Yes──┼──No                      │
       │   │                      │
       │   └──────────────────────┘
       ▼
┌─────────────┐
│ RESPONDING  │
│  (Claude)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  SPEAKING   │
│ (Comeback)  │
└──────┬──────┘
       │
       ▼
    ┌──────┐
    │More? │
    └──┬───┘
       │
  Yes──┼──No
       │   │
       │   └───────────────────────┐
       │                           │
       └──(back to LISTENING)      │
                                   │
                                   ▼
                              ┌─────────┐
                              │  IDLE   │
                              │(Waiting)│
                              └─────────┘
```

## API Integration

### Anthropic API
- **Model**: claude-3-5-sonnet-20241022
- **Vision**: Multimodal input (image + text)
- **Max Tokens**: 1024 per response
- **Usage**:
  - Initial costume analysis (1 call per person)
  - Conversation responses (1 call per exchange)

### Google Speech Recognition API
- **Service**: Google Speech Recognition
- **Input**: Audio from microphone
- **Output**: Transcribed text
- **Timeout**: Configurable (default 8s)

## Performance Characteristics

### Timing
- Camera capture: ~0.5s
- Image encoding: ~0.2s
- API request (vision): ~2-4s
- API request (text): ~1-2s
- TTS generation: ~1-2s
- Audio playback: ~2-5s (varies by text length)
- Speech recognition: Up to 8s timeout

### Total Interaction Time
- Initial roast: ~5-10s
- Each exchange: ~10-15s
- Full interaction (3 exchanges): ~30-60s

### Resource Usage
- Memory: ~200-300MB
- CPU: Moderate during API calls and audio processing
- Network: ~100-500KB per interaction
- Storage: Minimal (temp audio files only)

## Error Handling

```
┌──────────────────┐
│  Component Error │
└────────┬─────────┘
         │
    ┌────┴─────┐
    │  Which?  │
    └────┬─────┘
         │
    ┌────┼────────────┐
    │    │            │
    ▼    ▼            ▼
┌────────────┐  ┌──────────┐  ┌─────────┐
│   Camera   │  │   API    │  │  Audio  │
└─────┬──────┘  └─────┬────┘  └────┬────┘
      │               │             │
      ▼               ▼             ▼
  ┌────────┐      ┌────────┐   ┌────────┐
  │ Fatal  │      │ Retry  │   │Warning │
  │ Exit   │      │ 1x     │   │Continue│
  └────────┘      └────┬───┘   └────────┘
                       │
                   ┌───┴────┐
                   │Success?│
                   └───┬────┘
                       │
                  Yes──┼──No
                       │   │
                       │   ▼
                       │ ┌──────┐
                       │ │ Warn │
                       │ │ User │
                       │ └──────┘
                       ▼
                  ┌─────────┐
                  │Continue │
                  └─────────┘
```

## Security Considerations

### Data Privacy
- Images sent to Anthropic API (encrypted HTTPS)
- Audio sent to Google API (encrypted HTTPS)
- No local data persistence by default
- API keys stored in environment variables

### Network Security
- All API calls over HTTPS
- No incoming network connections
- Bluetooth uses standard pairing

### Physical Security
- Camera can capture anyone in range
- Consider privacy notice for visitors
- Microphone can record audio

---

This architecture provides a robust, modular system that's easy to understand, maintain, and extend.
