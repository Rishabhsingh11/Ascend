# 🚀 Ascend - AI-Powered Resume Analysis & Job Matching Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50.0-FF4B4B.svg)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.27-green.svg)](https://langchain.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-1%20Complete-success.svg)](https://github.com/Rishabhsingh11/Ascend)

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
Ascend/
├── src/ # Source code
│ ├── UI/ # Streamlit UI components
│ │ ├── components/ # Reusable UI components
│ │ │ ├── init.py
│ │ │ ├── cache_viewer.py # Cache statistics UI
│ │ │ ├── results.py # Results display
│ │ │ ├── sidebar.py # Navigation sidebar
│ │ │ └── upload.py # Upload handlers
│ │ ├── styles/
│ │ │ └── custom.css # Custom styling
│ │ ├── app.py # Main Streamlit app
│ │ └── streaming_utils.py # Streaming helpers
│ │
│ ├── agent.py # LangGraph agent orchestration
│ ├── callbacks.py # LLM streaming callbacks
│ ├── config.py # Configuration management
│ ├── document_store.py # SQLite cache layer
│ ├── enhanced_resume_parser.py # PDFPlumber-based parser
│ ├── google_drive_handler.py # Google Drive integration
│ ├── logger.py # Custom logging
│ ├── resume_parser.py # Text extraction
│ ├── state.py # Pydantic state models
│ └── utils.py # Helper functions
│
├── tests/ # Test suite
│ ├── init.py
│ ├── compare_files.py
│ ├── debug_script.py
│ ├── streamlit_streaming_demo.py
│ ├── test_agent.py
│ ├── test_google_drive.py
│ ├── test_ollama_integration.py
│ ├── test_parser.py
│ └── test_resume_parser.py
│
├── db/ # SQLite database
│ └── resume_cache.db # Cached resume analyses
│
├── logs/ # Application logs
│ └── agent_run_YYYYMMDD_HHMMSS.log
│
├── credentials/ # Google Cloud credentials
│ └── credentials.json # (not in git)
│
├── temp_resumes/ # Temporary file storage
│
├── .env # Environment variables (not in git)
├── .gitignore # Git ignore rules
├── main.py # CLI entry point
├── streamlit_app.py # Streamlit entry point
├── requirements.txt # Python dependencies
└── README.md # This file
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


**Cache Benefits:**
- **Speed**: 157x faster for cached resumes (5s vs 14 min)
- **Cost**: Saves LLM compute time and resources
- **Consistency**: Identical resumes always get identical results

---

## 📊 Performance

### Benchmarks

| Metric | Cache HIT | Cache MISS |
|--------|-----------|------------|
| **Resume Parsing** | 0.5s | 1-2s |
| **Hash Computation** | 0.3s | 0.3s |
| **Cache Lookup** | 0.2s | 0.2s |
| **Job Role Analysis** | Simulated (1.5s) | Real LLM (5-7 min) |
| **Summary Generation** | Simulated (1.5s) | Real LLM (7-9 min) |
| **Total Time** | **~5 seconds** ⚡ | **12-16 minutes** 🐢 |
| **Speedup** | **157x faster** | Baseline |

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

### 🚧 Phase 2A (In Progress)
- [ ] **Skills Gap Analysis**: Compare resume skills vs job description requirements
- [ ] **Job Board Integration**: Live job search via LinkedIn/Indeed APIs
- [ ] **ATS Optimization**: Detect ATS-unfriendly elements (multi-column, tables, graphics)
- [ ] **Keyword Extraction**: Identify missing keywords from target job descriptions

### 📅 Phase 2B (Planned)
- [ ] **Cover Letter Generation**: AI-generated personalized cover letters
- [ ] **Interview Prep**: Common questions + suggested answers based on resume
- [ ] **Resume Rewriting**: LLM-powered bullet point improvements
- [ ] **Multi-Language Support**: Parse and analyze non-English resumes

### 🔮 Phase 3 (Future)
- [ ] **Multi-Agent Architecture**: Parallel processing for faster analysis
- [ ] **Custom LLM Fine-Tuning**: Domain-specific resume analysis models
- [ ] **API Endpoints**: RESTful API for programmatic access
- [ ] **Chrome Extension**: Analyze resumes directly from LinkedIn profiles
- [ ] **Collaborative Features**: Team-based resume review workflows

