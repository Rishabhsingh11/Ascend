# src/job_store.py
"""Job recommendations storage and history management."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager

from src.logger import get_logger
from src.state import JobPosting

logger = get_logger()


class JobStore:
    """Manages storage and retrieval of job recommendations."""
    
    def __init__(self, db_path: str = "db/job_history.db"):
        """
        Initialize job store with database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Initializing JobStore: {self.db_path}")
        
        # Create tables
        self._create_tables()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create job history tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # ===== Job Search Sessions Table =====
            # Tracks each time jobs are fetched for a resume
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_search_sessions (
                    session_id TEXT PRIMARY KEY,
                    resume_hash TEXT NOT NULL,
                    resume_filename TEXT NOT NULL,
                    candidate_name TEXT,
                    candidate_email TEXT,
                    search_date TEXT NOT NULL,
                    total_jobs_found INTEGER DEFAULT 0,
                    job_roles TEXT,  -- JSON array of job roles searched
                    market_readiness REAL,
                    google_sheet_url TEXT,
                    email_sent BOOLEAN DEFAULT 0,
                    email_sent_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (resume_hash) REFERENCES resume_cache(resume_hash)
                )
            """)
            
            # ===== Job Recommendations Table =====
            # Stores individual job postings fetched
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_recommendations (
                    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT NOT NULL,
                    description TEXT,
                    required_skills TEXT,  -- JSON array
                    salary TEXT,
                    job_url TEXT,
                    posted_date TEXT,
                    source TEXT NOT NULL,  -- adzuna, jsearch, jooble
                    matched_role TEXT,  -- Which of top 3 roles this matched
                    relevance_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES job_search_sessions(session_id)
                )
            """)
            
            # ===== Job Application Tracking (Future Feature) =====
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_applications (
                    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    application_status TEXT DEFAULT 'not_applied',  -- not_applied, applied, interviewing, rejected, offered
                    applied_date TEXT,
                    notes TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES job_recommendations(job_id),
                    FOREIGN KEY (session_id) REFERENCES job_search_sessions(session_id)
                )
            """)
            
            # ===== Indexes for Performance =====
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_resume_hash 
                ON job_search_sessions(resume_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_session 
                ON job_recommendations(session_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_company 
                ON job_recommendations(company)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_date 
                ON job_search_sessions(search_date)
            """)
            
            logger.debug("Job history tables initialized")
    
    def create_session(
        self,
        resume_hash: str,
        resume_filename: str,
        candidate_name: Optional[str] = None,
        candidate_email: Optional[str] = None,
        job_roles: List[str] = None,
        market_readiness: Optional[float] = None
    ) -> str:
        """
        Create a new job search session.
        
        Args:
            resume_hash: Unique hash of the resume
            resume_filename: Original filename
            candidate_name: Candidate's name from resume
            candidate_email: Candidate's email
            job_roles: List of job roles searched (top 3)
            market_readiness: Overall market readiness score
            
        Returns:
            session_id: Unique session identifier
        """
        import uuid
        import json
        
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        search_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO job_search_sessions (
                    session_id, resume_hash, resume_filename, candidate_name, 
                    candidate_email, search_date, job_roles, market_readiness
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                resume_hash,
                resume_filename,
                candidate_name,
                candidate_email,
                search_date,
                json.dumps(job_roles) if job_roles else None,
                market_readiness
            ))
            
            logger.info(f"Created job search session: {session_id}")
            logger.debug(f"  Resume: {resume_filename}")
            logger.debug(f"  Candidate: {candidate_name} ({candidate_email})")
            logger.debug(f"  Roles: {job_roles}")
        
        return session_id
    
    def save_job(
        self,
        session_id: str,
        job: JobPosting,
        matched_role: Optional[str] = None,
        relevance_score: Optional[float] = None
    ) -> int:
        """
        Save a single job recommendation.
        
        Args:
            session_id: Job search session ID
            job: JobPosting object
            matched_role: Which of top 3 roles this job matched
            relevance_score: Relevance score (0-1)
            
        Returns:
            job_id: Database ID of saved job
        """
        import json
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO job_recommendations (
                    session_id, job_title, company, location, description,
                    required_skills, salary, job_url, posted_date, source,
                    matched_role, relevance_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                job.title,
                job.company,
                job.location,
                job.description[:1000] if job.description else None,  # Truncate long descriptions
                json.dumps(job.required_skills) if job.required_skills else None,
                job.salary,
                job.url,
                job.posted_date,
                job.source,
                matched_role,
                relevance_score
            ))
            
            job_id = cursor.lastrowid
            
            logger.debug(f"Saved job: {job.title} @ {job.company} (ID: {job_id})")
        
        return job_id
    
    def save_jobs_batch(
        self,
        session_id: str,
        jobs: List[JobPosting],
        job_roles: List[str]
    ) -> int:
        """
        Save multiple jobs in batch.
        
        Args:
            session_id: Job search session ID
            jobs: List of JobPosting objects
            job_roles: List of job roles for matching
            
        Returns:
            Number of jobs saved
        """
        saved_count = 0
        
        for job in jobs:
            # Determine which role this job matches
            matched_role = None
            for role in job_roles:
                if any(word.lower() in job.title.lower() 
                      for word in role.split() 
                      if len(word) > 3):
                    matched_role = role
                    break
            
            try:
                self.save_job(session_id, job, matched_role=matched_role)
                saved_count += 1
            except Exception as e:
                logger.warning(f"Failed to save job {job.title}: {e}")
                continue
        
        # Update total jobs count in session
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE job_search_sessions 
                SET total_jobs_found = ? 
                WHERE session_id = ?
            """, (saved_count, session_id))
        
        logger.info(f"Saved {saved_count} jobs to session {session_id}")
        
        return saved_count
    
    def get_session_jobs(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all jobs for a specific session.
        
        Args:
            session_id: Job search session ID
            
        Returns:
            List of job dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM job_recommendations 
                WHERE session_id = ? 
                ORDER BY created_at DESC
            """, (session_id,))
            
            rows = cursor.fetchall()
            
            jobs = []
            for row in rows:
                job_dict = dict(row)
                
                # Parse JSON fields
                import json
                if job_dict.get('required_skills'):
                    job_dict['required_skills'] = json.loads(job_dict['required_skills'])
                
                jobs.append(job_dict)
            
            logger.debug(f"Retrieved {len(jobs)} jobs for session {session_id}")
        
        return jobs
    
    def get_resume_sessions(self, resume_hash: str) -> List[Dict[str, Any]]:
        """
        Get all job search sessions for a specific resume.
        
        Args:
            resume_hash: Resume hash from document store
            
        Returns:
            List of session dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM job_search_sessions 
                WHERE resume_hash = ? 
                ORDER BY search_date DESC
            """, (resume_hash,))
            
            rows = cursor.fetchall()
            
            sessions = []
            for row in rows:
                session_dict = dict(row)
                
                # Parse JSON fields
                import json
                if session_dict.get('job_roles'):
                    session_dict['job_roles'] = json.loads(session_dict['job_roles'])
                
                sessions.append(session_dict)
            
            logger.debug(f"Retrieved {len(sessions)} sessions for resume {resume_hash[:16]}")
        
        return sessions
    
    def update_session_email_sent(
        self,
        session_id: str,
        google_sheet_url: Optional[str] = None
    ):
        """
        Mark email as sent for a session.
        
        Args:
            session_id: Job search session ID
            google_sheet_url: URL of created Google Sheet
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE job_search_sessions 
                SET email_sent = 1, 
                    email_sent_date = ?, 
                    google_sheet_url = ?
                WHERE session_id = ?
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                google_sheet_url,
                session_id
            ))
            
            logger.info(f"Marked email sent for session {session_id}")
    
    def clear_all_data(self):
        """
        Clear all data from all tables (USE WITH CAUTION).
    
        This is useful for testing or resetting the database.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
        
            # Delete in order to respect foreign key constraints
            cursor.execute("DELETE FROM job_applications")
            cursor.execute("DELETE FROM job_recommendations")
            cursor.execute("DELETE FROM job_search_sessions")
            
            logger.warning("⚠️  All job history data cleared!")

    def delete_session(self, session_id: str):
        """
        Delete a specific session and all its jobs.
        
        Args:
            session_id: Session ID to delete
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete related jobs first
            cursor.execute("DELETE FROM job_recommendations WHERE session_id = ?", (session_id,))
            
            # Delete session
            cursor.execute("DELETE FROM job_search_sessions WHERE session_id = ?", (session_id,))
            
            logger.info(f"Deleted session: {session_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall job history statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total sessions
            cursor.execute("SELECT COUNT(*) FROM job_search_sessions")
            total_sessions = cursor.fetchone()[0]
            
            # Total jobs
            cursor.execute("SELECT COUNT(*) FROM job_recommendations")
            total_jobs = cursor.fetchone()[0]
            
            # Emails sent
            cursor.execute("SELECT COUNT(*) FROM job_search_sessions WHERE email_sent = 1")
            emails_sent = cursor.fetchone()[0]
            
            # Recent sessions
            cursor.execute("""
                SELECT search_date, resume_filename, total_jobs_found 
                FROM job_search_sessions 
                ORDER BY search_date DESC 
                LIMIT 5
            """)
            recent_sessions = [dict(row) for row in cursor.fetchall()]
            
            stats = {
                'total_sessions': total_sessions,
                'total_jobs': total_jobs,
                'emails_sent': emails_sent,
                'recent_sessions': recent_sessions
            }
            
            logger.debug(f"Job store stats: {stats}")
        
        return stats
    
    def close(self):
        """Close database connection (cleanup)."""
        logger.debug("JobStore closed")

    # Add this method to JobStore class in src/jobs/job_store.py

    def update_session_market_readiness(self, session_id: str, market_readiness: float):
        """
        Update market readiness score for a session.
        
        Args:
            session_id: Session ID to update
            market_readiness: Market readiness percentage (0-100)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE job_search_sessions 
                SET market_readiness = ? 
                WHERE session_id = ?
            """, (market_readiness, session_id))
            
            logger.debug(f"Updated market readiness for {session_id}: {market_readiness}%")



logger.info("✅ JobStore module initialized")
