# tests/check_credentials.py
"""Check credential type and format."""

import json
from pathlib import Path

def check_credentials():
    """Check what type of credentials we have."""
    
    creds_path = Path("credentials/credentials.json")
    
    if not creds_path.exists():
        print("❌ credentials.json not found")
        return
    
    print("=" * 80)
    print("CHECKING CREDENTIALS FORMAT")
    print("=" * 80)
    print()
    
    with open(creds_path, 'r') as f:
        creds = json.load(f)
    
    print("📋 Fields found in credentials.json:")
    for key in creds.keys():
        print(f"   • {key}")
    print()
    
    # Check credential type
    if "type" in creds:
        print(f"🔑 Credential Type: {creds['type']}")
        print()
    
    # Determine what type we have
    if "type" in creds and creds["type"] == "service_account":
        print("✅ This is a Service Account credential (CORRECT)")
        
        # Check required fields
        required_fields = ["client_email", "private_key", "token_uri"]
        missing = [f for f in required_fields if f not in creds]
        
        if missing:
            print(f"⚠️  Missing required fields: {missing}")
        else:
            print("✅ All required fields present")
            print(f"   Email: {creds.get('client_email', 'N/A')}")
    
    elif "installed" in creds or "web" in creds:
        print("❌ This is an OAuth 2.0 Client credential (WRONG)")
        print()
        print("You need a SERVICE ACCOUNT credential instead.")
        print("See instructions below to create one.")
    
    else:
        print("❓ Unknown credential format")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    check_credentials()
