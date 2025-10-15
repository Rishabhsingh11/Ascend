# src/api/jooble_client.py
"""Jooble API client with enhanced filters."""

import os
import requests
from typing import List, Optional
from dotenv import load_dotenv

from src.logger import get_logger
from src.state import JobPosting

load_dotenv()
logger = get_logger()


class JoobleClient:
    """Client for Jooble Job Search API."""
    
    def __init__(self):
        self.api_key = os.getenv('JOOBLE_API_KEY')
        
        if not self.api_key:
            logger.warning("Jooble API key not found in .env")
        
        # Jooble URL format: https://jooble.org/api/{api_key}
        self.base_url = f"https://jooble.org/api/{self.api_key}" if self.api_key else None
    
    def search_jobs(
        self,
        job_title: str,
        country: str = "us",
        posting_hours: int = 24,
        employment_type: str = "FULLTIME",
        max_results: int = 20,
        location: Optional[str] = None
    ) -> List[JobPosting]:
        """
        Search for jobs on Jooble with enhanced filters.
        
        Args:
            job_title: Job role to search
            country: Country code (us, uk, ca, etc.)
            posting_hours: Jobs posted within last N hours
            employment_type: FULLTIME, PARTTIME, CONTRACTOR
            max_results: Maximum number of results
            location: Optional location filter (e.g., "New York")
        
        Returns:
            List of JobPosting objects
        """
        if not self.api_key or not self.base_url:
            logger.warning("Jooble API key not configured, skipping")
            return []
        
        # Convert hours to days (Jooble uses days)
        days_old = max(1, posting_hours // 24)
        
        # Jooble requires country-specific endpoint
        url = f"https://jooble.org/api/{self.api_key}"
        
        # Default location based on country if not specified
        if not location:
            default_locations = {
                "us": "United States",
                "uk": "United Kingdom",
                "ca": "Canada",
                "au": "Australia",
                "de": "Germany"
            }
            location = default_locations.get(country.lower(), "")
        
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "keywords": job_title,
            "location": location,
            "radius": "25",  # 25 km/miles radius
            "page": 1,
            "searchMode": str(days_old)  # Days to search back
        }
        
        try:
            logger.debug(f"Jooble API call: {url}")
            logger.debug(f"  Payload: {payload}")
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for result in data.get('jobs', [])[:max_results]:
                job = JobPosting(
                    title=result.get('title', ''),
                    company=result.get('company', 'Unknown'),
                    location=result.get('location', location),
                    description=result.get('snippet', ''),  # Jooble provides snippets
                    required_skills=[],  # Will be extracted later
                    url=result.get('link', ''),
                    salary=result.get('salary', None),
                    posted_date=result.get('updated', ''),
                    source='jooble'
                )
                jobs.append(job)
            
            logger.info(f"Jooble returned {len(jobs)} jobs for '{job_title}'")
            return jobs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Jooble API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Jooble unexpected error: {e}")
            return []
