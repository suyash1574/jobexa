# Implementation Plan: Jobexa AutoApply AI Platform

**Branch**: `002-autoapply-ai-platform` | **Date**: 2026-07-17 | **Spec**: [spec.md](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/spec.md)

**Input**: Feature specification from `specs/002-autoapply-ai-platform/spec.md`

## Summary

The Jobexa AutoApply AI Platform is an AI-powered job application tool that automates job parsing, ATS compatibility matching, resume optimization, and cover letter generation, while sending applications via Gmail API OAuth 2.0 and scheduling follow-up reminders. In accordance with the Jobexa Constitution, every application and follow-up email requires human-in-the-loop approval before dispatch.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI, python-telegram-bot, sqlalchemy, alembic, PyPDF2, google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client, httpx, jinja2

**Storage**: PostgreSQL (Supabase/Neon) with SQLAlchemy ORM

**Testing**: pytest (unit, integration, and contract tests)

**Target Platform**: Render (Backend + Telegram Webhook Worker), Vercel (Frontend)

**Project Type**: web-service & Telegram bot

**Performance Goals**: <300ms p95 response time for web dashboard endpoints, background async processing for AI matching and PDF compilation.

**Constraints**: <200ms p95 latency for API queries, <5MB storage size per resume/certificate PDF file, SSL/TLS database connections.

**Scale/Scope**: Support 50 job postings/day per user, multi-tenant OAuth state management.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Human-in-the-Loop Verification**: PASS. Every draft and follow-up must be approved on the dashboard or Telegram before sending.
- **Specialized Modular Multi-Agent Architecture**: PASS. Implemented via specialized agents (Planner, Job Analysis, Matcher, Writer, Optimizer) with Pydantic contracts.
- **Secure OAuth and Encrypted Credential Management**: PASS. User-level Gmail OAuth 2.0 token storage and database encryption.
- **Unified Backend API**: PASS. Shared FastAPI backend for Telegram bot and web dashboard.
- **ATS-Oriented Personalization**: PASS. Resume matching scoring instead of generic copy-pasting.
- **Strict Latency and Storage Limits**: PASS. Asynchronous task execution for LLM matching and PDF generation, 5MB file upload limit.

## Project Structure

### Documentation (this feature)

```text
specs/002-autoapply-ai-platform/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 data model definitions
├── quickstart.md        # Phase 1 validation guide
└── contracts/           # Phase 1 API contracts
    ├── auth.json
    ├── drafts.json
    ├── resumes.json
    └── analytics.json
```

### Source Code Layout

```text
backend/
├── src/
│   ├── models/          # SQLAlchemy Database Models
│   ├── services/        # AI Agents, Google API Service, PDF Compiler
│   ├── api/             # FastAPI routers
│   ├── schemas/         # Pydantic validation schemas
│   └── config.py        # Configuration settings
└── tests/               # pytest suites

frontend/
├── index.html           # Main SPA
├── js/
│   ├── auth.js          # Supabase & Gmail OAuth handler
│   ├── app.js           # Dashboard controllers
│   └── bot.js           # Telegram link utilities
└── css/
    └── index.css        # Main stylesheet
```

**Structure Decision**: Multi-project layout (Option 2) matching existing `backend/` and `frontend/` directory structure.
