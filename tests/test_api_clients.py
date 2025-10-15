# tests/test_all_api_clients.py
"""Test all API clients with enhanced filters."""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.adzuna_client import AdzunaClient
from src.api.jsearch_client import JSearchClient
from src.api.jooble_client import JoobleClient

def test_all_clients():
    """Test all three API clients with same query."""
    
    print("=" * 80)
    print("TESTING ALL API CLIENTS")
    print("=" * 80)
    print()
    
    search_params = {
        "job_title": "Data Scientist",
        "country": "us",
        "posting_hours": 24,
        "employment_type": "FULLTIME",
        "max_results": 5,
        "location": "New York"
    }
    
    # Test Adzuna
    print("1. Testing Adzuna...")
    adzuna = AdzunaClient()
    adzuna_jobs = adzuna.search_jobs(**search_params)
    print(f"   ✅ Found {len(adzuna_jobs)} jobs\n")
    
    # Test JSearch
    print("2. Testing JSearch...")
    jsearch = JSearchClient()
    jsearch_jobs = jsearch.search_jobs(**search_params)
    print(f"   ✅ Found {len(jsearch_jobs)} jobs\n")
    
    # Test Jooble
    print("3. Testing Jooble...")
    jooble = JoobleClient()
    jooble_jobs = jooble.search_jobs(**search_params)
    print(f"   ✅ Found {len(jooble_jobs)} jobs\n")
    
    total_jobs = len(adzuna_jobs) + len(jsearch_jobs) + len(jooble_jobs)
    print(f"Total: {total_jobs} jobs across all APIs")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_all_clients()
