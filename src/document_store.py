"""SQLite-based document store for caching parsed resume outputs."""

import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from src.logger import get_logger


class DocumentStore:
    """Persistent cache for parsed resume data using SQLite."""
    
    def __init__(self, db_path: str = "db/resume_cache.db"):
        """Initialize document store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.logger = get_logger()
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            self.logger.debug(f"Connected to document store: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to connect to document store: {e}")
            raise
    
    def _create_tables(self):
        """Create cache tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Main cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_cache (
                resume_hash TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                parsed_data TEXT NOT NULL,
                job_roles TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Metadata table for tracking cache statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        self.logger.debug("Document store tables initialized")
    
    def get_cached_resume(self, resume_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached parsed resume data by hash.
        
        Args:
            resume_hash: SHA256 hash of the resume file
            
        Returns:
            Dictionary containing cached data or None if not found
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT resume_hash, file_name, parsed_data, job_roles, summary, created_at
                FROM resume_cache
                WHERE resume_hash = ?
            """, (resume_hash,))
            
            row = cursor.fetchone()
            
            if row:
                # Update last accessed timestamp
                cursor.execute("""
                    UPDATE resume_cache
                    SET last_accessed = CURRENT_TIMESTAMP
                    WHERE resume_hash = ?
                """, (resume_hash,))
                self.conn.commit()
                
                self.logger.info(f"Cache HIT for resume hash: {resume_hash[:12]}...")
                
                return {
                    'resume_hash': row['resume_hash'],
                    'file_name': row['file_name'],
                    'parsed_data': json.loads(row['parsed_data']) if row['parsed_data'] else None,
                    'job_roles': json.loads(row['job_roles']) if row['job_roles'] else None,
                    'summary': json.loads(row['summary']) if row['summary'] else None,
                    'created_at': row['created_at']
                }
            
            self.logger.info(f"Cache MISS for resume hash: {resume_hash[:12]}...")
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def save_cached_resume(
        self, 
        resume_hash: str, 
        file_name: str,
        parsed_data: Dict[str, Any],
        job_roles: Optional[Dict[str, Any]] = None,
        summary: Optional[Dict[str, Any]] = None
    ):
        """Save parsed resume data to cache.
        
        Args:
            resume_hash: SHA256 hash of the resume file
            file_name: Original filename
            parsed_data: Parsed resume Pydantic model as dict
            job_roles: Job role matches (optional)
            summary: Resume summary (optional)
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO resume_cache 
                (resume_hash, file_name, parsed_data, job_roles, summary, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                resume_hash,
                file_name,
                json.dumps(parsed_data, ensure_ascii=False),
                json.dumps(job_roles, ensure_ascii=False) if job_roles else None,
                json.dumps(summary, ensure_ascii=False) if summary else None
            ))
            
            self.conn.commit()
            self.logger.info(f"Saved to cache: {resume_hash[:12]}... ({file_name})")
            
        except Exception as e:
            self.logger.error(f"Error saving to cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            cursor = self.conn.cursor()
            
            # Total cached resumes
            cursor.execute("SELECT COUNT(*) as count FROM resume_cache")
            total_count = cursor.fetchone()['count']
            
            # Most recently accessed
            cursor.execute("""
                SELECT file_name, last_accessed 
                FROM resume_cache 
                ORDER BY last_accessed DESC 
                LIMIT 5
            """)
            recent = cursor.fetchall()
            
            # Database size
            db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            return {
                'total_cached_resumes': total_count,
                'database_size_mb': round(db_size_mb, 2),
                'recent_accesses': [dict(row) for row in recent]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def clear_cache(self):
        """Clear all cached data."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM resume_cache")
            self.conn.commit()
            self.logger.info("Cache cleared")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.logger.debug("Document store connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
