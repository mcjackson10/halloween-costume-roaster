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
                            │  • OpenAI API    │
                            │    (GPT-4o mini) │
                            │                  │
                            │  • Google Speech │
                            │    Recognition   │
                            └──────────────────┘
                                     ▲
                                     │
                            ┌────────┴─────────┐
                            │  Trace Files     │
                            │  (.jpg + .json)  │
                            │                  │
                            │ Local: traces/   │
                            └──────────────────┘
```

## Data Flow

```
0. DETECTION PHASE (Auto-Detect Mode)
   ┌─────────────────┐
   │ Two-stage       │
   │ detection       │
   │ monitors feed   │
   │  (~2 FPS)       │
   └────────┬────────┘
            │
            ▼
      ┌────────────┐
      │  Stage 1:  │
      │  Motion    │
      │ detected?  │
      └─────┬──────┘
            │
       Yes──┴──No (continue monitoring)
            │
            ▼
      ┌────────────┐
      │  Stage 2:  │
      │  YOLO11n   │
      │  confirms  │
      │  person?   │
      └─────┬──────┘
            │
       Yes──┴──No (continue monitoring)
            │
            ▼
      ┌────────────┐
      │ Cooldown   │
      │ expired?   │
      └─────┬──────┘
            │
       Yes──┴──No (continue monitoring)
            │
            ▼
   (Trigger interaction)

1. CAPTURE PHASE
   ┌─────────────┐
   │ Trick-or-   │
   │  treater    │
   │  in frame   │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐      ┌──────────────┐
   │  Camera     │─────▶│ Capture Photo│
   │  Module     │      │ (1920x1080)  │
   └─────────────┘      └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ Base64 Encode│
                        │ for API      │
                        └──────┬───────┘
                               │
2. ANALYSIS PHASE                │
          ┌────────────────────────┘
          ▼
   ┌─────────────────┐
   │ Send to GPT-4o  │
   │  mini Vision API│
   │                 │
   │ Prompt:         │
   │ "Analyze costume│
   │  and roast it!" │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ GPT-4o analyzes │
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
   │  (OpenAI TTS-1) │
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
│ Send to GPT-4o  │
│ mini with       │
│ context         │
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
               │
5. TRACE FILE GENERATION
         ┌─────┘
         ▼
   ┌─────────────────┐
   │ Save image      │
   │ (.jpg, 85%      │
   │  quality)       │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Create JSON log │
   │ • Timestamp     │
   │ • Costume desc  │
   │ • Conversation  │
   │ • Mode          │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Save to local   │
   │ traces/ folder  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Start cooldown  │
   │ (auto-detect)   │
   │ or wait for     │
   │ Enter (manual)  │
   └─────────────────┘
```

## Class Structure

```
HalloweenRoaster
│
├─── __init__(auto_detect, cooldown)
│    ├─ Initialize OpenAI client
│    ├─ Initialize camera (Picamera2)
│    ├─ Initialize two-stage person detection:
│    │  ├─ Stage 1: Motion detector (OpenCV MOG2)
│    │  └─ Stage 2: YOLO11n person detector (Ultralytics)
│    ├─ Initialize speech recognition
│    ├─ Initialize audio playback (pygame)
│    ├─ Set up conversation context
│    └─ Create traces directory
│
├─── capture_image()
│    ├─ Capture from camera (1920x1080)
│    ├─ Convert to PIL Image
│    └─ Return image + base64
│
├─── detect_motion()
│    ├─ Capture frame from camera
│    ├─ Apply background subtraction (MOG2)
│    ├─ Find contours in foreground mask
│    └─ Return True if significant motion detected
│
├─── detect_person()
│    ├─ Stage 1: Check for motion (fast pre-filter)
│    ├─ If motion: Stage 2: Run YOLO11n detection
│    ├─ Filter for 'person' class only (COCO class 0)
│    └─ Return True if person detected with confidence > 0.4
│
├─── is_cooldown_active()
│    ├─ Check time since last interaction
│    └─ Return True if within cooldown period
│
├─── analyze_costume(image_base64)
│    ├─ Send image to GPT-4o mini API
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
│    ├─ Send to GPT-4o mini API
│    └─ Get witty comeback
│
├─── speak(text)
│    ├─ Convert text to speech (OpenAI TTS-1)
│    ├─ Save to temp file
│    ├─ Play via pygame
│    └─ Clean up temp file
│
├─── save_trace_files(image, costume, timestamp)
│    ├─ Save JPEG image (85% quality) to traces/
│    ├─ Create JSON log with metadata
│    └─ Return file paths
│
├─── run_interaction()
│    ├─ Capture & analyze costume
│    ├─ Speak initial roast
│    ├─ Handle 3 conversation exchanges
│    └─ Save trace files locally
│
├─── run()
│    ├─ Main loop
│    ├─ Auto-detect: Monitor for people continuously
│    └─ Manual: Wait for Enter keypress
│
└─── cleanup()
     ├─ Stop camera
     └─ Quit audio
```

## State Machine

### Auto-Detect Mode (Default)

```
┌──────────────┐
│  MONITORING  │◀──────────────────────────┐
│  (Two-stage) │                           │
└──────┬───────┘                           │
       │ ~0.5s intervals                   │
       ▼                                   │
    ┌──────┐                               │
    │Stage1│                               │
    │Motion│                               │
    │ in   │                               │
    │frame?│                               │
    └──┬───┘                               │
       │                                   │
  Yes──┼──No                               │
       │   └───────────────────────────────┘
       ▼
    ┌──────┐
    │Stage2│
    │YOLO  │
    │person│
    │conf? │
    └──┬───┘
       │
  Yes──┼──No
       │   └───────────────────────────────┐
       ▼                                   │
    ┌────────┐
    │Cooldown│
    │expired?│
    └──┬─────┘
       │
  Yes──┼──No────────────────────────────┐
       │                                │
       ▼                                │
┌─────────────┐                         │
│  CAPTURING  │                         │
│   (Photo)   │                         │
└──────┬──────┘                         │
       │                                │
       ▼                                │
┌─────────────┐                         │
│  ANALYZING  │                         │
│ (GPT-4o mini)│                         │
└──────┬──────┘                         │
       │                                │
       ▼                                │
┌─────────────┐                         │
│  SPEAKING   │                         │
│  (Roast)    │                         │
└──────┬──────┘                         │
       │                                │
       ▼                                │
┌─────────────┐                         │
│  LISTENING  │                         │
│  (8s max)   │                         │
└──────┬──────┘                         │
       │                                │
    ┌──┴───┐                            │
    │Heard?│                            │
    └──┬───┘                            │
       │                                │
  Yes──┼──No─────────┐                  │
       │             │                  │
       ▼             │                  │
┌─────────────┐      │                  │
│ RESPONDING  │      │                  │
│ (GPT-4o mini)│      │                  │
└──────┬──────┘      │                  │
       │             │                  │
       ▼             │                  │
┌─────────────┐      │                  │
│  SPEAKING   │      │                  │
│ (Comeback)  │      │                  │
└──────┬──────┘      │                  │
       │             │                  │
       ▼             │                  │
    ┌──────┐         │                  │
    │More? │         │                  │
    └──┬───┘         │                  │
       │             │                  │
  Yes──┼──No         │                  │
       │   │         │                  │
       │   └─────────┘                  │
       │   (back to LISTENING)          │
       │                                │
       ▼                                │
┌──────────────┐                        │
│ SAVING TRACE │                        │
│    FILES     │                        │
│   (locally)  │                        │
└──────┬───────┘                        │
       │                                │
       ▼                                │
┌──────────────┐                        │
│  COOLDOWN    │                        │
│  (60s timer) │                        │
└──────┬───────┘                        │
       │                                │
       └────────────────────────────────┘
  (back to MONITORING)

```

### Manual Mode

```
┌─────────────┐
│   IDLE      │◀──────────────────────────┐
│  (Waiting)  │                           │
└──────┬──────┘                           │
       │ Press Enter                      │
       ▼                                  │
   (Same flow as Auto-Detect              │
    from CAPTURING onwards,               │
    but skip COOLDOWN phase)              │
       │                                  │
       └──────────────────────────────────┘
```

## API Integration

### OpenAI API
**GPT-4o mini (Vision & Text)**
- **Model**: gpt-4o-mini
- **Vision**: Multimodal input (image + text)
- **Max Tokens**: 1024 per response
- **Pricing**: $0.15/M input tokens, $0.60/M output tokens
- **Usage**:
  - Initial costume analysis (1 call per person)
  - Conversation responses (1 call per exchange)

**TTS-1 (Text-to-Speech)**
- **Model**: tts-1
- **Voice**: onyx (deep, spooky voice)
- **Pricing**: $15/M characters (~$0.00006 per typical response)
- **Usage**:
  - Initial roast
  - Conversation responses
  - Farewell message

### Google Speech Recognition API
- **Service**: Google Speech Recognition
- **Input**: Audio from microphone
- **Output**: Transcribed text
- **Timeout**: Configurable (default 8s)

## Performance Characteristics

### Timing
- Motion detection (Stage 1): ~0.1-0.2s per check
- YOLO11n detection (Stage 2): ~0.3-0.5s per check (when motion detected)
- Camera capture (high-res): ~0.5s
- Image encoding: ~0.2s
- API request (vision): ~2-4s
- API request (text): ~1-2s
- TTS generation (OpenAI): ~0.5-1.5s
- Audio playback: ~2-5s (varies by text length)
- Speech recognition: Up to 8s timeout
- Trace file saving: ~0.5-1s

### Total Interaction Time
- Initial roast: ~5-10s
- Each exchange: ~10-15s
- Full interaction (3 exchanges): ~30-60s
- Trace file generation: ~1s
- **Total**: ~30-65s

### Resource Usage
- Memory: ~300-500MB (includes OpenCV + YOLO11n model)
- CPU:
  - Moderate during YOLO detection (~30-50% on Pi 5)
  - Moderate during API calls and audio processing
  - Low during motion detection monitoring
- Disk:
  - YOLO11n model: ~6MB (one-time download)
  - NCNN optimized model: ~12MB (auto-generated on first run)
- Network:
  - Model download: ~6MB (first run only)
  - API calls: ~100-500KB per interaction (includes TTS audio download)
- Storage:
  - Local: ~500KB per trick-or-treater
  - Temp files: ~500KB-1MB (audio files, auto-cleaned)

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
- Images sent to OpenAI API (encrypted HTTPS)
- Audio sent to Google Speech API (encrypted HTTPS)
- TTS audio generated via OpenAI API (encrypted HTTPS)
- **Trace files contain sensitive data**:
  - Photos of trick-or-treaters
  - Full conversation transcripts
  - Timestamps and costume descriptions
- **Local storage**: Files in `traces/` directory (world-readable by default)
- API keys stored in environment variables (.env file)

### Network Security
- All API calls over HTTPS
- No incoming network connections
- Bluetooth uses standard pairing

### Physical Security
- Camera can capture anyone in range
- **Privacy notice recommended** for visitors
- Microphone can record audio
- Trace files persist (local or cloud)

### Best Practices
- Never commit API keys to Git
- Set appropriate file permissions on trace files
- Use `.gitignore` to exclude:
  - `.env` files
  - `traces/` directory
- Consider data retention policy for trace files
- Inform visitors about photo capture and storage
- Regularly clean up old trace files to manage storage

---

This architecture provides a robust, modular system that's easy to understand, maintain, and extend.
