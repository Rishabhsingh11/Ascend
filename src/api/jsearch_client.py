# src/api/jsearch_client.py
"""JSearch (RapidAPI) client with enhanced filters."""

import os
import requests
from typing import List, Optional
from dotenv import load_dotenv

from src.logger import get_logger
from src.state import JobPosting

load_dotenv()
logger = get_logger()


class JSearchClient:
    """Client for JSearch API (via RapidAPI)."""
    
    BASE_URL = "https://jsearch.p.rapidapi.com/search"
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.api_host = os.getenv('RAPIDAPI_HOST', 'jsearch.p.rapidapi.com')
        
        if not self.api_key:
            logger.warning("RapidAPI key not found in .env")
    
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
        Search for jobs on JSearch with enhanced filters.
        
        Args:
            job_title: Job role to search
            country: Country code (us, uk, ca, etc.)
            posting_hours: Jobs posted within last N hours
            employment_type: FULLTIME, PARTTIME, CONTRACTOR, INTERN
            max_results: Maximum number of results
            location: Optional location filter (e.g., "New York, NY")
        
        Returns:
            List of JobPosting objects
        """
        if not self.api_key:
            logger.warning("JSearch API key not configured, skipping")
            return []
        
        # Convert posting_hours to JSearch date_posted format
        if posting_hours <= 24:
            date_posted = "today"
        elif posting_hours <= 72:
            date_posted = "3days"
        elif posting_hours <= 168:
            date_posted = "week"
        else:
            date_posted = "month"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
        
        # Build query string
        query = job_title
        if location:
            query = f"{job_title} in {location}"
        elif country:
            # Map country codes to location names for better results
            country_names = {
                "us": "United States",
                "uk": "United Kingdom",
                "ca": "Canada",
                "au": "Australia",
                "de": "Germany"
            }
            query = f"{job_title} in {country_names.get(country.lower(), country.upper())}"
        
        params = {
            "query": query,
            "date_posted": date_posted,
            "employment_types": employment_type,
            "num_pages": "1",
            "page": "1"
        }
        
        try:
            logger.debug(f"JSearch API call: {self.BASE_URL}")
            logger.debug(f"  Query: {query}, date_posted={date_posted}, employment={employment_type}")
            
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for result in data.get('data', [])[:max_results]:
                # Build location string
                location_parts = []
                if result.get('job_city'):
                    location_parts.append(result['job_city'])
                if result.get('job_state'):
                    location_parts.append(result['job_state'])
                if result.get('job_country'):
                    location_parts.append(result['job_country'])
                job_location = ', '.join(filter(None, location_parts)) or 'Remote'
                
                job = JobPosting(
                    title=result.get('job_title', ''),
                    company=result.get('employer_name', 'Unknown'),
                    location=job_location,
                    description=result.get('job_description', ''),
                    required_skills=[],  # Will be extracted later
                    url=result.get('job_apply_link', result.get('job_google_link', '')),
                    salary=self._format_salary(
                        result.get('job_min_salary'),
                        result.get('job_max_salary')
                    ),
                    posted_date=result.get('job_posted_at_datetime_utc', ''),
                    source='jsearch'
                )
                jobs.append(job)
            
            logger.info(f"JSearch returned {len(jobs)} jobs for '{job_title}'")
            return jobs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"JSearch API error: {e}")
            return []
        except Exception as e:
            logger.error(f"JSearch unexpected error: {e}")
            return []
    
    def _format_salary(self, min_sal, max_sal):
        """Format salary range."""
        if min_sal and max_sal:
            return f"${min_sal:,.0f} - ${max_sal:,.0f}"
        elif min_sal:
            return f"${min_sal:,.0f}+"
        return None
