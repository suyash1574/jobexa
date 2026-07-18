# Quickstart: Jobexa Platform Validation Guide

This guide details how to validate the end-to-end integration and functionality of the Jobexa platform components.

## Prerequisites

- Python 3.11+ installed.
- PostgreSQL database running (local or Neon/Supabase link).
- Redis server running (for background task execution).
- Node.js (optional, if frontend testing is automated).

---

## Validation Scenarios

### Scenario 1: Telegram to Web Dashboard User Pairing

**Goal**: Verify that a user can securely link their Telegram account using a pairing code.

1. **Setup**:
   - Run the FastAPI server: `uvicorn main:app --reload`
   - Run the Telegram bot script: `python bot.py`
2. **Steps**:
   - Log into the Web Dashboard at `http://localhost:8000`.
   - Go to Profile Settings and click "Generate Telegram Pairing Code". Note the 6-digit code (e.g., `123456`).
   - Open Telegram and message the bot: `/link 123456`.
3. **Expected Outcome**:
   - Telegram Bot responds: "✅ Accounts paired successfully!"
   - Web Dashboard Profile shows the Telegram Chat ID as "Linked".
   - Database check: `SELECT telegram_chat_id FROM users WHERE email='...'` yields the correct Telegram user ID.

---

### Scenario 2: Job Submission & AI Draft Generation

**Goal**: Verify that parsing, ATS scoring, and email generation succeed after submitting a job post.

1. **Setup**:
   - Ensure the database has at least one user with a default resume uploaded.
   - Run Celery worker: `celery -A tasks worker --loglevel=info`
2. **Steps**:
   - In Telegram, paste this message:
     ```
     Company: TechCorp
     Role: Backend Developer
     Requirements: Python, FastAPI, PostgreSQL, AWS
     Apply to: jobs@techcorp.com
     ```
3. **Expected Outcome**:
   - Bot replies: "🔍 Processing job description... This might take a moment."
   - After task completion, bot sends the review link: "✨ Tailored application draft created! ATS Match: XX% ..."
   - Database check: A new record is added in the `job_opportunities` and `application_drafts` tables linked to the user.

---

### Scenario 3: Draft Editing, Approval & Delivery Failure Alert

**Goal**: Verify that editing draft content works, and email delivery failures are propagated across all platforms.

1. **Setup**:
   - Intentionally configure incorrect SMTP/Gmail credentials in settings to trigger a failure.
2. **Steps**:
   - Open the Web Dashboard, go to Drafts, and click "Edit" on the TechCorp Backend Developer draft.
   - Modify the email subject to: "Application for Backend Developer - Edited".
   - Click "Save" then click "Approve & Send".
3. **Expected Outcome**:
   - Dashboard shows a red popup/toast alert: "Failed to send email. Credentials revoked or SMTP error."
   - Application status updates to `Failed` in the database.
   - Telegram Bot sends an asynchronous message to the user: "🚨 **Failed to send application!** ... Reason: Credential validation failed."

---

## Verification Commands

Run unit and integration tests to verify model parsing, endpoint routing, and state transitions:

```bash
# Run backend unit tests (Pydantic validation, database models)
pytest backend/tests/unit

# Run contract tests (API schemas)
pytest backend/tests/contract

# Run integration tests (Multi-agent orchestration and status synchronization)
pytest backend/tests/integration
```
