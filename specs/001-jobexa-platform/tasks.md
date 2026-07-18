# Tasks: Jobexa Platform

**Input**: Design documents from `/specs/001-jobexa-platform/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are requested per the project constitution's strict quality principles.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Paths shown below assume this layout

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure directories under backend/ and frontend/
- [x] T002 Initialize backend Python dependencies in backend/requirements.txt
- [x] T003 [P] Initialize frontend static configurations in frontend/js/api.js

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database connections, middleware, and auth that block user story implementation

- [x] T004 Implement database engine and config in backend/src/config.py
- [x] T005 Setup database migration config in backend/alembic.ini
- [x] T006 [P] Implement JWT token exchange endpoints in backend/src/api/auth.py
- [x] T007 Implement SQLAlchemy User model in backend/src/models/user.py
- [x] T008 Setup logging and CORS configurations in backend/src/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Submit Job Post via Telegram & Receive Review Link (Priority: P1) 🎯 MVP

**Goal**: Enable opportunity submission via Telegram bot, parsing via NVIDIA NIM, and receiving a dashboard review link.

**Independent Test**: Send a job post description text or PDF to the Telegram bot and verify a response containing the review URL link.

### Tests for User Story 1

- [x] T011 [US1] Create OCR and PDF parsing tests in backend/tests/unit/test_parser.py

### Implementation for User Story 1

- [x] T009 [P] [US1] Create JobOpportunity model in backend/src/models/application.py
- [x] T010 [P] [US1] Create Pydantic application schemas in backend/src/schemas/application.py
- [x] T012 [US1] Implement NVIDIA NIM analysis agent in backend/src/agents/planner.py
- [x] T013 [US1] Implement ATS scoring matcher in backend/src/agents/matcher.py
- [x] T014 [US1] Implement cover letter draft generator in backend/src/agents/writer.py
- [x] T015 [US1] Create end-to-end parsing integration tests in backend/tests/integration/test_agent_workflow.py
- [x] T016 [US1] Implement Telegram Bot token link handler in backend/bot.py
- [x] T017 [US1] Integrate background celery tasks for job post queues in backend/bot.py

**Checkpoint**: User Story 1 fully functional and testable independently.

---

## Phase 4: User Story 2 - Review and Approve Application on Web Dashboard (Priority: P1) 🎯 MVP

**Goal**: Review AI-generated email drafts, edit details, and trigger Gmail/SMTP transmission.

**Independent Test**: Edit a draft on the Web Dashboard and click approve, confirming the email arrives in the recruiter's inbox.

### Tests for User Story 2

- [x] T018 [P] [US2] Create contract tests for draft management in backend/tests/contract/test_drafts.py

### Implementation for User Story 2

- [x] T019 [US2] Implement draft update and delete endpoints in backend/src/api/drafts.py
- [x] T020 [P] [US2] Implement Gmail OAuth sending wrapper in backend/src/services/email.py
- [x] T021 [US2] Create application archive model in backend/src/models/application.py
- [x] T022 [US2] Create integration test for delivery failures in backend/tests/integration/test_delivery.py
- [x] T023 [US2] Build draft review interface page in frontend/index.html and frontend/js/app.js

**Checkpoint**: User Stories 1 and 2 work seamlessly together.

---

## Phase 5: User Story 3 - Manage Profile, Resumes, and Certificates (Priority: P2)

**Goal**: Upload and manage default/role-specific PDF resumes and certification attachments.

**Independent Test**: Upload a resume, verify it is set as default, and select it as an attachment on a job draft.

### Tests for User Story 3

- [x] T026 [P] [US3] Create upload endpoint contract tests in backend/tests/contract/test_documents.py

### Implementation for User Story 3

- [x] T024 [P] [US3] Create SQLAlchemy documents model in backend/src/models/resume.py
- [x] T025 [P] [US3] Create Pydantic resume schema in backend/src/schemas/resume.py
- [x] T027 [US3] Implement Supabase client storage connection in backend/src/services/storage.py
- [x] T028 [US3] Implement documents POST upload API in backend/src/api/documents.py
- [x] T029 [US3] Build document manager dashboard section in frontend/index.html and frontend/js/auth.js

**Checkpoint**: Resumes and documents are successfully stored and integrated with matching agents.

---

## Phase 6: User Story 4 - View Applications History & Dashboard Analytics (Priority: P3)

**Goal**: View historical sent applications and dashboard stats graphs.

**Independent Test**: Verify total applications, rejections, and response rates load correctly on the landing page.

### Tests for User Story 4

- [x] T032 [US4] Create stats computation unit tests in backend/tests/unit/test_analytics.py

### Implementation for User Story 4

- [x] T030 [P] [US4] Implement analytics stats JSON endpoint in backend/src/api/drafts.py
- [x] T031 [US4] Implement historical records GET endpoint in backend/src/api/drafts.py
- [x] T033 [US4] Build dashboard analytics chart container in frontend/index.html and frontend/js/app.js

**Checkpoint**: Full application history and stats visualization active.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Database migrations, failure handling UI popups, and documentation updates.

- [x] T034 [P] Generate first database tables migration file in backend/alembic/versions
- [x] T035 Implement delivery failure popup alerts in frontend/js/app.js
- [x] T036 Run quickstart check suite in backend/tests/integration/test_quickstart.py
- [x] T037 [P] Create execution guide in README.md

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. Blocks all user stories.
- **User Stories**: All depend on Foundational.
  - US1 (Phase 3) must be implemented first to enable opportunity ingestion.
  - US2 (Phase 4) depends on US1 (to review ingested opportunities).
  - US3 (Phase 5) integrates with US1/US2 (for attachments) but can start in parallel once database foundations are set.
  - US4 (Phase 6) depends on US2 (requires historical applications data).
- **Polish (Phase 7)**: Depends on all user stories.

### Parallel Opportunities
- Setup tasks (T002, T003) can execute in parallel.
- Foundational auth endpoints and schemas (T006) can execute in parallel with database configurations.
- Models (T009, T010) under US1 can execute in parallel.
- Email delivery client (T020) under US2 can be built in parallel with dashboard layouts.
- Document models (T024, T025) and contract tests (T026) under US3 can execute in parallel.
- Analytics endpoints (T030) under US4 can execute in parallel.
