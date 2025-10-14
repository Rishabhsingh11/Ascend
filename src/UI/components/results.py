"""Results display component for resume analysis."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any
from src.UI.components.skill_gap_viewer import render_skill_gap_analysis


def render_results(result: Dict[str, Any]):
    """Render complete analysis results with visualizations.
    
    Args:
        result: Final agent state with all analysis results
    """
    if result.get('error'):
        st.error(f"❌ Error: {result['error']}")
        return
    
    # Contact Info Section
    render_contact_info(result.get('parsed_resume'))
    
    st.divider()
    
    # Skills Overview
    render_skills_section(result.get('parsed_resume'))
    
    st.divider()
    
    # Job Role Matches
    render_job_matches(result.get('job_role_matches'))
    
    st.divider()
    
    # Resume Summary & Quality
    render_summary_section(result.get('resume_summary'))
    
    st.divider()
    
    # Experience Timeline
    render_experience_section(result.get('parsed_resume'))
    
    st.divider()
    
    # Education
    render_education_section(result.get('parsed_resume'))
    # ===== PHASE 2 RESULTS (NEW) =====
    
    # Check if skill gap analysis exists
    if result.get('skill_gap_analysis'):
        # Render the complete skill gap analysis
        render_skill_gap_analysis(result['skill_gap_analysis'])
    elif result.get('enable_skill_gap') == False:
        # User disabled Phase 2
        st.info("ℹ️ **Skill Gap Analysis was disabled** for this resume. Enable it when analyzing to see market insights.")
    elif result.get('job_postings') and len(result['job_postings']) == 0:
        # Jobs were fetched but none found
        st.warning("⚠️ **No job postings found** for your recommended roles. Skill gap analysis requires job data.")
    else:
        # No skill gap data at all (old cached results)
        st.info("ℹ️ **Skill Gap Analysis not available**. This may be an older cached result. Re-analyze the resume to see Phase 2 insights.")


def render_contact_info(parsed_resume):
    """Display contact information."""
    if not parsed_resume:
        return
    
    st.header("👤 Contact Information")
    
    contact = parsed_resume.contact_info
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Name", contact.name or "N/A")
    
    with col2:
        if contact.email:
            st.markdown(f"**Email**  \n📧 {contact.email}")
        else:
            st.metric("Email", "N/A")
    
    with col3:
        if contact.phone:
            st.markdown(f"**Phone**  \n📱 {contact.phone}")
        else:
            st.metric("Phone", "N/A")
    
    with col4:
        if contact.location:
            st.markdown(f"**Location**  \n📍 {contact.location}")
        else:
            st.metric("Location", "N/A")
    
    if contact.linkedin:
        st.markdown(f"**LinkedIn:** [Profile Link]({contact.linkedin})")


def render_skills_section(parsed_resume):
    """Display skills with visual representation."""
    if not parsed_resume or not parsed_resume.skills:
        return
    
    st.header("🛠️ Skills")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Total Skills: {len(parsed_resume.skills)}")
        
        # Display skills as tags
        skills_html = ""
        for skill in parsed_resume.skills:
            skills_html += f'<span style="display: inline-block; background-color: #3B82F6; color: white; padding: 0.4rem 0.8rem; margin: 0.3rem; border-radius: 20px; font-size: 0.9rem;">{skill}</span>'
        
        st.markdown(f'<div style="margin-top: 1rem;">{skills_html}</div>', unsafe_allow_html=True)
    
    with col2:
        # Skills count visualization
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=len(parsed_resume.skills),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Skills Count"},
            gauge={
                'axis': {'range': [None, 50]},
                'bar': {'color': "#3B82F6"},
                'steps': [
                    {'range': [0, 15], 'color': "#FEE2E2"},
                    {'range': [15, 30], 'color': "#FEF3C7"},
                    {'range': [30, 50], 'color': "#D1FAE5"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 35
                }
            }
        ))
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, config={'displayModeBar': False}, key='skills_gauge')


def render_job_matches(job_matches):
    """Display job role recommendations."""
    if not job_matches:
        st.warning("⚠️ No job role matches available")
        return
    
    st.header("🎯 Top Job Role Recommendations")
    
    for idx, match in enumerate(job_matches, 1):
        with st.expander(f"**{idx}. {match.role_title}** - Confidence: {match.confidence_score:.0%}", expanded=(idx==1)):
            
            # Confidence score bar
            st.progress(match.confidence_score, text=f"Match Score: {match.confidence_score:.0%}")
            
            # Reasoning
            st.subheader("📝 Why This Role?")
            st.write(match.reasoning)
            
            # Matching skills
            st.subheader("✅ Matching Skills")
            skills_cols = st.columns(3)
            for i, skill in enumerate(match.key_matching_skills):
                with skills_cols[i % 3]:
                    st.markdown(f"- {skill}")
    
    # Visualization: Confidence comparison
    st.subheader("📊 Confidence Score Comparison")
    
    fig = go.Figure(data=[
        go.Bar(
            x=[match.role_title for match in job_matches],
            y=[match.confidence_score * 100 for match in job_matches],
            marker_color=['#10B981', '#3B82F6', '#6366F1'],
            text=[f"{match.confidence_score:.0%}" for match in job_matches],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Job Role Match Confidence",
        xaxis_title="Job Role",
        yaxis_title="Confidence Score (%)",
        yaxis_range=[0, 100],
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, config={'displayModeBar': False}, key='job_confidence_chart')


def render_summary_section(summary):
    """Display resume summary and quality assessment."""
    if not summary:
        st.warning("⚠️ No summary available")
        return
    
    st.header("📊 Resume Quality Assessment")
    
    # Quality score with gauge
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Quality score gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=summary.quality_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Quality Score", 'font': {'size': 24}},
            delta={'reference': 7.0, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 10], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#10B981" if summary.quality_score >= 7 else "#F59E0B"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 4], 'color': '#FEE2E2'},
                    {'range': [4, 7], 'color': '#FEF3C7'},
                    {'range': [7, 10], 'color': '#D1FAE5'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 8
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            font={'color': "darkblue", 'family': "Arial"}
        )
        
        st.plotly_chart(fig, config={'displayModeBar': False}, key='quality_gauge')
    
    with col2:
        st.subheader("📝 Profile Summary")
        st.info(summary.overall_summary)
        
        if summary.years_of_experience:
            st.metric("📅 Experience", f"{summary.years_of_experience} years")
    
    # Strengths
    if summary.key_strengths:
        st.subheader("💪 Key Strengths")
        strengths_cols = st.columns(2)
        for i, strength in enumerate(summary.key_strengths):
            with strengths_cols[i % 2]:
                st.success(f"✅ {strength}")
    
    # Issues
    if summary.grammatical_issues:
        st.subheader("⚠️ Issues Found")
        with st.expander(f"View {len(summary.grammatical_issues)} issues"):
            for issue in summary.grammatical_issues:
                st.warning(f"⚠️ {issue}")
    
    # Improvement suggestions
    if summary.improvement_suggestions:
        st.subheader("💡 Improvement Suggestions")
        for i, suggestion in enumerate(summary.improvement_suggestions, 1):
            st.markdown(f"{i}. {suggestion}")


def render_experience_section(parsed_resume):
    """Display work experience timeline."""
    if not parsed_resume or not parsed_resume.experience:
        return
    
    st.header("💼 Work Experience")
    
    for idx, exp in enumerate(parsed_resume.experience, 1):
        with st.expander(f"**{exp.position}** at **{exp.company}** ({exp.duration})", expanded=(idx==1)):
            
            st.markdown(f"**Duration:** {exp.duration}")
            st.markdown(f"**Company:** {exp.company}")
            st.markdown(f"**Position:** {exp.position}")
            
            if exp.description:
                st.markdown("**Key Responsibilities:**")
                for desc in exp.description:
                    st.markdown(f"- {desc}")


def render_education_section(parsed_resume):
    """Display education information."""
    if not parsed_resume or not parsed_resume.education:
        return
    
    st.header("🎓 Education")
    
    for edu in parsed_resume.education:
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"**{edu.institution}**")
        
        with col2:
            degree_text = edu.degree
            if edu.field:
                degree_text += f", {edu.field}"
            st.markdown(degree_text)
        
        with col3:
            if edu.graduation_year:
                st.markdown(f"**{edu.graduation_year}**")
        
