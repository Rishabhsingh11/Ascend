# tests/get_folder_id.py
"""Get folder ID for Job Recommendations."""

import sys
from pathlib import Path
import time

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.csv_job_exporter import GoogleSheetsExporter

exporter = GoogleSheetsExporter()

# Try to find the folder
query = "name='Job Recommendations' and mimeType='application/vnd.google-apps.folder' and trashed=false"

results = exporter.drive_service.files().list(
    q=query,
    spaces='drive',
    fields='files(id, name, owners)'
).execute()

folders = results.get('files', [])

print("=" * 80)
print("SEARCHING FOR 'JOB RECOMMENDATIONS' FOLDER")
print("=" * 80)
print()

if folders:
    print(f"✅ Found {len(folders)} folder(s):\n")
    for idx, folder in enumerate(folders, 1):
        print(f"{idx}. {folder['name']}")
        print(f"   ID: {folder['id']}")
        owners = folder.get('owners', [])
        if owners:
            print(f"   Owner: {owners[0].get('emailAddress', 'Unknown')}")
        print()
    
    if len(folders) == 1:
        print(f"✅ Use this folder ID in your code:")
        print(f"   {folders[0]['id']}")
else:
    print("❌ No 'Job Recommendations' folder found!")
    print("\nThis means the folder is NOT shared with the service account.")
    print(f"\nPlease share the folder with:")
    print(f"   ascend-job-exporter@ascend-474519.iam.gserviceaccount.com")

print()
print("=" * 80)
