# 🤖 Jobexa — AI-Powered Job Application Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Telegram](https://img.shields.io/badge/Telegram_Bot-Interactive-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![Pytest](https://img.shields.io/badge/Tests-14%2F14_Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)

**Jobexa** is an end-to-end AI career platform that automates job opportunity collection, ATS resume matching, cold email personalization, dynamic PDF resume generation, Gmail dispatching, duplicate prevention, and recruiter response tracking — accessible via a Web Dashboard and an interactive Telegram Bot.

---

## 🌟 Key Features

### 🎯 1. Job Analysis & AI Extraction
- **Multi-Format Ingestion**: Process raw job descriptions, job posting URLs, PDF job specs, or job posting screenshots.
- **Deep Extraction**: Extracts company name, job title, required skills, preferred skills, recruiter contact email, experience level, application deadline, and estimated salary range using LLM agents.

### 📄 2. Resume Tailoring & Dynamic PDF Compiler
- **ATS Match Scoring**: Calculates ATS compatibility, skill match, and experience match percentage scores for every job post.
- **Resume Optimizer Agent**: Identifies missing skills for a job and compiles targeted Markdown resume variants.
- **Dynamic PDF Compilation**: Uses Jinja2 HTML templates and WeasyPrint to dynamically compile Markdown resume sources into styled, professional PDF attachments.

### ✉️ 3. Gmail OAuth 2.0 Integration & Automated Dispatch
- **Per-User OAuth 2.0 Connection**: Each user connects their personal Gmail account via Google OAuth 2.0 consent flow.
- **Direct Dispatch**: Approved emails are sent directly through the user's connected Gmail address with PDF resume attachments.
- **Thread Tracking**: Attaches Google `threadId` to application records for tracking recruiter interactions.

### 🛡️ 4. Application Deduplication Guard
- **Fuzzy Matching Service**: Uses Levenshtein / Trigram distance matching on company names and job titles.
- **30-Day Window**: Blocks duplicate submissions to the same company and role within 30 days, alerting the user on Telegram and Dashboard.

### 🏢 5. Company Research & Personalization Agent
- **Deep Company Intelligence**: Gathers target company tech stacks, recent product launches, and news items.
- **30-Day Cache Eviction**: Caches company profiles in PostgreSQL for 30 days to avoid redundant research requests.
- **Email Weaving**: Weaves company research points into personalized cold email drafts.

### ⏰ 6. Automated Follow-up Engine
- **Follow-up Scheduling**: Schedules 5-day, 10-day, and 15-day follow-up email drafts upon primary email dispatch.
- **Recruiter Reply Auto-Cancellation**: Background worker polls Gmail API `threadId` updates. If a recruiter reply is detected, pending follow-ups are automatically cancelled and status updates to "Interview".

### 📱 7. Interactive Telegram Bot
- **Full 9-Command Bot**: Includes `/start`, `/help`, `/link <code>`, `/unlink`, `/status`, `/drafts`, `/history`, `/resumes`, and `/certificates`.
- **Inline Action Keyboards**: Review full draft details, approve/reject drafts, and disambiguate PDF uploads (Resume vs. Job Posting) directly within Telegram chat.

### 📊 8. Analytics Dashboard & Tracking
- **Metrics Overview**: Tracks total applications, monthly count, pending drafts, interviews, offers, rejections, response rates, weekly volume trends, and top in-demand skills.

---

## 🏗️ System Architecture

```mermaid
graph TD
    User Telegram Bot / Dashboard --> API Auth / Webhooks
    API Auth / Webhooks --> FastAPI Router
    FastAPI Router --> JobAnalysisAgent
    FastAPI Router --> ResumeMatchingAgent
    FastAPI Router --> EmailGenerationAgent
    FastAPI Router --> ResumeOptimizerAgent
    FastAPI Router --> CompanyResearchAgent
    
    JobAnalysisAgent --> PostgreSQL Database
    ResumeMatchingAgent --> PostgreSQL Database
    EmailGenerationAgent --> PostgreSQL Database
    
    FastAPI Router --> DeduplicatorService
    FastAPI Router --> PDFCompilerService
    FastAPI Router --> GmailSenderService
    
    PDFCompilerService --> Dynamic PDF Resume
    GmailSenderService --> Recruiter Email Inbox
    
    Background Tasks --> Thread Reply Poller
    Thread Reply Poller --> Gmail API
    Thread Reply Poller --> PostgreSQL Database
```

---

## 📁 Repository Structure

```
Jobexa/
├── backend/
│   ├── bot.py                        # Interactive Telegram Bot runner (9 commands + inline buttons)
│   ├── requirements.txt              # Backend dependencies (FastAPI, SQLAlchemy, PyPDF2, WeasyPrint, Google API)
│   ├── alembic/                      # Database migrations
│   ├── scripts/
│   │   └── verify_setup.py           # Environment verification & Google OAuth check script
│   ├── src/
│   │   ├── main.py                   # FastAPI Application Entrypoint
│   │   ├── config.py                 # Configuration & Environment Settings
│   │   ├── api/                      # REST API Endpoints
│   │   │   ├── auth.py               # User authentication, Telegram pairing & Gmail OAuth
│   │   │   ├── documents.py          # Resume & Certificate uploads, variant creation & compilation
│   │   │   ├── drafts.py             # Application drafts management & approval
│   │   │   ├── analytics.py          # Dashboard aggregate statistics & history
│   │   │   └── webhooks.py           # Telegram bot webhooks
│   │   ├── models/                   # SQLAlchemy ORM Models
│   │   │   ├── user.py               # User model (auth & Gmail OAuth tokens)
│   │   │   ├── resume.py             # Resume variants & certificates models
│   │   │   └── application.py        # JobOpportunity, ApplicationDraft, ApplicationRecord, FollowUpSchedule, CompanyProfile
│   │   ├── services/                 # Core Business Logic Services
│   │   │   ├── gmail_sender.py       # Gmail API OAuth email client
│   │   │   ├── pdf_compiler.py       # Markdown-to-PDF dynamic compiler
│   │   │   ├── deduplicator.py       # Fuzzy matching duplicate guard
│   │   │   ├── storage.py            # Storage manager (Supabase / Local fallback)
│   │   │   └── tasks.py              # Background task runner & Gmail thread reply poller
│   │   └── agents/                   # LLM & Heuristic AI Agents
│   │       ├── planner.py            # JobAnalysisAgent
│   │       ├── matcher.py            # ResumeMatchingAgent
│   │       ├── writer.py             # EmailGenerationAgent
│   │       ├── optimizer.py          # ResumeOptimizerAgent
│   │       └── company_research.py   # CompanyResearchAgent
│   └── tests/                        # Automated Pytest Suite (14 Tests)
│       ├── contract/                 # API contract tests (documents, drafts)
│       ├── integration/              # Integration tests (agent workflow, delivery, quickstart, deduplication)
│       └── unit/                     # Unit tests (analytics, parser, optimizer)
├── frontend/                         # Modern Responsive Web Dashboard
│   ├── index.html                    # Single Page Dashboard UI
│   ├── css/                          # Custom Vanilla CSS Design System
│   └── js/                           # Axios REST API Client & Dashboard Logic
└── specs/                            # Design & Technical Specifications
    └── 002-autoapply-ai-platform/    # Spec-kit specification, plan, tasks, and checklists
```

---

## 🗄️ Database Data Model

```mermaid
erDiagram
    USERS ||--o{ RESUMES : owns
    USERS ||--o{ CERTIFICATES : owns
    USERS ||--o{ APPLICATION_DRAFTS : has
    USERS ||--o{ APPLICATION_RECORDS : completes
    JOB_OPPORTUNITIES ||--o{ APPLICATION_DRAFTS : generates
    APPLICATION_DRAFTS }|--|| RESUMES : selects
    APPLICATION_RECORDS ||--o{ FOLLOW_UP_SCHEDULES : schedules

    USERS {
        uuid id PK
        string email
        string telegram_chat_id
        string telegram_pairing_token
        string gmail_access_token
        string gmail_refresh_token
    }

    RESUMES {
        uuid id PK
        uuid user_id FK
        string filename
        string file_url
        string role_tag
        text markdown_content
        boolean is_default
    }

    JOB_OPPORTUNITIES {
        uuid id PK
        string company_name
        string job_title
        json required_skills
        string recruiter_email
    }

    APPLICATION_DRAFTS {
        uuid id PK
        uuid user_id FK
        uuid job_opportunity_id FK
        uuid selected_resume_id FK
        string email_subject
        text email_body
        int ats_compatibility_score
    }

    APPLICATION_RECORDS {
        uuid id PK
        uuid user_id FK
        string company_name
        string job_title
        string thread_id
        string status
    }
```

---

## 🛠️ Installation & Setup Guide

### 1. System Requirements
- **Python**: 3.11 or higher
- **PostgreSQL**: 14 or higher
- **Node.js**: (Optional, for running frontend dev tools)

---

### 2. Environment Configuration

Create a `.env` file inside the `backend/` directory:

```env
# Application Secrets
JWT_SECRET_KEY=supersecretkeychangeinproduction
ACCESS_TOKEN_EXPIRE_MINUTES=10080
ENCRYPTION_SECRET_KEY=yoursecretencryptionkey32byteslong

# Database Connection URL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobexa

# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

# Google OAuth 2.0 Credentials (for Gmail API dispatch)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/gmail/callback

# NVIDIA NIM / LLM API Key
NVIDIA_NIM_API_KEY=YOUR_NVIDIA_NIM_API_KEY

# Storage Credentials (Supabase / Local Fallback)
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=your-supabase-key
SUPABASE_BUCKET=jobexa-documents

# Fallback SMTP Email Dispatch Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_sending_gmail@gmail.com
SMTP_PASSWORD=your_app_password
```

---

### 3. Backend Setup & Local Run

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\activate

# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify environment and OAuth configuration
python scripts/verify_setup.py

# 5. Run database migrations
alembic upgrade head

# 6. Start the FastAPI API Server
uvicorn src.main:app --reload --port 8000
```

---

### 4. Running the Telegram Bot

In a separate terminal window:

```bash
cd backend
.venv\Scripts\activate
python bot.py
```

---

### 5. Running the Web Dashboard Frontend

Simply serve the `frontend/` directory using any local static file server:

```bash
# Using Python built-in HTTP server:
python -m http.server 3000 --directory frontend

# Or using npx serve:
npx serve frontend -p 3000
```

Open your browser at `http://localhost:3000` to interact with the Jobexa Dashboard.

---

## 📱 Telegram Bot Command Reference

| Command | Description |
|---|---|
| `/start` | Displays interactive welcome card with quick-action inline buttons |
| `/help` | Complete bot command reference guide |
| `/link <code>` | Pair Telegram chat ID with your Jobexa web account |
| `/unlink` | Unlink your Telegram account |
| `/status` | View aggregate application stats & response rates |
| `/drafts` | List pending application drafts with **View**, **Approve**, and **Reject** buttons |
| `/history` | View historical sent application records |
| `/resumes` | List uploaded resumes with role tags & default indicator |
| `/certificates` | List uploaded certificates & credentials |

---

## 🧪 Automated Testing & Verification

Jobexa includes a complete suite of unit, contract, and integration tests using `pytest`.

To run the full test suite locally:

```bash
cd backend
$env:PYTHONPATH="."
.venv\Scripts\pytest tests --asyncio-mode=auto
```

### Test Results Breakdown (14/14 Passed)
- ✅ `tests/contract/test_documents.py` (3 passed)
- ✅ `tests/contract/test_drafts.py` (2 passed)
- ✅ `tests/integration/test_agent_workflow.py` (1 passed)
- ✅ `tests/integration/test_delivery.py` (1 passed)
- ✅ `tests/integration/test_quickstart.py` (3 passed)
- ✅ `tests/unit/test_analytics.py` (1 passed)
- ✅ `tests/unit/test_parser.py` (3 passed)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
