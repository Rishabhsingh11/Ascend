# src/api/jsearch_client.py
"""JSearch (RapidAPI) client"""

import os
import requests
from typing import List
from dotenv import load_dotenv

from src.logger import get_logger
from src.state import JobPosting

load_dotenv()
logger = get_logger()

class JSearchClient:
    """Client for JSearch API (via RapidAPI)"""
    
    BASE_URL = "https://jsearch.p.rapidapi.com/search"
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.api_host = os.getenv('RAPIDAPI_HOST', 'jsearch.p.rapidapi.com')
        
        if not self.api_key:
            raise ValueError("RapidAPI key not found in .env")
    
    def search_jobs(self, job_title: str, location: str = "United States",
                    max_results: int = 10) -> List[JobPosting]:
        """Search for jobs on JSearch"""
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
        
        params = {
            "query": f"{job_title} in {location}",
            "num_pages": "1",
            "page": "1"
        }
        
        try:
            response = requests.get(self.BASE_URL, headers=headers, 
                                  params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for result in data.get('data', [])[:max_results]:
                job = JobPosting(
                    title=result.get('job_title', ''),
                    company=result.get('employer_name', 'Unknown'),
                    location=result.get('job_city', '') + ', ' + result.get('job_state', ''),
                    description=result.get('job_description', ''),
                    required_skills=[],
                    url=result.get('job_apply_link', ''),
                    salary=self._format_salary(result.get('job_min_salary'), 
                                              result.get('job_max_salary')),
                    posted_date=result.get('job_posted_at_datetime_utc', ''),
                    source='jsearch'
                )
                jobs.append(job)
            
            logger.info(f"JSearch returned {len(jobs)} jobs for '{job_title}'")
            return jobs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"JSearch API error: {e}")
            return []
    
    def _format_salary(self, min_sal, max_sal):
        if min_sal and max_sal:
            return f"${min_sal:,.0f} - ${max_sal:,.0f}"
        return None
