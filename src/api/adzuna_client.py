# src/api/adzuna_client.py
"""Adzuna API client"""

import os
import requests
from typing import List
from dotenv import load_dotenv

from src.logger import get_logger
from src.state import JobPosting

load_dotenv()
logger = get_logger()

class AdzunaClient:
    """Client for Adzuna Job Search API"""
    
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    
    def __init__(self):
        self.app_id = os.getenv('ADZUNA_APP_ID')
        self.app_key = os.getenv('ADZUNA_APP_KEY')
        
        if not self.app_id or not self.app_key:
            raise ValueError("Adzuna API credentials not found in .env")
    
    def search_jobs(self, job_title: str, country: str = "us", 
                    max_results: int = 10) -> List[JobPosting]:
        """
        Search for jobs on Adzuna
        
        Args:
            job_title: Job role to search
            country: Country code (us, uk, de, etc.)
            max_results: Maximum number of results
        
        Returns:
            List of JobPosting objects
        """
        url = f"{self.BASE_URL}/{country}/search/1"
        
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'results_per_page': min(max_results, 50),  # API limit
            'what': job_title,
            'content-type': 'application/json'
        }
        
        try:
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
                    required_skills=[],  # Will be extracted later
                    url=result.get('redirect_url', ''),
                    salary=self._format_salary(result.get('salary_min'), result.get('salary_max')),
                    posted_date=result.get('created', ''),
                    source='adzuna'
                )
                jobs.append(job)
            
            logger.info(f"Adzuna returned {len(jobs)} jobs for '{job_title}'")
            return jobs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Adzuna API error: {e}")
            return []
    
    def _format_salary(self, min_sal, max_sal):
        """Format salary range"""
        if min_sal and max_sal:
            return f"${min_sal:,.0f} - ${max_sal:,.0f}"
        elif min_sal:
            return f"${min_sal:,.0f}+"
        return None
