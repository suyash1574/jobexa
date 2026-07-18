# Implementation Plan: Jobexa Platform

**Branch**: `001-jobexa-platform` | **Date**: 2026-07-16 | **Spec**: [spec.md](file:///d:/Projects/Jobexa/specs/001-jobexa-platform/spec.md)

**Input**: Feature specification from `/specs/001-jobexa-platform/spec.md`

## Summary
Build the Jobexa AI career assistant platform containing a FastAPI backend, a multi-agent AI engine using NVIDIA NIM API, a Telegram Bot for opportunity capture, and a Web Dashboard for reviewing and approving applications.

## Technical Context

**Language/Version**: Python 3.11, JavaScript (ES6)

**Primary Dependencies**: FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, python-telegram-bot, Axios, Tailwind CSS

**Storage**: PostgreSQL (Neon/Supabase), Supabase Storage / S3 (for PDFs)

**Testing**: pytest (unit, contract, integration)

**Target Platform**: Render (backend API and Celery worker), Vercel (frontend), Supabase (database & file storage)

**Project Type**: Web Application & Telegram Bot

**Performance Goals**: API response time under 300ms p95 (excluding direct LLM calls), heavy parsing/matching delegated to background tasks.

**Constraints**: Uploaded file size limited to 5MB, JWT token authentication, secure OAuth connection.

**Scale/Scope**: Designed for personal use with database limits/quotas built-in for commercialization readiness.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Gate | Status | How Satisfied / Action taken |
| :--- | :--- | :--- |
| **I. Human-in-the-Loop Verification** | ✅ PASS | Email dispatch requires explicit user approval on the Web Dashboard. |
| **II. Specialized Modular Architecture**| ✅ PASS | Modular agents (planner, matching, email gen, review) using Pydantic payloads. |
| **III. Secure OAuth and Credentials** | ✅ PASS | JWT authentication for the dashboard. Secure database encryption for credentials. |
| **IV. Unified Backend & Real-Time Sync**| ✅ PASS | Bot and dashboard utilize the exact same FastAPI endpoints and database transactions. |
| **V. ATS-Oriented Personalization** | ✅ PASS | Custom matching analysis, ATS score output, and role-tailored draft generation. |
| **VI. Code Quality & Typing** | ✅ PASS | Mandatory Pydantic models for API request/response and inter-agent messages. |
| **VII. Comprehensive Testing** | ✅ PASS | Pytest suite covering unit, contract, and integration tests (including agent prompts).|
| **VIII. UX Consistency** | ✅ PASS | Synchronized application statuses and fail notifications on dashboard and bot. |
| **IX. Latency & Storage Limits** | ✅ PASS | Celery background worker for AI matching. PDF limit set to 5MB. |

## Project Structure

The project will use the Web Application layout separating the backend API and frontend assets:

```text
backend/
├── alembic/                      # Database migrations
├── src/
│   ├── main.py                   # FastAPI entrypoint
│   ├── config.py                 # Environment configurations
│   ├── models/                   # SQLAlchemy database models
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── resume.py
│   │   └── application.py
│   ├── schemas/                  # Pydantic schemas for API validation
│   │   ├── user.py
│   │   ├── resume.py
│   │   └── application.py
│   ├── api/                      # Router & controllers
│   │   ├── auth.py
│   │   ├── documents.py
│   │   └── drafts.py
│   ├── agents/                   # NVIDIA NIM agent classes
│   │   ├── base.py
│   │   ├── planner.py
│   │   ├── matcher.py
│   │   └── writer.py
│   └── services/                 # Email and file storage service integrations
│       ├── storage.py
│       └── email.py
├── tests/                        # Pytest test directory
│   ├── unit/
│   ├── contract/
│   └── integration/
└── bot.py                        # Telegram Bot entrypoint

frontend/
├── index.html                    # Dashboard main HTML
├── css/
│   └── style.css                 # Custom CSS
└── js/
    ├── app.js                    # Main dashboard scripts
    ├── api.js                    # Axios client
    └── auth.js                   # Authentication & pairing scripts
```

**Structure Decision**: Option 2 (Web application layout) is selected to cleanly separate the FastAPI/Celery backend from the static Vercel dashboard.

## Complexity Tracking

*No principles were violated. Complexity metrics remain within limits.*
