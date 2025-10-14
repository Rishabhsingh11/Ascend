# tests/test_skill_gap.py
"""Test skill gap analysis"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.skills.skill_extractor import SkillExtractor
from src.skills.skill_comparator import SkillComparator
from src.skills.skill_gap_analyzer import SkillGapAnalyzer
from src.state import JobPosting

def test_skill_gap_analysis():
    """Test complete skill gap workflow"""
    
    # Initialize components
    extractor = SkillExtractor()
    comparator = SkillComparator()
    analyzer = SkillGapAnalyzer(extractor, comparator)
    
    # Mock resume data
    resume_skills = [
        "Python", "SQL", "Git", "JavaScript", "Excel", 
        "Data Analysis", "Problem Solving"
    ]
    
    # Mock job postings with detailed descriptions
    jobs = [
        JobPosting(
            title="Data Scientist",
            company="Tech Corp",
            location="New York, NY",
            description="""
            We are looking for a Data Scientist with strong analytical skills.
            
            Required Skills:
            - Python programming for data analysis
            - SQL for database queries
            - Machine Learning experience
            - TensorFlow or PyTorch
            - Statistical analysis
            - Data visualization with Tableau
            - Git version control
            - Strong communication skills
            
            Preferred:
            - AWS or Azure cloud experience
            - Docker containerization
            - Agile methodology
            """,
            required_skills=[],  # Will be auto-extracted
            url="https://example.com/job1",
            salary="$120,000 - $150,000",
            posted_date="2025-10-10",
            source="test"
        ),
        JobPosting(
            title="Senior Data Scientist",
            company="AI Labs",
            location="San Francisco, CA",
            description="""
            Senior Data Scientist position for ML team.
            
            Must Have:
            - Python (pandas, numpy, scikit-learn)
            - Machine Learning and Deep Learning
            - TensorFlow, PyTorch, or Keras
            - SQL and database design
            - Spark for big data processing
            - Git and CI/CD
            - Docker and Kubernetes
            
            Nice to Have:
            - NLP experience
            - AWS SageMaker
            - MLOps practices
            """,
            required_skills=[],
            url="https://example.com/job2",
            salary="$150,000 - $180,000",
            posted_date="2025-10-12",
            source="test"
        ),
        JobPosting(
            title="Software Engineer - Full Stack",
            company="Startup Inc",
            location="Remote",
            description="""
            Full Stack Software Engineer needed for fast-growing startup.
            
            Technical Requirements:
            - JavaScript/TypeScript
            - React.js or Vue.js frontend framework
            - Node.js backend development
            - Python for backend services
            - SQL and NoSQL databases (PostgreSQL, MongoDB)
            - Docker containerization
            - AWS cloud services (EC2, S3, Lambda)
            - Git version control
            - REST API design
            - Agile/Scrum methodology
            
            Bonus:
            - GraphQL experience
            - Kubernetes
            - CI/CD pipelines (Jenkins, GitHub Actions)
            """,
            required_skills=[],
            url="https://example.com/job3",
            salary="$130,000 - $160,000",
            posted_date="2025-10-13",
            source="test"
        ),
        JobPosting(
            title="Machine Learning Engineer",
            company="Data Corp",
            location="Boston, MA",
            description="""
            Machine Learning Engineer to build production ML systems.
            
            Required:
            - Python (TensorFlow, PyTorch, scikit-learn)
            - Machine Learning algorithms
            - Deep Learning and Neural Networks
            - SQL for data extraction
            - Docker and Kubernetes
            - Git version control
            - AWS or GCP cloud platforms
            - MLOps and model deployment
            - Problem solving and communication
            
            Preferred:
            - Spark for big data
            - Kafka for streaming
            - Terraform for infrastructure
            """,
            required_skills=[],
            url="https://example.com/job4",
            salary="$140,000 - $170,000",
            posted_date="2025-10-14",
            source="test"
        )
    ]
    
    # Job roles matching the jobs
    roles = ["Data Scientist", "Software Engineer", "Machine Learning Engineer"]
    
    print("\n" + "="*60)
    print("SKILL GAP ANALYSIS TEST")
    print("="*60)
    
    print(f"\n📋 Resume Skills ({len(resume_skills)}):")
    for skill in resume_skills:
        print(f"   • {skill}")
    
    print(f"\n💼 Analyzing {len(jobs)} job postings...")
    
    # Run analysis
    result = analyzer.analyze(resume_skills, jobs, roles)
    
    # Print detailed results
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)
    
    print(f"\n📊 Overall Market Readiness: {result.overall_market_readiness}%")
    print(f"📈 Total Jobs Analyzed: {result.total_jobs_analyzed}")
    print(f"📅 Analysis Date: {result.analysis_date}")
    
    print("\n🎯 Per-Role Analysis:")
    for role_analysis in result.role_analyses:
        print(f"\n   Role: {role_analysis.job_role}")
        print(f"   Match: {role_analysis.match_percentage}%")
        print(f"   Coverage Score: {role_analysis.skill_coverage_score}/10")
        print(f"   Readiness: {role_analysis.estimated_readiness}")
        print(f"   Matched Skills ({len(role_analysis.matched_skills)}): {', '.join(role_analysis.matched_skills[:5])}")
        print(f"   Missing Skills ({len(role_analysis.missing_skills)}): {', '.join([s.skill_name for s in role_analysis.missing_skills[:5]])}")
    
    print(f"\n🚨 Common Gaps Across All Roles ({len(result.common_gaps)}):")
    for gap in result.common_gaps[:5]:
        print(f"   • {gap}")
    
    print(f"\n⚡ Quick Wins ({len(result.quick_wins)}):")
    for skill in result.quick_wins[:5]:
        print(f"   • {skill}")
    
    print(f"\n🎓 Long-Term Goals ({len(result.long_term_goals)}):")
    for skill in result.long_term_goals[:5]:
        print(f"   • {skill}")
    
    print(f"\n📈 Trending Skills ({len(result.trending_skills)}):")
    for skill in result.trending_skills:
        print(f"   • {skill}")
    
    print("\n📋 Action Plans:")
    print("\n   Immediate (Next 2 Weeks):")
    for action in result.immediate_actions:
        print(f"      • {action}")
    
    print("\n   One Month Plan:")
    for action in result.one_month_plan[:3]:
        print(f"      • {action}")
    
    print("\n   Three Month Plan:")
    for action in result.three_month_plan[:3]:
        print(f"      • {action}")
    
    # Assertions
    assert result.total_jobs_analyzed == 4, f"Expected 4 jobs, got {result.total_jobs_analyzed}"
    assert len(result.role_analyses) > 0, "No role analyses generated"
    assert result.overall_market_readiness > 0, "Market readiness is 0"
    assert len(result.immediate_actions) > 0, "No immediate actions generated"
    
    # Additional assertions
    assert result.overall_market_readiness <= 100, "Market readiness exceeds 100%"
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60 + "\n")
    
    return result

if __name__ == "__main__":
    test_skill_gap_analysis()
