# tests/cleanup_service_account_drive.py
"""Clean up files created by service account."""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    'credentials/credentials.json',
    scopes=['https://www.googleapis.com/auth/drive']
)

service = build('drive', 'v3', credentials=creds)

print("=" * 80)
print("CLEANING UP SERVICE ACCOUNT DRIVE")
print("=" * 80)
print()

try:
    # Get all files owned by service account
    print("🔍 Finding files owned by service account...")
    
    results = service.files().list(
        q="'me' in owners",
        pageSize=100,
        fields="files(id, name, mimeType, size, createdTime)"
    ).execute()
    
    files = results.get('files', [])
    
    print(f"✅ Found {len(files)} files\n")
    
    if not files:
        print("✅ Service account Drive is already clean!")
        exit(0)
    
    # Calculate total size
    total_size = sum(int(f.get('size', 0)) for f in files if f.get('size'))
    total_size_mb = total_size / (1024 * 1024)
    
    print(f"📊 Total size: {total_size_mb:.2f} MB\n")
    print("Files to delete:")
    print("-" * 80)
    
    for idx, file in enumerate(files, 1):
        size = int(file.get('size', 0)) if file.get('size') else 0
        size_kb = size / 1024
        print(f"{idx}. {file['name']}")
        print(f"   Type: {file['mimeType']}")
        print(f"   Size: {size_kb:.1f} KB")
        print(f"   Created: {file['createdTime']}")
        print(f"   ID: {file['id']}")
        print()
    
    # Ask for confirmation
    print("=" * 80)
    response = input(f"\n⚠️  Delete ALL {len(files)} files? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Cancelled")
        exit(0)
    
    # Delete files
    print("\n🗑️  Deleting files...")
    
    deleted = 0
    failed = 0
    
    for file in files:
        try:
            service.files().delete(fileId=file['id']).execute()
            print(f"✅ Deleted: {file['name']}")
            deleted += 1
        except Exception as e:
            print(f"❌ Failed to delete {file['name']}: {e}")
            failed += 1
    
    print()
    print("=" * 80)
    print(f"✅ Deleted: {deleted} files")
    if failed:
        print(f"❌ Failed: {failed} files")
    print(f"💾 Freed up: ~{total_size_mb:.2f} MB")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
