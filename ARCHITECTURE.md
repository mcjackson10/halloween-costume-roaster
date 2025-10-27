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
                            │                  │
                            │  • Google Drive  │
                            │    API (optional)│
                            └──────────────────┘
                                     ▲
                                     │
                            ┌────────┴─────────┐
                            │  Trace Files     │
                            │  (.jpg + .json)  │
                            │                  │
                            │ Local: traces/   │
                            │ Cloud: G Drive   │
                            └──────────────────┘
```

## Data Flow

```
0. DETECTION PHASE (Auto-Detect Mode)
   ┌─────────────────┐
   │ OpenCV monitors │
   │  camera feed    │
   │  (~2 FPS)       │
   └────────┬────────┘
            │
            ▼
      ┌────────────┐
      │  Person    │
      │ detected?  │
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
      ┌────┴─────┐
      │ --gdrive │
      │  flag?   │
      └────┬─────┘
           │
      Yes──┼──No
           │   │
           │   └──────────────────┐
           ▼                      │
6. GOOGLE DRIVE UPLOAD            │
   ┌─────────────────┐            │
   │ Upload to       │            │
   │ Google Drive    │            │
   │ • Image file    │            │
   │ • JSON file     │            │
   └────────┬────────┘            │
            │                     │
            ▼                     │
   ┌─────────────────┐            │
   │ Upload success? │            │
   └────────┬────────┘            │
            │                     │
       Yes──┼──No                 │
            │   │                 │
            │   └──(keep local)   │
            ▼                     │
   ┌─────────────────┐            │
   │ Delete local    │            │
   │ copies          │            │
   └────────┬────────┘            │
            │                     │
            └─────────────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │ Start cooldown   │
            │ (auto-detect)    │
            │ or wait for      │
            │ Enter (manual)   │
            └──────────────────┘
```

## Class Structure

```
HalloweenRoaster
│
├─── __init__(auto_detect, cooldown, drive_uploader)
│    ├─ Initialize OpenAI client
│    ├─ Initialize camera (Picamera2)
│    ├─ Initialize speech recognition
│    ├─ Initialize audio playback (pygame)
│    ├─ Initialize person detection (OpenCV Haar Cascade)
│    ├─ Set up conversation context
│    ├─ Create traces directory
│    └─ Store Google Drive uploader (if provided)
│
├─── capture_image()
│    ├─ Capture from camera (1920x1080)
│    ├─ Convert to PIL Image
│    └─ Return image + base64
│
├─── detect_person()
│    ├─ Capture frame from camera
│    ├─ Convert to grayscale
│    ├─ Run Haar Cascade detection
│    └─ Return True if person detected
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
│    ├─ Convert text to speech (gTTS)
│    ├─ Save to temp file
│    ├─ Play via pygame
│    └─ Clean up temp file
│
├─── save_trace_files(image, costume, timestamp)
│    ├─ Save JPEG image (85% quality)
│    ├─ Create JSON log with metadata
│    └─ Return file paths
│
├─── upload_to_drive(image_path, json_path)
│    ├─ Upload both files to Google Drive
│    ├─ Delete local copies if successful
│    └─ Keep local copies if upload fails
│
├─── run_interaction()
│    ├─ Capture & analyze costume
│    ├─ Speak initial roast
│    ├─ Handle 3 conversation exchanges
│    ├─ Save trace files
│    └─ Upload to Google Drive (if enabled)
│
├─── run()
│    ├─ Main loop
│    ├─ Auto-detect: Monitor for people continuously
│    └─ Manual: Wait for Enter keypress
│
└─── cleanup()
     ├─ Stop camera
     ├─ Stop person detection
     └─ Quit audio

GoogleDriveUploader (separate class)
│
├─── __init__(credentials_file)
│    ├─ Load service account credentials
│    └─ Build Drive API client
│
├─── find_or_create_folder(folder_name)
│    ├─ Search for existing folder
│    └─ Create if not found
│
├─── upload_file(file_path, folder_id)
│    ├─ Read file content
│    ├─ Upload to Google Drive
│    └─ Return success status
│
└─── upload_files(files, folder_name)
     ├─ Find/create folder
     ├─ Upload each file
     └─ Return success status
```

## State Machine

### Auto-Detect Mode (Default)

```
┌──────────────┐
│  MONITORING  │◀──────────────────────────┐
│  (OpenCV)    │                           │
└──────┬───────┘                           │
       │ ~0.5s intervals                   │
       ▼                                   │
    ┌──────┐                               │
    │Person│                               │
    │ in   │                               │
    │frame?│                               │
    └──┬───┘                               │
       │                                   │
  Yes──┼──No                               │
       │   └───────────────────────────────┘
       ▼
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
└──────┬───────┘                        │
       │                                │
       ▼                                │
    ┌──────┐                            │
    │GDrive│                            │
    │ on?  │                            │
    └──┬───┘                            │
       │                                │
  Yes──┼──No───────────┐                │
       │               │                │
       ▼               │                │
┌──────────────┐       │                │
│  UPLOADING   │       │                │
│ (Google Drive)│      │                │
└──────┬───────┘       │                │
       │               │                │
       └───────────────┘                │
       │                                │
       ▼                                │
┌──────────────┐                        │
│  COOLDOWN    │                        │
│  (60s timer) │                        │
└──────┬───────┘                        │
       │                                │
       └────────────────────────────────┘
  (back to MONITORING)

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
- **Model**: gpt-4o-mini
- **Vision**: Multimodal input (image + text)
- **Max Tokens**: 1024 per response
- **Pricing**: $0.15/M input tokens, $0.60/M output tokens
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
- Person detection check: ~0.5s per check
- Camera capture: ~0.5s
- Image encoding: ~0.2s
- API request (vision): ~2-4s
- API request (text): ~1-2s
- TTS generation: ~1-2s
- Audio playback: ~2-5s (varies by text length)
- Speech recognition: Up to 8s timeout
- Trace file saving: ~0.5-1s
- Google Drive upload: ~2-5s (depends on network)

### Total Interaction Time
- Initial roast: ~5-10s
- Each exchange: ~10-15s
- Full interaction (3 exchanges): ~30-60s
- Trace file generation: ~1s
- Google Drive upload: ~2-5s (if enabled)
- **Total with Google Drive**: ~35-70s

### Resource Usage
- Memory: ~200-400MB (includes OpenCV)
- CPU:
  - Moderate during API calls and audio processing
  - Low during person detection monitoring
- Network:
  - API calls: ~100-500KB per interaction
  - Google Drive upload: ~500KB per interaction (if enabled)
- Storage:
  - Local (no --gdrive): ~500KB per trick-or-treater
  - Cloud (with --gdrive): ~0KB local (files deleted after upload)
  - Temp files: ~1-2MB (audio files, auto-cleaned)

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
- **Trace files contain sensitive data**:
  - Photos of trick-or-treaters
  - Full conversation transcripts
  - Timestamps and costume descriptions
- **Local storage**: Files in `traces/` directory (world-readable by default)
- **Cloud storage**: Files uploaded to Google Drive (encrypted in transit)
- API keys stored in environment variables
- **Google Drive credentials**: Service account JSON file (keep secure!)

### Network Security
- All API calls over HTTPS
- Google Drive API uses OAuth 2.0 service account
- No incoming network connections
- Bluetooth uses standard pairing

### Physical Security
- Camera can capture anyone in range
- **Privacy notice recommended** for visitors
- Microphone can record audio
- Trace files persist (local or cloud)

### Best Practices
- Never commit API keys or credentials to Git
- Set appropriate file permissions on trace files
- Use `.gitignore` to exclude:
  - `.env` files
  - `traces/` directory
  - `gdrive_credentials.json`
- Consider data retention policy for trace files
- Inform visitors about photo capture and storage
- Regularly clean up old trace files (if using local storage)

---

This architecture provides a robust, modular system that's easy to understand, maintain, and extend.
