# Tasks: Jobexa AutoApply AI Platform

**Input**: Design documents from `/specs/002-autoapply-ai-platform/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included under each phase in accordance with the Jobexa Constitution's testing principles.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic dependencies configuration

- [x] T001 Configure new project dependencies (PyPDF2, google-api-python-client, google-auth-oauthlib, jinja2, weasyprint) in `backend/requirements.txt`
- [x] T002 Add Google OAuth client credentials configurations, secrets paths, and encrypt keys in `backend/src/config.py`
- [x] T003 [P] Configure environment setup script to automate OAuth client verification in `backend/scripts/verify_setup.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that must be complete before any user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create database schema migrations for new tables (`follow_up_schedules`, `company_profiles`) and table updates (`users`, `resumes`, `job_opportunities`, `application_drafts`, `application_records`) in `backend/src/models/`
- [x] T005 [P] Setup OAuth 2.0 routes for Gmail authorization (`/gmail/authorize` and `/gmail/callback`) in `backend/src/api/auth.py`
- [x] T006 [P] Implement dynamic PDF compiler service from Markdown using Jinja2 templates and Weasyprint in `backend/src/services/pdf_compiler.py`

---

## Phase 3: User Story 1 - Submit Job Posting for AI Processing (Priority: P1) 🎯 MVP

**Goal**: Extract job details and draft a matched application package

**Independent Test**: Send a job posting via Telegram or dashboard, check that an application draft with ATS match score is created in under 2 minutes.

### Tests for User Story 1
- [x] T007 [P] [US1] Unit test for PDF and image OCR extraction in `backend/tests/unit/test_parser.py`
- [x] T008 [P] [US1] Integration test for job analysis and matching tasks in `backend/tests/integration/test_agent_workflow.py`

### Implementation for User Story 1
- [x] T009 [P] [US1] Update `JobAnalysisAgent` in `backend/src/agents/planner.py` to extract experience level and salary range
- [x] T010 [US1] Update task orchestrator `process_job_submission_task` in `backend/src/services/tasks.py` to run matching against resume variants and save the matching variant to the draft
- [x] T011 [US1] Support job submission URLs and screenshots in the Telegram bot webhook endpoint in `backend/src/main.py`

---

## Phase 4: User Story 2 - Review, Edit, and Approve Applications (Priority: P1) 🎯 MVP

**Goal**: Review drafts on dashboard or Telegram, approve, and send them via Gmail API

**Independent Test**: Retrieve a draft, click approve, and verify that the recruiter receives the email with the dynamically compiled PDF resume variant.

### Tests for User Story 2
- [x] T012 [P] [US2] Contract test for draft approval endpoints in `backend/tests/contract/test_drafts.py`
- [x] T013 [P] [US2] Integration test for Gmail API token exchange in `backend/tests/integration/test_gmail_auth.py`

### Implementation for User Story 2
- [x] T014 [P] [US2] Implement Gmail API sending client supporting PDF attachments in `backend/src/services/gmail_sender.py`
- [x] T015 [US2] Update draft approval endpoint `/api/v1/drafts/{id}/approve` in `backend/src/api/drafts.py` to compile the PDF resume variant, send the mail, delete the draft, and write to application records

---

## Phase 5: User Story 3 - Job Collection and Deduplication (Priority: P2)

**Goal**: Prevent duplicate job applications to the same company for the same role within 30 days

**Independent Test**: Submit a job opportunity from the same company and role twice, verify that the second submission returns a duplicate warning and creates no draft.

### Tests for User Story 3
- [x] T016 [P] [US3] Integration test for fuzzy matching duplicate detection in `backend/tests/integration/test_deduplication.py`

### Implementation for User Story 3
- [x] T017 [US3] Implement fuzzy matching service based on Trigram distance for company names and roles in `backend/src/services/deduplicator.py`
- [x] T018 [US3] Integrate deduplication check inside the job submission task runner in `backend/src/services/tasks.py`

---

## Phase 6: User Story 4 - Application Tracking and Analytics Dashboard (Priority: P2)

**Goal**: View aggregate metrics and application status histories on the dashboard

**Independent Test**: Load the dashboard metrics API endpoint and verify all counts, volume trends, and skills request rates are returned.

### Tests for User Story 4
- [x] T019 [P] [US4] Unit test for analytics aggregates and SQL window trend functions in `backend/tests/unit/test_analytics.py`

### Implementation for User Story 4
- [x] T020 [US4] Implement `/api/v1/analytics/dashboard` endpoint in `backend/src/api/analytics.py` returning aggregate metrics, trend data, and skills statistics

---

## Phase 7: User Story 5 - Resume Optimization and Variant Management (Priority: P2)

**Goal**: Create and compile resume variants tagged by role category

**Independent Test**: Upload a Markdown variant and retrieve the compiled PDF from the storage bucket.

### Tests for User Story 5
- [x] T021 [P] [US5] Unit test for ResumeOptimizerAgent prompts in `backend/tests/unit/test_optimizer.py`

### Implementation for User Story 5
- [x] T022 [P] [US5] Implement variant creation endpoint `/api/v1/documents/resumes/variants` in `backend/src/api/documents.py`
- [x] T023 [US5] Implement `ResumeOptimizerAgent` in `backend/src/agents/optimizer.py` to identify missing skills and compile optimized resume variants

---

## Phase 8: User Story 6 - Automated Follow-up Emails (Priority: P3)

**Goal**: Schedule follow-ups, require approval, and track recruiter responses to cancel them

**Independent Test**: Verify follow-up schedules are cancelled automatically once a reply is received on the Google thread.

### Tests for User Story 6
- [x] T024 [P] [US6] Integration test for follow-up scheduling and thread response checking in `backend/tests/integration/test_follow_up.py`

### Implementation for User Story 6
- [x] T025 [US6] Implement background worker task `poll_sent_threads_for_responses` to call Gmail API thread details in `backend/src/services/tasks.py`
- [x] T026 [US6] Implement follow-up draft generation and approval endpoints in `backend/src/api/drafts.py`

---

## Phase 9: User Story 7 - Company Research and Personalization (Priority: P3)

**Goal**: Research target company details and weave them into the generated cold emails

**Independent Test**: Submit a job posting from a prominent tech company and verify the draft cold email includes recent products or tech stack references.

### Tests for User Story 7
- [x] T027 [P] [US7] Unit test for CompanyResearchAgent scraping and parsing prompts in `backend/tests/unit/test_company_research.py`

### Implementation for User Story 7
- [x] T028 [US7] Implement `CompanyResearchAgent` in `backend/src/agents/company_research.py` to fetch recent products, hiring trends, and tech stack details and weave them into email writing templates

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, validation, and optimizations

- [x] T029 [P] Update API documentation in `backend/README.md`
- [x] T030 [P] Harden Gmail OAuth tokens storage by encrypting credentials in transit and rest
- [x] T031 Run quickstart.md validation script end-to-end to verify all 7 User Stories pass

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) - BLOCKS all User Stories.
- **User Stories (Phases 3–9)**: Depend on Foundational (Phase 2).
  - Can proceed sequentially (P1 -> P2 -> P3).
- **Polish (Phase 10)**: Requires all target user stories to be complete.

### Parallel Opportunities
- Setup tasks T001–T003 can run in parallel.
- Foundational tasks T005–T006 can run in parallel.
- Once Foundation (Phase 2) is complete, Phases 3–9 can be executed in parallel by different developers.
- Unit/integration/contract tests marked with `[P]` under each story can be written and run in parallel.
