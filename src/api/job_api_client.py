# src/api/job_api_client.py
"""Unified job API client with fallback logic"""

import os
from typing import List, Optional
from dotenv import load_dotenv

from src.logger import get_logger
from src.state import JobPosting
from src.api.adzuna_client import AdzunaClient
from src.api.jsearch_client import JSearchClient
from src.api.jooble_client import JoobleClient

load_dotenv()
logger = get_logger()

class JobAPIClient:
    """Unified client that tries multiple APIs with fallback"""
    
    def __init__(self):
        # Initialize all clients
        self.adzuna = AdzunaClient()
        self.jsearch = JSearchClient()
        self.jooble = JoobleClient()
        
        self.max_jobs_per_role = int(os.getenv('MAX_JOBS_PER_ROLE', 10))
        self.default_country = os.getenv('DEFAULT_COUNTRY', 'us')
    
    def search_jobs(self, job_title: str, max_results: int = None) -> List[JobPosting]:
        """
        Search for jobs across all APIs with fallback logic
        
        Args:
            job_title: Job role to search (e.g., "Software Engineer")
            max_results: Maximum jobs to return (default from env)
        
        Returns:
            List of JobPosting objects
        """
        if max_results is None:
            max_results = self.max_jobs_per_role
        
        logger.info(f"Searching for '{job_title}' jobs (max {max_results})")
        
        all_jobs = []
        
        # Try Adzuna first (best free tier)
        try:
            adzuna_jobs = self.adzuna.search_jobs(
                job_title=job_title,
                country=self.default_country,
                max_results=max_results
            )
            all_jobs.extend(adzuna_jobs)
            logger.info(f"✓ Adzuna: {len(adzuna_jobs)} jobs")
        except Exception as e:
            logger.warning(f"✗ Adzuna failed: {e}")
        
        # Try JSearch if we need more results
        if len(all_jobs) < max_results:
            try:
                remaining = max_results - len(all_jobs)
                jsearch_jobs = self.jsearch.search_jobs(
                    job_title=job_title,
                    max_results=remaining
                )
                all_jobs.extend(jsearch_jobs)
                logger.info(f"✓ JSearch: {len(jsearch_jobs)} jobs")
            except Exception as e:
                logger.warning(f"✗ JSearch failed: {e}")
        
        # Try Jooble as last resort
        if len(all_jobs) < max_results:
            try:
                remaining = max_results - len(all_jobs)
                jooble_jobs = self.jooble.search_jobs(
                    job_title=job_title,
                    max_results=remaining
                )
                all_jobs.extend(jooble_jobs)
                logger.info(f"✓ Jooble: {len(jooble_jobs)} jobs")
            except Exception as e:
                logger.warning(f"✗ Jooble failed: {e}")
        
        logger.info(f"Total jobs found: {len(all_jobs)}")
        return all_jobs[:max_results]  # Ensure we don't exceed max
