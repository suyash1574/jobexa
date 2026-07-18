# AutoApply AI Platform Verification & Quickstart Guide

This guide outlines the step-by-step verification flows to validate the new AutoApply AI Platform capabilities end-to-end.

## Prerequisites

1. PostgreSQL database running with updated tables (see [data-model.md](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/data-model.md)).
2. Google OAuth client credentials file (`client_secret.json`) placed in `backend/secrets/`.
3. Valid `TELEGRAM_BOT_TOKEN` set in environment configurations.

---

## Verification Flow 1: User Onboarding & Gmail OAuth Connection

This flow verifies that a user can successfully connect their personal Gmail account via OAuth 2.0.

1. **Start the API Server**:
   ```bash
   cd backend && python -m uvicorn src.main:app --reload --port 8000
   ```
2. **Access Authorization Endpoint**:
   Open a browser or API client and send a request to `GET /api/v1/auth/gmail/authorize` (see [auth.json](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/contracts/auth.json)).
3. **Verify Google Consent Screen**:
   Ensure you are redirected to the Google accounts page. Grant permissions for `gmail.send` and `gmail.readonly` scopes.
4. **Inspect Callback**:
   After logging in, you will be redirected to `/api/v1/auth/gmail/callback`. Verify that your database `users` record now has values for `gmail_access_token` and `gmail_refresh_token` (see [data-model.md](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/data-model.md)).

---

## Verification Flow 2: Multi-Agent Job Submission & Deduplication

This flow verifies that submitting a job posting triggers correct multi-agent processing, scores matching, and handles duplicates.

1. **Submit Job Posting (Initial)**:
   Send a job posting via the Telegram bot or the web dashboard.
2. **Verify Process Logs**:
   Confirm that the `JobAnalysisAgent`, `ResumeMatchingAgent`, and `EmailGenerationAgent` run sequentially in background threads.
3. **Verify Output Draft**:
   Query `GET /api/v1/drafts` and verify that a new `ApplicationDraft` is created with a non-zero ATS match score (see [drafts.json](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/contracts/drafts.json)).
4. **Submit Duplicate Job**:
   Submit the same job description or URL again within a 30-day window.
5. **Verify Duplicate Prevention**:
   Verify that the system returns a warning and prevents creating a duplicate draft (validated by [FR-009](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/spec.md#L155)).

---

## Verification Flow 3: App Draft Approval & Gmail API Dispatch

This flow verifies that approving a draft sends the email with dynamically compiled PDF variants and schedules follow-ups.

1. **Create Resume Variant**:
   Submit a Markdown resume variant via `POST /api/v1/documents/resumes/variants` (see [resumes.json](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/contracts/resumes.json)).
2. **Approve Application**:
   Send a request to `POST /api/v1/drafts/{id}/approve` (see [drafts.json](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/contracts/drafts.json)).
3. **Verify Email & Attachments**:
   Check the recipient's inbox. Ensure the email body is personalized, the subject is correct, and the attached PDF resume variant was dynamically compiled from the source Markdown (validated by [FR-015](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/spec.md#L161)).
4. **Verify Follow-up Schedule**:
   Query the database to confirm that 3 follow-up drafts are scheduled in `follow_up_schedules` (see [data-model.md](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/data-model.md)).

---

## Verification Flow 4: Recruiter Reply Tracking & Follow-up Cancellation

This flow verifies that recruiter responses automatically cancel scheduled follow-up notifications.

1. **Simulate Recruiter Reply**:
   Send a reply to the sent thread from the recruiter's email.
2. **Trigger Thread Verification Worker**:
   Run the thread polling task manually or wait for the cron schedule to run.
3. **Verify Cancellation**:
   Query the `follow_up_schedules` table for the thread. Verify that all pending follow-ups are now marked as `Cancelled` (validated by [FR-011](file:///d:/Projects/Jobexa/specs/002-autoapply-ai-platform/spec.md#L157)).
