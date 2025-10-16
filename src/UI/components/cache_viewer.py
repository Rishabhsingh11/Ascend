"""Database management component for Cache and Job History."""

import streamlit as st
from src.document_store import DocumentStore
from src.jobs.job_store import JobStore
from src.cleanup import cleanup_all, get_directory_size
import pandas as pd
from datetime import datetime


def render_database_manager():
    """Render database management interface for both Cache and Job History."""
    
    st.title("🗄️ Database Manager")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📦 Resume Cache",
        "💼 Job History",
        "🧹 Cleanup"
    ])
    
    # ========== TAB 1: RESUME CACHE ==========
    with tab1:
        render_cache_stats()
    
    # ========== TAB 2: JOB HISTORY ==========
    with tab2:
        render_job_history_stats()
    
    # ========== TAB 3: CLEANUP ==========
    with tab3:
        render_cleanup_tools()


def render_cache_stats():
    """Render cache statistics."""
    
    st.subheader("📦 Resume Cache Database")
    st.caption("Fast access to previously analyzed resumes (Phase 1 only)")
    
    try:
        with DocumentStore() as doc_store:
            stats = doc_store.get_cache_stats()
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Cached Resumes",
                    stats.get('total_cached_resumes', 0),
                    help="Phase 1 analyses stored for instant reload"
                )
            
            with col2:
                st.metric(
                    "Database Size",
                    f"{stats.get('database_size_mb', 0):.2f} MB",
                    help="Size of resume cache database"
                )
            
            with col3:
                st.metric(
                    "Total Analyses",
                    stats.get('total_cached_resumes', 0)
                )
            
            # Recent accesses
            if stats.get('recent_accesses'):
                st.markdown("---")
                st.subheader("🕐 Recently Accessed")
                
                recent_data = []
                for access in stats['recent_accesses']:
                    recent_data.append({
                        'File Name': access['file_name'],
                        'Last Accessed': access['last_accessed'],
                        'Hit Count': access.get('access_count', 1)
                    })
                
                df = pd.DataFrame(recent_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Actions
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Refresh Stats", use_container_width=True):
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Clear All Cache", type="primary", use_container_width=True):
                    if st.session_state.get('confirm_clear_cache', False):
                        doc_store.clear_cache()
                        st.success("✅ Cache cleared!")
                        st.session_state.confirm_clear_cache = False
                        st.rerun()
                    else:
                        st.session_state.confirm_clear_cache = True
                        st.warning("⚠️ Click again to confirm")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def render_job_history_stats():
    """Render job history statistics."""
    
    st.subheader("💼 Job History Database")
    st.caption("Complete job search history with skill gap analysis")
    
    try:
        job_store = JobStore()
        stats = job_store.get_stats()
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Sessions",
                stats.get('total_sessions', 0),
                help="Number of job search sessions"
            )
        
        with col2:
            st.metric(
                "Total Jobs",
                stats.get('total_jobs', 0),
                help="Job postings analyzed"
            )
        
        with col3:
            st.metric(
                "Emails Sent",
                stats.get('emails_sent', 0),
                help="Successful email deliveries"
            )
        
        with col4:
            db_size = get_directory_size('db')
            st.metric(
                "Database Size",
                f"{db_size:.2f} MB"
            )
        
        # Recent sessions
        if stats.get('recent_sessions'):
            st.markdown("---")
            st.subheader("📅 Recent Job Searches")
            
            session_data = []
            for session in stats['recent_sessions']:
                session_data.append({
                    'Date': session.get('search_date', 'N/A'),
                    'Resume': session.get('resume_filename', 'N/A'),
                    'Jobs Found': session.get('total_jobs_found', 0),
                    'Market Readiness': f"{session.get('market_readiness', 0)}%" if session.get('market_readiness') else 'N/A'
                })
            
            df = pd.DataFrame(session_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Detailed session browser
        st.markdown("---")
        st.subheader("🔍 Browse Sessions")
        
        # Get all sessions
        all_sessions = job_store.get_all_sessions()
        
        if all_sessions:
            # Session selector
            session_options = {
                f"{s['created_at']} - {s['resume_filename']} ({s['jobs_count']} jobs)": s['session_id']
                for s in all_sessions
            }
            
            selected_display = st.selectbox(
                "Select a session to view details:",
                options=list(session_options.keys())
            )
            
            if selected_display:
                session_id = session_options[selected_display]
                
                # Get session details
                jobs = job_store.get_session_jobs(session_id)
                
                if jobs:
                    st.markdown(f"**Session ID:** `{session_id}`")
                    st.markdown(f"**Jobs in this session:** {len(jobs)}")
                    
                    # Display jobs in expander
                    with st.expander(f"📋 View {len(jobs)} Jobs", expanded=False):
                        job_data = []
                        for job in jobs[:50]:  # Limit to 50 for performance
                            job_data.append({
                                'Title': job.get('title', 'N/A'),
                                'Company': job.get('company', 'N/A'),
                                'Location': job.get('location', 'N/A'),
                                'Salary': job.get('salary', 'Not specified'),
                                'Source': job.get('source', 'N/A'),
                                'URL': job.get('url', 'N/A')
                            })
                        
                        jobs_df = pd.DataFrame(job_data)
                        st.dataframe(jobs_df, use_container_width=True, hide_index=True)
                    
                    # Delete session option
                    if st.button(f"🗑️ Delete This Session", use_container_width=True):
                        if st.session_state.get(f'confirm_delete_{session_id}', False):
                            job_store.delete_session(session_id)
                            st.success("✅ Session deleted!")
                            st.session_state[f'confirm_delete_{session_id}'] = False
                            st.rerun()
                        else:
                            st.session_state[f'confirm_delete_{session_id}'] = True
                            st.warning("⚠️ Click again to confirm deletion")
        else:
            st.info("No job search sessions found yet")
        
        job_store.close()
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def render_cleanup_tools():
    """Render cleanup tools."""
    
    st.subheader("🧹 Cleanup Tools")
    st.caption("Manage disk space and clean old files")
    
    # Current disk usage
    st.markdown("### 📊 Current Storage")
    
    col1, col2 = st.columns(2)
    
    with col1:
        logs_size = get_directory_size('logs')
        st.metric("Logs Directory", f"{logs_size:.2f} MB")
    
    with col2:
        exports_size = get_directory_size('exports')
        st.metric("Exports Directory", f"{exports_size:.2f} MB")
    
    st.markdown("---")
    
    # Cleanup settings
    st.markdown("### ⚙️ Cleanup Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        logs_age = st.slider(
            "Delete logs older than (hours):",
            min_value=1,
            max_value=168,  # 1 week
            value=24,
            help="Logs older than this will be deleted"
        )
    
    with col2:
        exports_keep = st.slider(
            "Keep most recent exports:",
            min_value=1,
            max_value=50,
            value=5,
            help="Number of recent CSV exports to keep"
        )
    
    st.markdown("---")
    
    # Run cleanup
    if st.button("🧹 Run Cleanup", type="primary", use_container_width=True):
        with st.spinner("Cleaning up..."):
            results = cleanup_all(
                logs_max_age=logs_age,
                exports_keep=exports_keep
            )
            
            st.success("✅ Cleanup complete!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Logs Deleted", results['logs_deleted'])
                st.metric("New Logs Size", f"{results['logs_size_mb']:.2f} MB")
            
            with col2:
                st.metric("Exports Deleted", results['exports_deleted'])
                st.metric("New Exports Size", f"{results['exports_size_mb']:.2f} MB")


def render_sidebar_database_info():
    """Render database info in sidebar."""
    try:
        with DocumentStore() as doc_store:
            cache_stats = doc_store.get_cache_stats()
        
        job_store = JobStore()
        job_stats = job_store.get_stats()
        job_store.close()
        
        st.sidebar.markdown("### 🗄️ Database")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Cache",
                cache_stats.get('total_cached_resumes', 0),
                help="Cached resumes"
            )
        
        with col2:
            st.metric(
                "Jobs",
                job_stats.get('total_jobs', 0),
                help="Total jobs analyzed"
            )
    
    except:
        pass
