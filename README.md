# 🚀 Ascend - AI-Powered Resume Analysis & Job Matching Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50.0-FF4B4B.svg)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.27-green.svg)](https://langchain.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-3%20Complete-success.svg)](https://github.com/Rishabhsingh11/Ascend)

> **Transform your resume into career opportunities with AI-powered analysis, intelligent job matching, and actionable improvement suggestions.**

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Live Demo](#-live-demo)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Performance](#-performance)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## 🎯 Overview

**Ascend** is an end-to-end AI Job Search Agent that helps job seekers optimize their resumes, identify matching career opportunities, and receive expert-level feedback, all powered by local LLMs and intelligent caching.

### What Makes Ascend Different?

✅ **Privacy-First**: Runs locally with Ollama (no data sent to cloud)  
✅ **Lightning Fast**: Intelligent caching provides instant results for analyzed resumes  
✅ **Dual Interface**: Both CLI and beautiful Streamlit web UI  
✅ **Production-Ready**: Hash-based deduplication, error handling, comprehensive logging  
✅ **Real-Time Streaming**: Watch AI analyze your resume in real-time  
✅ **End-to-End Solution**: Resume analysis → Job search → Skill gap → Email delivery  
✅ **Multi-API Job Search**: Aggregates from Adzuna, JSearch, and Jooble  
✅ **Automated Email Delivery**: Professional HTML emails with CSV attachments  
✅ **Market Readiness Score**: Know exactly how job-ready you are (0-100%)

---

## ✨ Key Features

### 🤖 AI-Powered Analysis
- **Resume Parsing**: Extracts contact info, skills, experience, education from PDF/DOCX using advanced PDFPlumber parsing
- **Job Role Matching**: Identifies top 3 job roles with confidence scores (0-100%) based on experience, skills, and career trajectory
- **Quality Assessment**: Provides overall resume quality score (0-10), grammatical issue detection, and improvement suggestions
- **Smart Recommendations**: AI-generated actionable advice to strengthen your resume

### 📂 Flexible Upload Options
- **Local Upload**: Drag-and-drop PDF/DOCX files directly
- **Google Drive Integration**: Connect and analyze resumes from your Google Drive folder

### ⚡ Performance & UX
- **Intelligent Caching**: Hash-based deduplication—analyzed resumes load in ~5 seconds instead of 15 minutes
- **Real-Time Streaming**: Watch LLM tokens appear live in the UI (ChatGPT-like experience)
- **Progress Indicators**: Clear visual feedback during long-running operations
- **Cache Statistics**: Dashboard showing cache hits, database size, and time saved

### 🎨 User Interface
- **Streamlit Web App**: Clean, modern interface with collapsible sections and progress tracking
- **CLI Tool**: Terminal-based interface for automation and scripting
- **Responsive Design**: Works on desktop, tablet, and mobile browsers

### 💼 Job Search & Skill Gap Analysis (Phase 2)
- **Multi-API Job Search**: Fetches jobs from Adzuna, JSearch, and Jooble simultaneously
- **Skill Extraction**: Automatically identifies required skills from job descriptions
- **Market Readiness Score**: Calculates your job-readiness percentage (0-100%)
- **Skill Gap Analysis**: Identifies missing skills with learning recommendations
- **Action Plans**: Immediate, 1-month, 3-month, and 6-month learning roadmaps
- **Job History Database**: SQLite storage of all job searches and analyses

### 📧 CSV Export & Email Integration (Phase 3)
- **Automated CSV Generation**: Clean job recommendations file with status tracking
- **Email Delivery**: Professional HTML emails with market readiness metrics
- **Gmail SMTP Support**: Secure app password authentication
- **Status Tracking**: Built-in column to track application progress
- **Database Management UI**: View cache and job history statistics
- **Automatic Cleanup**: Configurable cleanup for logs (24h) and exports (keep 5 latest)

---

### Design Principles

1. **Separation of Concerns**: Rule-based parsing (fast, deterministic) separated from LLM analysis (slow, intelligent)
2. **Cache-First Strategy**: Hash-based caching prevents redundant LLM calls (157x speedup for cached resumes)
3. **Streaming Architecture**: Real-time token streaming provides immediate user feedback
4. **Stateful Workflow**: LangGraph manages state transitions through 4-node pipeline
5. **Error Resilience**: Each node returns error states without crashing the entire pipeline

---

## 🛠️ Tech Stack

### Frontend
- **Streamlit 1.50.0** - Modern web UI framework
- **streamlit-option-menu** - Enhanced navigation components

### AI & LLM
- **Ollama** - Local LLM runtime (privacy-first)
- **Mistral** - High-performance language model
- **LangChain 0.3.27** - LLM orchestration framework
- **LangGraph 0.6.8** - Stateful agent workflow management
- **LangSmith** - LLM observability and debugging

### Parsing & Data Processing
- **PDFPlumber 0.11.7** - Advanced PDF parsing with layout awareness
- **PyPDF2 3.0.1** - PDF text extraction
- **pdfminer.six** - Low-level PDF processing
- **python-docx 1.2.0** - Microsoft Word document parsing
- **Pydantic 2.12.0** - Data validation and structured outputs

### Storage & Caching
- **SQLite 3** - Embedded database for resume cache
- **SQLAlchemy 2.0.43** - ORM for database operations

### Cloud Integration
- **Google Drive API** - Resume upload from Google Drive
- **google-auth** - OAuth2 authentication

### Development
- **Python 3.10+** - Core language
- **pytest** - Unit testing framework
- **python-dotenv** - Environment configuration

### Job Search APIs
- **Adzuna API** - UK-based job search aggregator
- **JSearch (RapidAPI)** - Global job search with 20M+ listings
- **Jooble API** - International job board integration

### Email & Export
- **SMTP (Gmail)** - Email delivery with app passwords
- **CSV** - Job recommendations export
- **HTML Email Templates** - Professional email formatting

### Additional Storage
- **Job History Database** - SQLite storage for job searches
- **Skill Gap Tracking** - Historical market readiness data


---

## 📦 Installation

### Prerequisites

1. **Python 3.10 or higher**
- `python --version`

2. **Ollama** (for local LLM)
- Download from [ollama.com](https://ollama.com)
- Install and start the service
- `ollama pull mistral`
- `ollama serve`


3. **Google Cloud Credentials** (optional, for Google Drive integration)
- Create project at [Google Cloud Console](https://console.cloud.google.com)
- Enable Google Drive API
- Download `credentials.json` and place in `credentials/` folder


### Create Virtual Environment

# Windows
`python -m venv .pyascend`

`.pyascend\Scripts\activate`

# macOS/Linux
`python3 -m venv .pyascend`

`source .pyascend/bin/activate`


### Install Dependencies

`pip install -r requirements.txt`


### Environment Setup

Create `.env` file in project root:

Ollama Configuration
- OLLAMA_MODEL=mistral
- OLLAMA_BASE_URL=http://localhost:11434
- TEMPERATURE=0.7

Google Drive Configuration (optional)
- GOOGLE_CREDENTIALS_PATH=credentials/credentials.json
- GOOGLE_DRIVE_FOLDER_NAME=Resumes

Logging
- LOG_LEVEL=INFO

Email Configuration (for job recommendations delivery)
- SMTP_SERVER=smtp.gmail.com
- SMTP_PORT=587
- SENDER_EMAIL=your-email@gmail.com
- SENDER_PASSWORD=your-app-password `Generate at: https://myaccount.google.com/apppasswords`

Job Search Configuration
- DEFAULT_COUNTRY=us
- MAX_JOBS_PER_ROLE=20
- DEFAULT_POSTING_HOURS=24

API Keys (optional - has free tiers)
- ADZUNA_APP_ID=your-adzuna-id
- ADZUNA_APP_KEY=your-adzuna-key
- JSEARCH_API_KEY=your-rapidapi-key
- JOOBLE_API_KEY=your-jooble-key



### Create Required Directories

Windows

- `mkdir db logs credentials temp_resumes`

macOS/Linux

- `mkdir -p db logs credentials temp_resumes`


---

## 🚀 Quick Start

### 1. Start Ollama

In a separate terminal

- `ollama serve`

### 2. Run Streamlit App (Recommended)

- `streamlit run streamlit_app.py`


The app will open in your browser at `http://localhost:8501`

### 3. Or Use CLI

`python main.py`


### 4. Upload & Analyze Resume

**Via Streamlit:**
1. Go to "📤 Upload Resume" tab
2. Choose upload method:
   - **Local File**: Drag-and-drop PDF/DOCX
   - **Google Drive**: Connect and select from folder
3. Click "🚀 Analyze Resume"
4. View results in "📊 Analysis Results" tab

**Via CLI:**
- Follow interactive prompts to select resume from Google Drive folder

## 📧 Email Setup Guide

To receive job recommendations via email, you need to set up Gmail app passwords:

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "How you sign in to Google", enable **2-Step Verification**

### Step 2: Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select **Mail** and **Other (Custom name)**
3. Enter "Ascend Job App"
4. Click **Generate**
5. Copy the 16-character password (remove spaces)

### Step 3: Update `.env`

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=abcdefghijklmnop # Paste 16-char app password here
```

### Email Features
- 📊 Market readiness percentage with color coding
- 📋 Job count and summary
- 📎 CSV attachment with all job details
- 📅 Next steps and action items
- 🎨 Professional HTML formatting

---

## 📚 Usage Guide

### Streamlit Web Interface

#### 1. Upload Resume Tab
```📤 Upload Resume
├─ 📁 Upload Local File
│ └─ Drag-and-drop PDF/DOCX
│
└─ ☁️ From Google Drive
├─ Connect to Google Drive
├─ Select resume from folder
└─ Download & Analyze
```


#### 2. Analysis Results Tab
```
📊 Analysis Results
├─ 📄 Resume Parsing
│ ├─ Contact Information
│ ├─ Skills (count)
│ ├─ Experience (count)
│ └─ Education (count)
│
├─ 🎯 Job Role Analysis
│ ├─ Role 1: Title + Confidence + Reasoning
│ ├─ Role 2: Title + Confidence + Reasoning
│ └─ Role 3: Title + Confidence + Reasoning
│
└─ 📊 Quality Assessment
├─ Quality Score (0-10)
├─ Overall Summary
├─ Years of Experience
├─ Key Strengths
├─ Grammatical Issues
└─ Improvement Suggestions
```

---

## 📁 Project Structure

```
db/
    ├── job_history_test.db
    ├── job_history.db
    └── resume_cache.db
src/
    ├── api/
        ├── __init__.py
        ├── adzuna_client.py
        ├── job_api_client.py
        ├── jooble_client.py
        └── jsearch_client.py
    ├── jobs/
        └── job_store.py
    ├── skills/
        ├── __init__.py
        ├── skill_comparator.py
        ├── skill_extractor.py
        └── skill_gap_analyzer.py
    ├── UI/
        ├── components/
            ├── __inti__.py
            ├── cache_viewer.py
            ├── results.py
            ├── sidebar.py
            ├── skill_gap_viewer.py
            └── upload.py
        ├── styles/
            └── custom.css
        ├── app.py
        └── streaming_utils.py
    ├── __init__.py
    ├── agent.py
    ├── callbacks.py
    ├── cleanup.py
    ├── config.py
    ├── csv_job_exporter.py
    ├── document_store.py
    ├── email_sender.py
    ├── enhanced_resume_parser.py
    ├── google_drive_handler.py
    ├── logger.py
    ├── resume_parser.py
    ├── state.py
    └── utils.py
tests/
    ├── __init__.py
    ├── cleanup_service_account.py
    ├── compare_files.py
    ├── debug_script.py
    ├── get_folder_id.py
    ├── streamlit_streaming_demo.py
    ├── test_agent.py
    ├── test_api_clients.py
    ├── test_csv_exporter.py
    ├── test_email_sender.py
    ├── test_google_drive.py
    ├── test_google_sheets.py
    ├── test_job_store.py
    ├── test_ollama_integration.py
    ├── test_parser.py
    ├── test_resume_parser.py
    └── test_skill_gap.py
.gitignore
main.py
output_result.json
README.md
requirements.txt
streamlit_app.py
```


---

## ⚙️ How It Works

### 1. Resume Parsing Flow

```
PDF/DOCX File
│
▼
EnhancedResumeParser (PDFPlumber)
├─ Character-level layout analysis
├─ Font size & boldness detection
├─ Section classification
│ ├─ Contact Info (name, email, phone, LinkedIn)
│ ├─ Skills (keyword extraction)
│ ├─ Experience (company, position, dates, bullets)
│ ├─ Education (institution, degree, field, year)
│ ├─ Projects
│ └─ Certifications
│
▼
Pydantic Validation
│
▼
ParsedResume Object
```


### 2. LangGraph Workflow

```
Initial State
│
▼
┌──────────────────┐
│ download_resume │ Downloads from Google Drive
└────────┬─────────┘ Extracts raw text
│
▼
┌──────────────────┐
│ parse_resume │ PDFPlumber parsing
└────────┬─────────┘ Structured Pydantic models
│
▼
┌──────────────────┐
│ analyze_job_roles│ LLM generates top 3 roles
└────────┬─────────┘ Confidence scores + reasoning
│
▼
┌──────────────────┐
│ generate_summary │ Quality assessment
└────────┬─────────┘ Improvement suggestions
│
▼
Final State
(Complete Results)
```


### 3. Caching Strategy

```
Resume Upload
│
▼
Compute SHA-256 Hash
│
├──────────────┬──────────────┐
│ │ │
▼ ▼ ▼
Cache HIT Cache MISS Cache MISS
(same file) (new file) (edited file)
│ │ │
▼ ▼ ▼
Load from Run Full Run Full
SQLite Pipeline Pipeline
│ │ │
├──────────────┴──────────────┤
│ │
▼ ▼
Display with Save to Cache
Simulated │
Streaming │
(~5 sec) │
▼
Next upload
will be cached
```

### 4. Phase 2: Job Search & Skill Gap Analysis

```
Job Role Matches
│
▼
┌──────────────────────┐
│ fetch_job_postings │ Searches Adzuna, JSearch, Jooble
└──────────┬───────────┘ Aggregates ~20 jobs per role
│
▼
┌──────────────────────┐
│ save_to_database │ Stores jobs in SQLite
└──────────┬───────────┘ Creates search session
│
▼
┌──────────────────────┐
│ analyze_skill_gaps │ Extracts skills from job descriptions
└──────────┬───────────┘ Compares with resume skills
│ Calculates market readiness (0-100%)
│ Generates learning roadmap
▼
Skill Gap Analysis
(Market Readiness Score)
```

### 5. Phase 3: Export & Email Delivery

```
Skill Gap Analysis
│
▼
┌──────────────────────┐
│ create_csv │ Generates clean CSV
└──────────┬───────────┘ Job recommendations with:
│ - Title, Company, Location
│ - Salary, Posted Date
│ - Status (Not Applied)
│ - Notes (empty)
│
▼
┌──────────────────────┐
│ send_email │ Professional HTML email
└──────────┬───────────┘ - Market readiness %
│ - Job count
│ - Next steps
│ - CSV attachment
│
▼
┌──────────────────────┐
│ cleanup │ Delete old logs (>24h)
└──────────────────────┘ Keep latest 5 exports
```





**Cache Benefits:**
- **Speed**: 157x faster for cached resumes (5s vs 14 min)
- **Cost**: Saves LLM compute time and resources
- **Consistency**: Identical resumes always get identical results

---

## 📊 Performance

### Benchmarks

| Metric | Cache HIT | Cache MISS (Phase 1 Only) | Full Pipeline (Phase 1-3) |
|--------|-----------|----------------------------|---------------------------|
| **Resume Parsing** | 0.5s | 1-2s | 1-2s |
| **Hash Computation** | 0.3s | 0.3s | 0.3s |
| **Cache Lookup** | 0.2s | 0.2s | 0.2s |
| **Job Role Analysis** | Simulated (1.5s) | Real LLM (5-7 min) | Real LLM (5-7 min) |
| **Summary Generation** | Simulated (1.5s) | Real LLM (7-9 min) | Real LLM (7-9 min) |
| **Job Search (3 roles)** | N/A | N/A | 5-10s (API calls) |
| **Skill Gap Analysis** | N/A | N/A | 2-3s |
| **CSV & Email** | N/A | N/A | 1-2s |
| **Total Time** | **~5 seconds** ⚡ | **12-16 minutes** 🐢 | **13-18 minutes** 🚀 |
| **Jobs Found** | 0 | 0 | ~60 jobs |
| **Market Readiness** | N/A | N/A | Calculated (0-100%) |
---

## 🗺️ Roadmap

### ✅ Phase 1 (Complete)
- [x] Resume parsing (PDF/DOCX)
- [x] LLM-based job role matching
- [x] Quality assessment & suggestions
- [x] Google Drive integration
- [x] Intelligent caching (hash-based deduplication)
- [x] Real-time LLM streaming
- [x] Dual interfaces (CLI + Streamlit)
- [x] Comprehensive logging

### ✅ Phase 2 (Complete)
- [x] **Multi-API Job Search**: Adzuna, JSearch, Jooble integration
- [x] **Skills Gap Analysis**: Compare resume vs job requirements
- [x] **Market Readiness Score**: Calculate job-readiness percentage
- [x] **Learning Roadmap**: Immediate, 1-month, 3-month, 6-month plans
- [x] **Job History Database**: SQLite storage with session tracking

### ✅ Phase 3 (Complete)
- [x] **CSV Export**: Clean job recommendations with status tracking
- [x] **Email Integration**: Gmail SMTP with HTML templates
- [x] **Market Readiness in Email**: Display percentage in email
- [x] **Database Manager UI**: View cache and job history
- [x] **Automatic Cleanup**: Configurable log and export cleanup
- [x] **Email Validation**: Robust extraction from pipe-separated contact info

### 🚧 Phase 4 (In Progress)
- [ ] **ATS Optimization**: Detect ATS-unfriendly elements (multi-column, tables, graphics)
- [ ] **Keyword Extraction**: Identify missing keywords from target job descriptions
- [ ] **Resume Comparison**: Side-by-side before/after analysis


