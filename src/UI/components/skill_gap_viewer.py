# src/UI/components/skill_gap_viewer.py
"""Skill Gap Analysis visualization component."""

import streamlit as st
from typing import Optional
from src.state import SkillGapAnalysis

def render_skill_gap_analysis(skill_gap: Optional[SkillGapAnalysis]):
    """
    Render comprehensive skill gap analysis visualization.
    
    Args:
        skill_gap: SkillGapAnalysis object from agent
    """
    if not skill_gap:
        st.info("🔍 No skill gap analysis available. Enable Phase 2 when analyzing resumes.")
        return
    
    st.markdown("---")
    st.header("🔍 Skill Gap Analysis")
    
    # ===== Overall Metrics =====
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Market Readiness",
            f"{skill_gap.overall_market_readiness}%",
            delta=f"{skill_gap.overall_market_readiness - 50:+.1f}% vs avg"
        )
    
    with col2:
        st.metric(
            "Jobs Analyzed",
            skill_gap.total_jobs_analyzed
        )
    
    with col3:
        st.metric(
            "Common Gaps",
            len(skill_gap.common_gaps),
            delta=f"-{len(skill_gap.common_gaps)} skills needed",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Quick Wins",
            len(skill_gap.quick_wins),
            delta=f"+{len(skill_gap.quick_wins)} easy skills",
            delta_color="normal"
        )
    
    st.markdown("---")
    
    # ===== Per-Role Analysis =====
    st.subheader("🎯 Role-Specific Analysis")
    
    for idx, role_analysis in enumerate(skill_gap.role_analyses, 1):
        with st.expander(f"**{idx}. {role_analysis.job_role}**", expanded=(idx == 1)):
            
            # Metrics row
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Match %", f"{role_analysis.match_percentage:.1f}%")
            
            with col2:
                st.metric("Coverage Score", f"{role_analysis.skill_coverage_score}/10")
            
            with col3:
                st.metric("Jobs Analyzed", role_analysis.jobs_analyzed)
            
            st.markdown(f"**Estimated Readiness:** {role_analysis.estimated_readiness}")
            
            # Progress bar for match percentage
            st.progress(role_analysis.match_percentage / 100)
            
            # Matched Skills
            if role_analysis.matched_skills:
                st.markdown("### ✅ Skills You Have")
                matched_cols = st.columns(min(len(role_analysis.matched_skills), 4))
                for i, skill in enumerate(role_analysis.matched_skills):
                    with matched_cols[i % 4]:
                        st.success(f"✓ {skill}")
            
            # Missing Skills
            if role_analysis.missing_skills:
                st.markdown("### 🚨 Skills to Develop")
                
                for gap in role_analysis.missing_skills[:10]:  # Top 10
                    priority_color = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(gap.priority, "⚪")
                    
                    st.markdown(f"""
                    {priority_color} **{gap.skill_name}** ({gap.category})
                    - Found in **{gap.found_in_jobs_count}** jobs
                    - Priority: **{gap.priority.upper()}**
                    - Learning Time: **{gap.estimated_learning_time}**
                    """)
            
            # Top Skills to Learn
            if role_analysis.top_skills_to_learn:
                st.markdown("### 🎓 Recommended Learning Priority")
                for i, skill in enumerate(role_analysis.top_skills_to_learn, 1):
                    st.markdown(f"{i}. **{skill}**")
    
    st.markdown("---")
    
    # ===== Cross-Role Insights =====
    st.subheader("🔗 Cross-Role Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚨 Common Gaps (High Priority)")
        st.markdown("*Skills missing across ALL your target roles*")
        
        if skill_gap.common_gaps:
            for idx, skill in enumerate(skill_gap.common_gaps[:8], 1):
                st.error(f"{idx}. {skill}")
        else:
            st.success("✅ No common gaps - you're well-rounded!")
    
    with col2:
        st.markdown("### ⚡ Quick Wins")
        st.markdown("*Easy-to-learn, high-impact skills*")
        
        if skill_gap.quick_wins:
            for idx, skill in enumerate(skill_gap.quick_wins[:8], 1):
                st.info(f"{idx}. {skill}")
        else:
            st.info("No quick wins identified")
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### 🎓 Long-Term Goals")
        st.markdown("*Complex skills requiring 3-6 months*")
        
        if skill_gap.long_term_goals:
            for idx, skill in enumerate(skill_gap.long_term_goals[:8], 1):
                st.warning(f"{idx}. {skill}")
        else:
            st.info("No long-term goals needed")
    
    with col4:
        st.markdown("### 🌟 Niche Skills")
        st.markdown("*Specialized skills for specific roles*")
        
        if skill_gap.niche_skills:
            for idx, skill in enumerate(skill_gap.niche_skills[:8], 1):
                st.markdown(f"{idx}. {skill}")
        else:
            st.info("No niche skills identified")
    
    st.markdown("---")
    
    # ===== Market Trends =====
    st.subheader("📈 Market Trends")
    
    col_trend1, col_trend2 = st.columns(2)
    
    with col_trend1:
        st.markdown("### 📈 Trending Skills")
        if skill_gap.trending_skills:
            for skill in skill_gap.trending_skills:
                st.markdown(f"🔥 **{skill}**")
        else:
            st.info("No trending skills data")
    
    with col_trend2:
        st.markdown("### 📉 Declining Skills")
        if skill_gap.declining_skills:
            for skill in skill_gap.declining_skills:
                st.markdown(f"📉 {skill}")
        else:
            st.success("✅ No declining skills in your profile")
    
    st.markdown("---")
    
    # ===== Action Plans =====
    st.subheader("📋 Your Learning Roadmap")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Immediate (2 weeks)",
        "📅 1 Month",
        "🎯 3 Months",
        "🚀 6 Months"
    ])
    
    with tab1:
        st.markdown("### Actions for Next 2 Weeks")
        if skill_gap.immediate_actions:
            for idx, action in enumerate(skill_gap.immediate_actions, 1):
                st.markdown(f"{idx}. {action}")
        else:
            st.info("No immediate actions")
    
    with tab2:
        st.markdown("### 1-Month Plan")
        if skill_gap.one_month_plan:
            for idx, action in enumerate(skill_gap.one_month_plan, 1):
                st.markdown(f"{idx}. {action}")
        else:
            st.info("No 1-month plan")
    
    with tab3:
        st.markdown("### 3-Month Plan")
        if skill_gap.three_month_plan:
            for idx, action in enumerate(skill_gap.three_month_plan, 1):
                st.markdown(f"{idx}. {action}")
        else:
            st.info("No 3-month plan")
    
    with tab4:
        st.markdown("### 6-Month Plan")
        if skill_gap.six_month_plan:
            for idx, action in enumerate(skill_gap.six_month_plan, 1):
                st.markdown(f"{idx}. {action}")
        else:
            st.info("No 6-month plan")
    
    st.markdown("---")
    st.caption(f"📅 Analysis performed on: {skill_gap.analysis_date}")
