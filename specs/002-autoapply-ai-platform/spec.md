# Feature Specification: Jobexa AutoApply AI Platform

**Feature Branch**: `002-autoapply-ai-platform`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "An AI-powered job application platform that scrapes job posts, matches them with resumes, generates personalized emails, selects the best resume, attaches resume + cover letter, sends emails automatically with human approval, tracks every application, avoids duplicates, and follows up after a few days. Multi-agent architecture with job scraper, JD analyzer, resume matcher, resume optimizer, cover letter agent, email writer, email sender, tracker, and follow-up agent. Dashboard with analytics. SaaS-ready."

## Clarifications

### Session 2026-07-17

- Q: How should the system determine if a job posting/application is a duplicate to prevent redundant applications? → A: Same company name and job title (fuzzy match) within a 30-day window.
- Q: How should the system detect recruiter responses to cancel follow-up emails? → A: Automated Thread Monitoring via Gmail API threadId polling, with mandatory user approval required before any follow-up is sent.
- Q: How should the Gmail sending integration be structured for multiple users in this SaaS platform? → A: Multi-Tenant User OAuth (each user connects their personal Gmail account via Google OAuth 2.0).
- Q: How should the Resume Optimizer Agent produce optimized resume variants? → A: Dynamic PDF compilation (Markdown/LaTeX to PDF).
- Q: Given the cost and setup complexity of the official WhatsApp Business API, how should the WhatsApp channel be scoped for the MVP? → A: Out of Scope for MVP (only Telegram and Web Dashboard are supported).

### Session 2026-07-18

- Q: How should the system handle revoked or permanently invalid Google OAuth credentials during background tasks or email dispatch? → A: Pause all pending drafts/follow-ups without data loss, mark Gmail status as Reauthentication Required, and alert the user on Telegram and Dashboard to re-link Gmail.
- Q: What fallback behavior should occur if dynamic PDF compilation fails for a resume variant? → A: Fallback to the user's uploaded default static PDF resume, log the error, and display a warning banner on the draft review card.
- Q: Which extracted metadata fields are mandatory to create a draft, and how long should company research data be cached? → A: Mandatory fields are `company_name` and `job_title` (or raw job description text). All other fields are optional with AI discovery/fallback. Company research profiles are cached for 30 days.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit a Job Posting for AI Processing (Priority: P1)

A user sends a job posting to the system via Telegram (text, PDF, screenshot) or through the web dashboard. The system's AI pipeline automatically extracts structured details (company, role, skills, recruiter email, deadline), scores the user's resume against the job description, selects the best-matching resume variant, generates a personalized email and cover letter, and presents the draft for the user's review.

**Why this priority**: This is the core value proposition — transforming a raw job posting into a ready-to-send, personalized application. Without this, the platform has no reason to exist.

**Independent Test**: Can be fully tested by submitting a sample job description and verifying that a structured draft with scores, personalized email, and cover letter is generated and presented to the user.

**Acceptance Scenarios**:

1. **Given** a user has uploaded at least one resume, **When** they send a job posting via any supported channel, **Then** the system extracts job details, scores the resume match, selects the best resume variant, and presents a draft with email body, cover letter, and ATS compatibility score within 2 minutes.
2. **Given** a job posting lacks a recruiter email, **When** the system processes it, **Then** the system attempts to discover the recruiter's contact information and flags it for user confirmation if not found.
3. **Given** a user has multiple resume variants, **When** a job posting is processed, **Then** the system automatically selects the highest-scoring variant and displays the selection rationale.

---

### User Story 2 - Review, Edit, and Approve Applications (Priority: P1)

A user reviews AI-generated application drafts on the web dashboard or Telegram bot. They can view the full email body, cover letter, selected resume, ATS scores, and recruiter details. They can edit any field before approving. Upon approval, the system sends the application email with attachments via Gmail API or SMTP.

**Why this priority**: Human-in-the-loop approval is a constitutional non-negotiable. Users must retain control over what gets sent in their name.

**Independent Test**: Can be tested by creating a mock draft and verifying the user can view, edit, approve, and trigger email delivery with correct attachments.

**Acceptance Scenarios**:

1. **Given** a pending draft exists, **When** the user opens it on the dashboard or Telegram, **Then** they see the full email body, cover letter, selected resume, match scores, and recruiter email.
2. **Given** the user edits the email body and approves, **When** the system sends the email, **Then** the sent email reflects the user's edits and includes the selected resume and cover letter as attachments.
3. **Given** email delivery fails, **When** the failure occurs, **Then** the system records the failure, notifies the user on all connected channels, and preserves the draft for retry.

---

### User Story 3 - Job Collection from Multiple Sources (Priority: P2)

The system collects job postings from multiple sources — user submissions via Telegram, LinkedIn job links, company career pages, job boards (Naukri, Indeed, Wellfound), and direct text/PDF/screenshot inputs. Each job is deduplicated and stored in a structured format.

**Why this priority**: Expanding input sources increases the volume and quality of job opportunities the user can access, but the core pipeline (P1) must work first.

**Independent Test**: Can be tested by submitting job postings through different channels and verifying deduplication and structured storage.

**Acceptance Scenarios**:

1. **Given** a user submits a job posting that has already been processed, **When** the system checks for duplicates, **Then** it notifies the user that this job has already been submitted and does not create a duplicate draft.
2. **Given** a user sends a LinkedIn job URL, **When** the system processes it, **Then** it extracts the job details from the URL and creates a structured job opportunity record.
3. **Given** a user sends a screenshot of a job posting, **When** the system performs OCR, **Then** it extracts the text and processes it through the standard AI pipeline.

---

### User Story 4 - Application Tracking and Analytics Dashboard (Priority: P2)

The user views a comprehensive dashboard showing all applications, their statuses (Draft, Sent, Interview, Offer, Rejected, Failed), response rates, application volume trends, most-applied skills, and most-requested skills. Each application record includes the company, role, date applied, and current status.

**Why this priority**: Tracking enables users to measure their job search progress and make data-driven decisions about where to focus their efforts.

**Independent Test**: Can be tested by creating sample application records and verifying the dashboard displays correct aggregate statistics, charts, and filterable history.

**Acceptance Scenarios**:

1. **Given** a user has sent multiple applications, **When** they view the dashboard, **Then** they see total applications, pending count, interview count, offer count, rejection count, and response rate.
2. **Given** a user has application history, **When** they view the analytics section, **Then** they see application volume trends by week and top skills applied/requested.
3. **Given** a user updates an application status (e.g., marks "Interview scheduled"), **When** the update is saved, **Then** the dashboard metrics refresh to reflect the change.

---

### User Story 5 - Resume Optimization and Variant Management (Priority: P2)

The system creates and manages multiple resume variants (e.g., AI-focused, Backend-focused, Data-focused, GenAI-focused). When processing a job posting, the Resume Optimizer Agent can suggest modifications to an existing resume to improve ATS scores for a specific role, highlighting missing skills and recommended additions.

**Why this priority**: Resume optimization significantly improves application quality and ATS pass rates, but requires the core matching pipeline to be functional first.

**Independent Test**: Can be tested by uploading a base resume, processing a job posting, and verifying the system suggests modifications and/or selects the best variant.

**Acceptance Scenarios**:

1. **Given** a user has a base resume, **When** they request a variant for a specific role category, **Then** the system generates a tailored resume variant emphasizing relevant skills and experience.
2. **Given** a job posting requires skills not on the user's resume, **When** the match analysis runs, **Then** the system identifies missing skills and suggests relevant projects or certifications to add.
3. **Given** multiple resume variants exist, **When** the user views their resume library, **Then** each variant displays its role tag, ATS score range, and last-used date.

---

### User Story 6 - Automated Follow-up Emails (Priority: P3)

After an application is sent, the system automatically schedules follow-up emails at configurable intervals (default: 5, 10, and 15 days). Each follow-up is personalized, references the original application, and is presented for user approval before sending (unless auto-send is enabled for follow-ups).

**Why this priority**: Follow-ups significantly improve response rates but are an enhancement to the core apply flow.

**Independent Test**: Can be tested by approving an application and verifying that follow-up drafts are generated at the scheduled intervals and presented for approval.

**Acceptance Scenarios**:

1. **Given** an application was sent 5 days ago with no response, **When** the follow-up scheduler runs, **Then** a personalized follow-up draft is created and the user is notified via Telegram and dashboard.
2. **Given** a user has enabled auto-send for follow-ups, **When** the follow-up is due, **Then** the system sends the follow-up automatically and records it in the application history.
3. **Given** a user has already received a response (interview, rejection), **When** the follow-up is scheduled, **Then** the system cancels the follow-up and notifies the user.

---

### User Story 7 - Company Research and Personalization (Priority: P3)

The system researches the target company before generating application emails. It gathers information about recent products, tech stack, latest news, and hiring trends. This context is woven into the email and cover letter to make applications feel deeply personalized and human-written.

**Why this priority**: Company-specific personalization dramatically improves email response rates but requires the core email writing pipeline to be stable first.

**Independent Test**: Can be tested by processing a job posting for a well-known company and verifying the generated email references company-specific details.

**Acceptance Scenarios**:

1. **Given** a job posting from a known company, **When** the email is generated, **Then** the email body includes at least one company-specific reference (recent product, tech stack, or news item).
2. **Given** no company information can be found, **When** the email is generated, **Then** the system gracefully falls back to a role-focused email without fabricating company details.

---

### Edge Cases

- What happens when the user submits a job posting in a language other than English? → System processes the text as-is and generates an English application, unless the user has configured a preferred application language.
- What happens when the recruiter email is invalid or bounces? → System records the bounce, marks the application as "Failed - Bounce", and notifies the user.
- What happens when the user's Gmail OAuth token expires or is revoked? → System pauses all pending drafts and scheduled follow-ups, marks account status as `Reauthentication Required`, and sends alerts via Telegram and Web Dashboard instructing the user to re-link Gmail.
- What happens when two job postings from the same company for the same role are submitted? → System detects the duplicate and prompts the user to confirm or skip.
- What happens when the user has no resume uploaded? → System blocks draft generation and prompts the user to upload at least one resume first.
- What happens when the AI generates an email that sounds robotic? → The AI Humanizer pass ensures natural language patterns, varied sentence structure, and avoidance of common AI-sounding phrases (e.g. avoiding words like 'delve', 'testament', 'beacon').
- What happens if a recruiter responds outside the original email thread? → The user can manually mark the application status as 'Replied' on the Web Dashboard or Telegram Bot, which immediately cancels all remaining scheduled follow-up drafts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract structured job details from job postings submitted as text, PDF, screenshot, or URL. `company_name` and `job_title` (or raw text) are mandatory; all other attributes (recruiter email, skills, deadline, salary, experience) are optional with automated fallback discovery.
- **FR-002**: System MUST score the user's resume against a job description, producing ATS compatibility, skill match, and experience match percentages.
- **FR-003**: System MUST automatically select the best-matching resume variant when multiple variants exist.
- **FR-004**: System MUST generate a personalized, non-generic application email referencing the user's specific skills, projects, and experience relevant to the job.
- **FR-005**: System MUST generate a role-specific and company-specific cover letter for each application.
- **FR-006**: System MUST present all AI-generated content (email, cover letter, resume selection) for user review and editing before sending.
- **FR-007**: System MUST send approved applications via the user's personal Gmail account connected via Gmail API OAuth 2.0 (with SMTP as fallback), attaching the selected resume, cover letter, and optionally portfolio/certificates.
- **FR-008**: System MUST record every application with company, role, date applied, status, email body, and attachments sent.
- **FR-009**: System MUST detect and prevent duplicate applications by checking if an application has been sent to the same company for a role with a similar title (fuzzy match) within a 30-day window.
- **FR-010**: System MUST schedule and generate follow-up email drafts at configurable intervals after application submission, and MUST require explicit user approval before sending any follow-up.
- **FR-011**: System MUST monitor email threads of sent applications via the Gmail API (`threadId`) to detect recruiter responses and automatically cancel pending follow-up approvals if a response is received.
- **FR-012**: System MUST support job submission via Telegram, web dashboard, and URL input. (WhatsApp integration is explicitly out of scope for the MVP).
- **FR-013**: System MUST synchronize all application states in real-time across Telegram bot and web dashboard.
- **FR-014**: System MUST provide a dashboard with aggregate analytics: total applications, applications per week, interview ratio, response rate, most applied/requested skills.
- **FR-015**: System MUST create, compile, and manage multiple resume variants tagged by role category, supporting dynamic PDF compilation from Markdown/LaTeX sources (falling back to the user's default static PDF resume if dynamic compilation fails).
- **FR-016**: System MUST identify missing skills and dynamically compile an optimized PDF resume incorporating recommended skill and project additions when matching scores fall below a configurable threshold.
- **FR-017**: System MUST apply an AI humanization pass to all generated emails to ensure natural, non-robotic language.
- **FR-018**: System MUST research target companies and incorporate company-specific context into application emails when available.

### Key Entities

- **User**: The job seeker. Has credentials, connected channels (Telegram, Gmail), uploaded resumes, certificates, and application preferences.
- **Job Opportunity**: A structured representation of a job posting. Includes company, role, skills, recruiter email, deadline, source URL, salary range, experience level, and raw content.
- **Resume Variant**: A version of the user's resume optimized for a specific role category (e.g., AI, Backend, Data, GenAI). Has a role tag, ATS score history, and content.
- **Application Draft**: An AI-generated application package awaiting user approval. Contains email subject, email body, cover letter, selected resume variant, match scores, and recommended attachments.
- **Application Record**: A historical record of a sent application. Contains company, role, date applied, status, email body sent, attachments, and follow-up schedule.
- **Follow-up Schedule**: A series of scheduled follow-up emails tied to an application record. Each has a scheduled date, status (pending, sent, cancelled), and generated content.
- **Company Profile**: Cached research data about a target company. Contains recent products, tech stack, news, hiring trends, and last-refreshed date (cached for 30 days before refresh).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can go from receiving a job posting to having a ready-to-send, personalized application draft in under 2 minutes.
- **SC-002**: The system achieves a duplicate detection accuracy rate of 95% or higher, preventing redundant applications.
- **SC-003**: At least 80% of generated application emails require no more than minor edits (fewer than 3 sentence changes) before user approval.
- **SC-004**: The system supports processing at least 50 job submissions per user per day without performance degradation.
- **SC-005**: Follow-up emails are generated and presented to the user within 1 hour of the scheduled follow-up time.
- **SC-006**: Users can view their complete application history and analytics dashboard with data loading in under 3 seconds.
- **SC-007**: The system correctly selects the highest-scoring resume variant for a given job posting at least 90% of the time (validated against user override rates).
- **SC-008**: Application emails pass AI-detection tools (e.g., GPTZero) as human-written at least 85% of the time.

## Assumptions

- Users have a Gmail account and are willing to connect it via OAuth for sending applications. SMTP is available as a fallback.
- The initial version targets the English language for job postings and generated content. Multi-language support is deferred to a future version.
- Users are responsible for providing accurate resume content. The system optimizes formatting and targeting but does not fabricate experience or skills.
- Job scraping from third-party platforms (LinkedIn, Naukri, Indeed, Wellfound) is limited by those platforms' terms of service and rate limits. The system will prioritize user-submitted postings and publicly accessible career pages.
- The existing Jobexa backend (FastAPI, PostgreSQL/Supabase, Telegram bot, Supabase Storage) will be extended rather than rebuilt from scratch.
- WhatsApp integration is deferred to a future phase and is out of scope for the MVP.
- Company research data may be incomplete or unavailable for smaller companies. The system gracefully degrades to role-focused personalization when company data is insufficient.
- The free tier supports limited daily applications. Commercialization and SaaS tier limits will be defined in a separate billing specification.
