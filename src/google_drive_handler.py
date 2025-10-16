# src/google_drive_handler.py
"""Google Drive integration for resume file handling with Service Account."""

import os
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from typing import Optional, Dict, List

from src.logger import get_logger
from src.config import get_settings

logger = get_logger()


class GoogleDriveHandler:
    """Handle Google Drive operations for resume files using Service Account."""
    
    def __init__(self):
        """Initialize Google Drive API client with service account."""
        settings = get_settings()
        
        # Define required scopes (read/write for Drive and Sheets)
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        
        self.credentials_path = settings.google_credentials_path
        
        # Load service account credentials
        try:
            self.creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            
            # Build Drive service
            self.service = build('drive', 'v3', credentials=self.creds)
            
            logger.info("✅ Google Drive initialized with Service Account")
            logger.debug(f"   Service account: {self.creds.service_account_email}")
            
        except FileNotFoundError:
            logger.error(f"❌ Credentials file not found: {self.credentials_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Drive: {e}")
            raise
    
    def find_folder_by_name(self, folder_name: str) -> Optional[str]:
        """Find a folder ID by folder name.
        
        Args:
            folder_name: Name of the folder to find
            
        Returns:
            Folder ID if found, None otherwise
        """
        try:
            # Query for folders with the specified name
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=10
            ).execute()
            
            folders = results.get('files', [])
            
            if not folders:
                logger.warning(f"Folder '{folder_name}' not found")
                return None
            
            folder_id = folders[0]['id']
            logger.debug(f"Found folder '{folder_name}': {folder_id}")
            
            # Return the first matching folder
            return folder_id
            
        except Exception as e:
            logger.error(f"Error finding folder: {e}")
            return None
    
    def list_resumes(
        self, 
        folder_id: Optional[str] = None,
        folder_name: Optional[str] = None,
        mime_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """List all resume files in Google Drive.
        
        Args:
            folder_id: Optional folder ID to search within
            folder_name: Optional folder name to search within (will find ID automatically)
            mime_types: List of MIME types to filter (default: PDF and DOCX)
            
        Returns:
            List of file metadata dictionaries
        """
        if mime_types is None:
            mime_types = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
        
        # If folder_name provided but no folder_id, find the folder
        if folder_name and not folder_id:
            folder_id = self.find_folder_by_name(folder_name)
            if not folder_id:
                logger.warning(f"Folder '{folder_name}' not found. Searching entire Drive.")
        
        # Build query
        query_parts = [f"mimeType='{mime}'" for mime in mime_types]
        query = "(" + " or ".join(query_parts) + ")"
        
        # Add folder filter if folder_id is provided
        if folder_id:
            query = f"{query} and '{folder_id}' in parents and trashed=false"
        else:
            query += " and trashed=false"
        
        try:
            # Execute query
            results = self.service.files().list(
                q=query,
                spaces='drive',
                pageSize=100,
                fields="files(id, name, mimeType, modifiedTime, size)",
                orderBy='modifiedTime desc'
            ).execute()
            
            files = results.get('files', [])
            
            logger.info(f"Found {len(files)} resume file(s) in '{folder_name or 'Drive'}'")
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing resumes: {e}")
            return []
    
    def download_file(self, file_id: str, file_name: str) -> bytes:
        """Download file content from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            file_name: Name to save the file as locally
            
        Returns:
            File content as bytes
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.debug(f"Download progress: {progress}%")
            
            fh.seek(0)
            content = fh.read()
            
            # Save to disk
            with open(file_name, 'wb') as f:
                f.write(content)
            
            logger.info(f"Downloaded file: {file_name}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def get_file_metadata(self, file_id: str) -> Dict:
        """Get metadata for a specific file.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File metadata dictionary
        """
        try:
            metadata = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime'
            ).execute()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return {}
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """Create a new folder in Google Drive.
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: Optional parent folder ID
            
        Returns:
            Created folder ID or None if failed
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name'
            ).execute()
            
            logger.info(f"Created folder: {folder_name} (ID: {folder['id']})")
            
            return folder['id']
            
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            return None


logger.info("✅ GoogleDriveHandler module initialized")
