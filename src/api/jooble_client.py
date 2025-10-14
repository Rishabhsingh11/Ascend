# src/api/jooble_client.py
"""Jooble API client"""

import os
import requests
from typing import List
from dotenv import load_dotenv

from src.logger import get_logger
from src.state import JobPosting

load_dotenv()
logger = get_logger()

class JoobleClient:
    """Client for Jooble Job Search API"""
    
    def __init__(self):
        self.api_key = os.getenv('JOOBLE_API_KEY')
        
        if not self.api_key:
            raise ValueError("Jooble API key not found in .env")
        
        self.base_url = f"https://jooble.org/api/{self.api_key}"
    
    def search_jobs(self, job_title: str, location: str = "New York",
                    max_results: int = 10) -> List[JobPosting]:
        """Search for jobs on Jooble"""
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "keywords": job_title,
            "location": location
        }
        
        try:
            response = requests.post(self.base_url, json=payload, 
                                   headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for result in data.get('jobs', [])[:max_results]:
                job = JobPosting(
                    title=result.get('title', ''),
                    company=result.get('company', 'Unknown'),
                    location=result.get('location', ''),
                    description=result.get('snippet', ''),  # Jooble provides snippets
                    required_skills=[],
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
