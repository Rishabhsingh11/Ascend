"""Cache management component."""

import streamlit as st
from src.document_store import DocumentStore
import pandas as pd


def render_cache_stats():
    """Render cache statistics and management interface."""
    
    st.subheader("📊 Cache Statistics")
    
    try:
        with DocumentStore() as doc_store:
            stats = doc_store.get_cache_stats()
            
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Total Cached Resumes",
                    stats.get('total_cached_resumes', 0),
                    help="Number of resumes stored in cache"
                )
            
            with col2:
                st.metric(
                    "Database Size",
                    f"{stats.get('database_size_mb', 0)} MB",
                    help="Total size of cache database"
                )
            
            # Recent accesses
            if stats.get('recent_accesses'):
                st.subheader("🕐 Recently Accessed Resumes")
                
                recent_data = []
                for access in stats['recent_accesses']:
                    recent_data.append({
                        'File Name': access['file_name'],
                        'Last Accessed': access['last_accessed']
                    })
                
                df = pd.DataFrame(recent_data)
                st.dataframe(df, width='stretch', hide_index=True)
            
            # Cache management
            st.subheader("🗑️ Cache Management")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Refresh Stats", width='stretch'):
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Clear Cache", type="primary", width='stretch'):
                    if st.session_state.get('confirm_clear', False):
                        doc_store.clear_cache()
                        st.success("✅ Cache cleared successfully!")
                        st.session_state.confirm_clear = False
                        st.rerun()
                    else:
                        st.session_state.confirm_clear = True
                        st.warning("⚠️ Click again to confirm cache deletion")
    
    except Exception as e:
        st.error(f"❌ Error loading cache statistics: {str(e)}")


def render_sidebar_cache_info():
    """Render cache info in sidebar."""
    try:
        with DocumentStore() as doc_store:
            stats = doc_store.get_cache_stats()
            
            st.sidebar.metric(
                "Cached Resumes",
                stats.get('total_cached_resumes', 0)
            )
    except:
        pass
