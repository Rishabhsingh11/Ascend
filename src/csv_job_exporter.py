# src/csv_job_exporter.py
"""CSV exporter for job recommendations with Google Drive upload."""

import csv
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.logger import get_logger
from src.config import get_settings
from src.state import JobPosting

logger = get_logger()


class CSVJobExporter:
    """Export job recommendations to CSV and upload to Google Drive."""
    
    def __init__(self, output_dir: str = "exports"):
        """Initialize CSV exporter with Drive integration."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Google Drive API
        settings = get_settings()
        
        try:
            scopes = ['https://www.googleapis.com/auth/drive']
            
            self.creds = Credentials.from_service_account_file(
                settings.google_credentials_path,
                scopes=scopes
            )
            
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            
            logger.info(f"✅ CSV exporter initialized (output: {self.output_dir})")
            logger.debug(f"   Google Drive integration enabled")
            
        except Exception as e:
            logger.warning(f"Drive integration unavailable: {e}")
            self.drive_service = None
    
    def create_job_recommendations_csv(
        self,
        jobs: List[JobPosting],
        candidate_name: str,
        job_roles: List[str],
        market_readiness: Optional[float] = None,
        upload_to_drive: bool = True,
        drive_folder_id: Optional[str] = None
    ) -> tuple[str, Optional[str]]:
        """
        Create a CSV file with job recommendations.
        
        Args:
            jobs: List of JobPosting objects
            candidate_name: Name of the candidate
            job_roles: List of job roles searched
            market_readiness: Optional market readiness score
            upload_to_drive: Whether to upload to Google Drive
            drive_folder_id: Optional Drive folder ID to upload to
            
        Returns:
            Tuple of (local_csv_path, drive_url)
        """
        try:
            # Create CSV filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Jobs_{candidate_name.replace(' ', '_')}_{timestamp}.csv"
            filepath = self.output_dir / filename
            
            logger.info(f"Creating CSV: {filename}")
            
            # Write CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header information
                #writer.writerow([f'Job Recommendations for {candidate_name}'])
                # writer.writerow([f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}'])
                # writer.writerow([f'Job Roles: {", ".join(job_roles)}'])
                # writer.writerow([f'Total Jobs: {len(jobs)}'])
                
                # if market_readiness is not None:
                #     writer.writerow([f'Market Readiness: {market_readiness:.1f}%'])
                
                # writer.writerow([])  # Empty row
                
                # Column headers
                writer.writerow([
                    '#', 'Job Title', 'Company', 'Location', 
                    'Salary', 'Posted Date', 'Source', 'URL', 'Status'
                ])
                
                # Job data
                for idx, job in enumerate(jobs, 1):
                    writer.writerow([
                        idx,
                        job.title,
                        job.company,
                        job.location,
                        job.salary or 'Not specified',
                        job.posted_date or 'N/A',
                        job.source.title(),
                        job.url,
                        'Not Applied'
                    ])
            
            logger.info(f"✅ CSV created: {filepath}")
            
            # Upload to Drive if requested
            drive_url = None
            if upload_to_drive and self.drive_service:
                try:
                    drive_url = self._upload_to_drive(
                        filepath, 
                        filename, 
                        drive_folder_id
                    )
                except Exception as e:
                    logger.warning(f"Drive upload failed (non-critical): {e}")
            
            return str(filepath), drive_url
            
        except Exception as e:
            logger.error(f"Failed to create CSV: {e}")
            raise
    
    def _upload_to_drive(
        self,
        filepath: Path,
        filename: str,
        folder_id: Optional[str] = None
    ) -> str:
        """Upload CSV file to Google Drive."""
        
        logger.info(f"Uploading to Google Drive...")
        
        # Get or find folder
        if not folder_id:
            folder_id = self._find_folder("Job Recommendations")
        
        # File metadata
        file_metadata = {
            'name': filename,
            'mimeType': 'text/csv'
        }
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Upload file
        media = MediaFileUpload(
            str(filepath),
            mimetype='text/csv',
            resumable=True
        )
        
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()
        
        file_id = file['id']
        
        # Share publicly (anyone with link can view)
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            self.drive_service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            logger.info("✅ File shared publicly")
            
        except Exception as e:
            logger.warning(f"Could not set public sharing: {e}")
        
        # Get shareable link
        drive_url = file.get('webViewLink') or file.get('webContentLink')
        
        logger.info(f"✅ Uploaded to Drive")
        logger.info(f"   URL: {drive_url}")
        
        return drive_url
    
    def _find_folder(self, folder_name: str) -> Optional[str]:
        """Find folder ID by name."""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                logger.debug(f"Found folder '{folder_name}': {folder_id}")
                return folder_id
            else:
                logger.warning(f"Folder '{folder_name}' not found")
                return None
                
        except Exception as e:
            logger.error(f"Error finding folder: {e}")
            return None
    
    def update_job_status(self, csv_path: str, job_row: int, status: str):
        """
        Update job status in CSV file.
        
        Args:
            csv_path: Path to CSV file
            job_row: Row number of the job (1-indexed, first data row = 1)
            status: New status (e.g., "Applied", "Interviewing")
        """
        try:
            # Read all rows
            with open(csv_path, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            
            # Calculate actual row (header is row 0, data starts at row 1)
            actual_row = job_row  # Direct mapping since no header info
            
            if actual_row < len(rows):
                rows[actual_row][8] = status  # Status is column 9 (index 8)
                
                # Write back
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
                
                logger.info(f"Updated job {job_row} status: {status}")
            else:
                logger.error(f"Row {job_row} not found in CSV")
            
        except Exception as e:
            logger.error(f"Failed to update CSV: {e}")
            raise


logger.info("✅ CSVJobExporter module initialized")
