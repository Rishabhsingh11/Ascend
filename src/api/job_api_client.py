# src/api/job_api_client.py
"""Unified job API client with fallback logic and enhanced filters."""

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
    """Unified client that tries multiple APIs with fallback."""
    
    def __init__(self):
        """Initialize all API clients."""
        # Initialize individual clients
        self.adzuna = AdzunaClient()
        self.jsearch = JSearchClient()
        self.jooble = JoobleClient()
        
        # Load configuration from environment
        self.max_jobs_per_role = int(os.getenv('MAX_JOBS_PER_ROLE', 20))
        self.default_country = os.getenv('DEFAULT_COUNTRY', 'us')
        self.default_posting_hours = int(os.getenv('DEFAULT_POSTING_HOURS', 24))
        self.employment_type = os.getenv('EMPLOYMENT_TYPE', 'FULLTIME')
    
    def search_jobs(
        self,
        job_title: str,
        country: Optional[str] = None,
        posting_hours: Optional[int] = None,
        employment_type: Optional[str] = None,
        max_results: Optional[int] = None,
        location: Optional[str] = None
    ) -> List[JobPosting]:
        """
        Search for jobs across all APIs with enhanced filters and fallback logic.
        
        Args:
            job_title: Job role to search (e.g., "Software Engineer")
            country: Country code (us, uk, ca, etc.) - defaults to env setting
            posting_hours: Jobs posted within last N hours (24, 72, 168, 720)
            employment_type: FULLTIME, PARTTIME, CONTRACTOR, INTERN
            max_results: Maximum jobs to return - defaults to env setting
            location: Optional location filter (e.g., "New York, NY")
        
        Returns:
            List of unique JobPosting objects
        """
        # Use defaults from env if not provided
        country = country or self.default_country
        posting_hours = posting_hours or self.default_posting_hours
        employment_type = employment_type or self.employment_type
        max_results = max_results or self.max_jobs_per_role
        
        logger.info(f"Searching for '{job_title}' jobs (max {max_results})")
        logger.debug(f"  Country: {country}")
        logger.debug(f"  Posted within: {posting_hours} hours")
        logger.debug(f"  Employment type: {employment_type}")
        logger.debug(f"  Location: {location or 'Any'}")
        
        all_jobs = []
        
        # ===== Try Adzuna first (best free tier) =====
        try:
            logger.debug("Trying Adzuna...")
            adzuna_jobs = self.adzuna.search_jobs(
                job_title=job_title,
                country=country,
                posting_hours=posting_hours,
                employment_type=employment_type,
                max_results=max_results,
                location=location
            )
            
            if adzuna_jobs:
                all_jobs.extend(adzuna_jobs)
                logger.info(f"✓ Adzuna: {len(adzuna_jobs)} jobs")
            else:
                logger.debug("✗ Adzuna: No jobs found")
                
        except Exception as e:
            logger.warning(f"✗ Adzuna failed: {e}")
        
        # ===== Try JSearch if we need more results =====
        if len(all_jobs) < max_results:
            try:
                remaining = max_results - len(all_jobs)
                logger.debug(f"Trying JSearch (need {remaining} more)...")
                
                jsearch_jobs = self.jsearch.search_jobs(
                    job_title=job_title,
                    country=country,
                    posting_hours=posting_hours,
                    employment_type=employment_type,
                    max_results=remaining,
                    location=location
                )
                
                if jsearch_jobs:
                    all_jobs.extend(jsearch_jobs)
                    logger.info(f"✓ JSearch: {len(jsearch_jobs)} jobs")
                else:
                    logger.debug("✗ JSearch: No jobs found")
                    
            except Exception as e:
                logger.warning(f"✗ JSearch failed: {e}")
        
        # ===== Try Jooble as last resort =====
        if len(all_jobs) < max_results:
            try:
                remaining = max_results - len(all_jobs)
                logger.debug(f"Trying Jooble (need {remaining} more)...")
                
                jooble_jobs = self.jooble.search_jobs(
                    job_title=job_title,
                    country=country,
                    posting_hours=posting_hours,
                    employment_type=employment_type,
                    max_results=remaining,
                    location=location
                )
                
                if jooble_jobs:
                    all_jobs.extend(jooble_jobs)
                    logger.info(f"✓ Jooble: {len(jooble_jobs)} jobs")
                else:
                    logger.debug("✗ Jooble: No jobs found")
                    
            except Exception as e:
                logger.warning(f"✗ Jooble failed: {e}")
        
        # ===== Remove duplicates based on URL =====
        unique_jobs = []
        seen_urls = set()
        
        for job in all_jobs:
            if job.url and job.url not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job.url)
            elif not job.url:
                # Keep jobs without URLs (rare but handle gracefully)
                unique_jobs.append(job)
        
        # Limit to max_results
        final_jobs = unique_jobs[:max_results]
        
        logger.info(f"Total jobs found: {len(final_jobs)}")
        
        return final_jobs
    
    def search_with_fallback_dates(
        self,
        job_title: str,
        country: Optional[str] = None,
        employment_type: Optional[str] = None,
        max_results: Optional[int] = None,
        location: Optional[str] = None
    ) -> tuple[List[JobPosting], int]:
        """
        Search with progressive date fallback if no results found.
        
        Tries: 24 hours → 3 days → 7 days → 30 days
        
        Returns:
            Tuple of (jobs, posting_hours_used)
        """
        posting_hours_options = [24, 72, 168, 720]  # 1 day, 3 days, 7 days, 30 days
        
        for hours in posting_hours_options:
            logger.info(f"🔍 Searching jobs posted within {hours} hours...")
            
            jobs = self.search_jobs(
                job_title=job_title,
                country=country,
                posting_hours=hours,
                employment_type=employment_type,
                max_results=max_results,
                location=location
            )
            
            if jobs:
                logger.info(f"✅ Found {len(jobs)} jobs with {hours} hour filter")
                return jobs, hours
            else:
                logger.warning(f"⚠️  No jobs found with {hours} hour filter, trying longer period...")
        
        # If still no results after 30 days
        logger.warning("❌ No jobs found even with 30-day filter")
        return [], 720


logger.info("✅ JobAPIClient initialized")
