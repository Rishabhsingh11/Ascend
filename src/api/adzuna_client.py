# src/api/adzuna_client.py
"""Adzuna API client with enhanced filters."""

import os
import requests
from typing import List, Optional
from dotenv import load_dotenv

from src.logger import get_logger
from src.state import JobPosting

load_dotenv()
logger = get_logger()


class AdzunaClient:
    """Client for Adzuna Job Search API."""
    
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    
    def __init__(self):
        self.app_id = os.getenv('ADZUNA_APP_ID')
        self.app_key = os.getenv('ADZUNA_APP_KEY')
        
        if not self.app_id or not self.app_key:
            logger.warning("Adzuna API credentials not found in .env")
    
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
        Search for jobs on Adzuna with enhanced filters.
        
        Args:
            job_title: Job role to search
            country: Country code (us, uk, de, ca, au, etc.)
            posting_hours: Jobs posted within last N hours
            employment_type: FULLTIME, PARTTIME, CONTRACTOR
            max_results: Maximum number of results
            location: Optional location filter (e.g., "New York")
        
        Returns:
            List of JobPosting objects
        """
        if not self.app_id or not self.app_key:
            logger.warning("Adzuna credentials not configured, skipping")
            return []
        
        # Convert hours to days (Adzuna uses days)
        days_old = max(1, posting_hours // 24)
        
        url = f"{self.BASE_URL}/{country}/search/1"
        
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'results_per_page': min(max_results, 50),  # API limit is 50
            'what': job_title,
            'max_days_old': days_old,
            'content-type': 'application/json'
        }
        
        # Add location filter if specified
        if location:
            params['where'] = location
        
        # Add employment type filters (Adzuna specific)
        if employment_type == "FULLTIME":
            params['full_time'] = 1
        elif employment_type == "PARTTIME":
            params['part_time'] = 1
        elif employment_type == "CONTRACTOR":
            params['contract'] = 1
        
        try:
            logger.debug(f"Adzuna API call: {url}")
            logger.debug(f"  Params: what={job_title}, max_days_old={days_old}, employment={employment_type}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for result in data.get('results', []):
                job = JobPosting(
                    title=result.get('title', ''),
                    company=result.get('company', {}).get('display_name', 'Unknown'),
                    location=result.get('location', {}).get('display_name', ''),
                    description=result.get('description', ''),
                    required_skills=[],  # Will be extracted later by skill extractor
                    url=result.get('redirect_url', ''),
                    salary=self._format_salary(
                        result.get('salary_min'), 
                        result.get('salary_max')
                    ),
                    posted_date=result.get('created', ''),
                    source='adzuna'
                )
                jobs.append(job)
            
            logger.info(f"Adzuna returned {len(jobs)} jobs for '{job_title}'")
            return jobs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Adzuna API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Adzuna unexpected error: {e}")
            return []
    
    def _format_salary(self, min_sal, max_sal):
        """Format salary range."""
        if min_sal and max_sal:
            return f"${min_sal:,.0f} - ${max_sal:,.0f}"
        elif min_sal:
            return f"${min_sal:,.0f}+"
        return None
