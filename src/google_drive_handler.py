"""Google Drive integration for resume file handling."""

import os
import io
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from typing import Optional, Dict, List


class GoogleDriveHandler:
    """Handle Google Drive operations for resume files."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, credentials_path: str = 'credentials/credentials.json'):
        """Initialize Google Drive API connection.
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file
        """
        self.credentials_path = credentials_path
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API."""
        # Check if token.pickle exists for stored credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        # If credentials are invalid or don't exist, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('drive', 'v3', credentials=self.creds)
    
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
                return None
            
            # Return the first matching folder
            return folders[0]['id']
            
        except Exception as e:
            print(f"Error finding folder: {str(e)}")
            return None
    
    def list_resumes(
        self, 
        folder_id: Optional[str] = None,
        folder_name: Optional[str] = None,
        mime_types: List[str] = None
    ) -> List[Dict]:
        """List all resume files in Google Drive.
        
        Args:
            folder_id: Optional folder ID to search within
            folder_name: Optional folder name to search within (will find ID automatically)
            mime_types: List of MIME types to filter
            
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
                print(f"Warning: Folder '{folder_name}' not found. Searching entire Drive.")
        
        # Build query
        query = f"mimeType='{mime_types[0]}'"
        if len(mime_types) > 1:
            for mime in mime_types[1:]:
                query += f" or mimeType='{mime}'"
        
        # Add folder filter if folder_id is provided
        if folder_id:
            query = f"({query}) and '{folder_id}' in parents and trashed=false"
        else:
            query += " and trashed=false"
        
        # Execute query
        results = self.service.files().list(
            q=query,
            spaces='drive',
            pageSize=100,
            fields="files(id, name, mimeType, modifiedTime, size)"
        ).execute()
        
        return results.get('files', [])
    
    def download_file(self, file_id: str, file_name: str) -> bytes:
        """Download file content from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            file_name: Name to save the file as locally
            
        Returns:
            File content as bytes
        """
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")
        
        fh.seek(0)
        content = fh.read()
        
        # Save to disk
        with open(file_name, 'wb') as f:
            f.write(content)
        
        return content
    
    def get_file_metadata(self, file_id: str) -> Dict:
        """Get metadata for a specific file.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File metadata dictionary
        """
        return self.service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, size, createdTime, modifiedTime'
        ).execute()
