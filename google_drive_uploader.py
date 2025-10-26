#!/usr/bin/env python3
"""
Google Drive Uploader for Halloween Roaster
Handles uploading trace files and images to Google Drive
"""

import os
from typing import Optional
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class GoogleDriveUploader:
    """Handles uploading files to Google Drive using Service Account authentication"""

    # Required Google Drive API scopes
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self, credentials_path: str, folder_name: str = "Halloween-Roaster-Traces"):
        """Initialize Google Drive uploader

        Args:
            credentials_path: Path to service account credentials JSON file
            folder_name: Name of folder in Google Drive to store traces (default: "Halloween-Roaster-Traces")

        Raises:
            ValueError: If credentials file doesn't exist
            Exception: If authentication fails
        """
        if not os.path.exists(credentials_path):
            raise ValueError(f"Credentials file not found: {credentials_path}")

        self.credentials_path = credentials_path
        self.folder_name = folder_name
        self.folder_id = None

        try:
            # Authenticate with service account
            print(f"Authenticating with Google Drive using: {credentials_path}")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=self.SCOPES
            )

            # Build Drive API service
            self.service = build('drive', 'v3', credentials=credentials)

            # Create or find the folder
            self._setup_folder()

            print(f"✓ Google Drive initialized. Folder ID: {self.folder_id}")

        except Exception as e:
            raise Exception(f"Failed to initialize Google Drive: {e}")

    def _setup_folder(self):
        """Create the trace folder if it doesn't exist, or get its ID if it does"""
        try:
            # Search for existing folder
            query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            folders = results.get('files', [])

            if folders:
                # Folder exists, use it
                self.folder_id = folders[0]['id']
                print(f"✓ Found existing folder: {self.folder_name}")
            else:
                # Create new folder
                folder_metadata = {
                    'name': self.folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                self.folder_id = folder['id']
                print(f"✓ Created new folder: {self.folder_name}")

        except HttpError as e:
            raise Exception(f"Failed to setup Google Drive folder: {e}")

    def upload_file(self, file_path: str, custom_name: Optional[str] = None) -> str:
        """Upload a file to Google Drive

        Args:
            file_path: Local path to file to upload
            custom_name: Optional custom name for file in Drive (default: use original filename)

        Returns:
            Google Drive file ID

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Determine filename
            filename = custom_name if custom_name else os.path.basename(file_path)

            # Determine MIME type based on extension
            file_ext = Path(file_path).suffix.lower()
            mime_types = {
                '.json': 'application/json',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.txt': 'text/plain'
            }
            mime_type = mime_types.get(file_ext, 'application/octet-stream')

            # File metadata
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }

            # Upload file
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()

            file_id = file['id']
            print(f"✓ Uploaded: {filename} (ID: {file_id})")

            return file_id

        except HttpError as e:
            raise Exception(f"Failed to upload file {file_path}: {e}")

    def upload_multiple(self, file_paths: list) -> dict:
        """Upload multiple files to Google Drive

        Args:
            file_paths: List of local file paths to upload

        Returns:
            Dictionary mapping local paths to Drive file IDs
            Failed uploads will have None as value
        """
        results = {}

        for file_path in file_paths:
            try:
                file_id = self.upload_file(file_path)
                results[file_path] = file_id
            except Exception as e:
                print(f"✗ Failed to upload {file_path}: {e}")
                results[file_path] = None

        return results

    def get_folder_url(self) -> str:
        """Get the web URL for the Google Drive folder

        Returns:
            URL to view folder in browser
        """
        return f"https://drive.google.com/drive/folders/{self.folder_id}"
