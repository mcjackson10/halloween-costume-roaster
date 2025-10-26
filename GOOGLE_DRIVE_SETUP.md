# Google Drive Setup Guide

This guide explains how to set up Google Drive integration for the Halloween Roaster to automatically upload trace files (images + conversation logs) after each interaction.

## Why Google Drive?

- **Memory preservation**: Automatically deletes local files after successful upload
- **Offline analysis**: Access all interaction data from anywhere
- **Backup**: Prevents data loss if Raspberry Pi crashes
- **Storage**: ~500 KB per trick-or-treater uploaded to cloud

## Setup Steps

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
   - Click "Select a Project" → "New Project"
   - Name: "Halloween Roaster" (or any name you prefer)
   - Click "Create"

### 2. Enable Google Drive API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

### 3. Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in details:
   - **Service account name**: `halloween-roaster`
   - **Service account ID**: (auto-generated)
   - **Description**: "Service account for Halloween Roaster trace uploads"
4. Click "Create and Continue"
5. Skip optional steps (no roles needed for personal Drive)
6. Click "Done"

### 4. Create Service Account Key

1. In "Credentials" page, find your service account in the list
2. Click on the service account email
3. Go to "Keys" tab
4. Click "Add Key" → "Create new key"
5. Choose "JSON" format
6. Click "Create"
7. A JSON file will download automatically - **keep this safe!**

### 5. Transfer Credentials to Raspberry Pi

Copy the downloaded JSON file to your Raspberry Pi:

```bash
# From your computer (replace paths accordingly)
scp ~/Downloads/halloween-roaster-*.json pi@raspberrypi.local:~/halloween-costume-roaster/

# Or use any file transfer method you prefer
```

Recommended location on Pi:
```bash
mv halloween-roaster-*.json ~/halloween-costume-roaster/gdrive_credentials.json
```

### 6. Share Google Drive Folder (Important!)

The service account has its own Google Drive, separate from yours. To access uploaded files:

**Option A: Share with yourself (Recommended)**

1. Run the Halloween Roaster once with Google Drive enabled:
   ```bash
   python3 halloween_roaster.py --gdrive gdrive_credentials.json --manual
   ```

2. Look for output like:
   ```
   ✓ Google Drive folder: https://drive.google.com/drive/folders/XXXXXXXXXXXXX
   ```

3. Open that URL in a browser (you'll see "Access Denied")

4. Share the folder with yourself:
   - From terminal on your Pi:
   ```bash
   python3 << EOF
   from google_drive_uploader import GoogleDriveUploader
   uploader = GoogleDriveUploader('gdrive_credentials.json')

   # Replace with your personal Gmail address
   your_email = 'your.email@gmail.com'

   uploader.service.permissions().create(
       fileId=uploader.folder_id,
       body={'type': 'user', 'role': 'writer', 'emailAddress': your_email}
   ).execute()
   print(f"✓ Shared with {your_email}")
   EOF
   ```

5. Check your Gmail - you should receive a sharing notification
6. Now you can access the folder from your personal Google Drive!

**Option B: Use service account's Drive directly**

Access files by using the service account's credentials to authenticate. Not recommended for casual browsing.

### 7. Install Dependencies

```bash
# In your virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

### 8. Test the Setup

Run a manual test:

```bash
python3 halloween_roaster.py --manual --gdrive gdrive_credentials.json
```

Press Enter to trigger an interaction, and verify:
1. Local files are created in `traces/` directory
2. Files are uploaded to Google Drive
3. Local files are deleted after successful upload
4. You can see the files in your shared Google Drive folder

## Usage

### Enable Google Drive Upload

Add `--gdrive` flag with path to credentials:

```bash
# Auto-detect mode with Google Drive
python3 halloween_roaster.py --gdrive gdrive_credentials.json

# Manual mode with Google Drive
python3 halloween_roaster.py --manual --gdrive gdrive_credentials.json

# With custom cooldown
python3 halloween_roaster.py --cooldown 90 --gdrive gdrive_credentials.json
```

### Without Google Drive

Simply omit the `--gdrive` flag:

```bash
# Files will be saved locally in traces/ directory only
python3 halloween_roaster.py
```

## What Gets Uploaded

For each interaction, two files are uploaded:

### 1. Image File (`roast_YYYYMMDD_HHMMSS.jpg`)
- 1920x1080 JPEG image of the trick-or-treater
- ~200-500 KB per image
- Quality: 85% (good balance of size/quality)

### 2. JSON Trace File (`roast_YYYYMMDD_HHMMSS.json`)

Contains:
```json
{
  "timestamp": "2025-10-31T18:23:45.123456",
  "costume_description": "Oh look, a ghost! How original...",
  "conversation_history": [
    {"role": "assistant", "content": "Oh look, a ghost! ..."},
    {"role": "user", "content": "At least I tried!"},
    {"role": "assistant", "content": "Tried? More like..."}
  ],
  "exchanges_count": 2,
  "mode": "auto"
}
```

## Troubleshooting

### "Credentials file not found"
- Check the path to your JSON file
- Use absolute path if relative path doesn't work:
  ```bash
  python3 halloween_roaster.py --gdrive /home/pi/halloween-costume-roaster/gdrive_credentials.json
  ```

### "Failed to initialize Google Drive"
- Ensure Google Drive API is enabled in your project
- Check that JSON credentials file is valid
- Verify internet connection

### "Some uploads failed, keeping local files"
- Check internet connection
- Verify API quotas not exceeded (very unlikely with normal use)
- Check `traces/` directory - files will be kept as backup

### Can't see uploaded files in Google Drive
- Make sure you shared the folder with your personal Gmail (see Step 6)
- Check the folder URL printed during initialization
- Files are in service account's Drive, not yours by default

### Files filling up Raspberry Pi storage
- Google Drive upload is probably failing (check errors)
- Manually delete `traces/` directory contents:
  ```bash
  rm -rf traces/*
  ```

## Security Notes

- **Never commit credentials to Git**: The `gdrive_credentials.json` should be in `.gitignore`
- **Protect the JSON file**: Anyone with this file can upload to your Drive
- **Service account limitations**: Can't access your existing Drive files, only its own folder
- **Quota**: Google Drive API has generous free quota (sufficient for Halloween use)

## Storage Estimates

Assuming 100 trick-or-treaters on Halloween night:
- Images: 100 × 400 KB = ~40 MB
- JSON logs: 100 × 3 KB = ~300 KB
- **Total: ~40 MB per Halloween**

Google Drive free tier: 15 GB (enough for ~375 Halloweens!)

## Alternative: Manual Upload

If you prefer not to use Google Drive:

1. Files saved to `traces/` directory
2. After Halloween, manually copy to your computer:
   ```bash
   # From your computer
   scp -r pi@raspberrypi.local:~/halloween-costume-roaster/traces ./halloween-2025-traces
   ```

3. Delete from Pi:
   ```bash
   rm -rf traces/*
   ```
