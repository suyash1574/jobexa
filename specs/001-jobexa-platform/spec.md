# Feature Specification: Jobexa Platform

**Feature Branch**: `001-jobexa-platform`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "Jobexa is an AI-powered job application automation platform that combines a Telegram Bot, Web Dashboard, and AI Agents to streamline the entire job application process."

## Clarifications

### Session 2026-07-16

- Q: How should the system authorize and link a user's Telegram chat session to their Web Dashboard profile? → A: The Web Dashboard generates a secure temporary pairing token or link, which the user sends to the Telegram Bot to link accounts.
- Q: How should storage constraints for user-controlled documents (resumes/certificates) be structured? → A: Unlimited storage for personal use, but the database schema and backend API support per-user total storage caps and count limits to control cloud storage costs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit Job Post via Telegram & Receive Review Link (Priority: P1)

**Why this priority**: Core entry point for the job search workflow. Users need a quick, friction-free way to capture and submit opportunities on the go.

**Independent Test**: Send a job posting URL or PDF to the Telegram Bot and verify that the bot returns a confirmation message containing a link to the Web Dashboard.

**Acceptance Scenarios**:

1. **Given** the user is in the Telegram Bot, **When** they paste a valid LinkedIn job posting URL, **Then** the bot confirms receipt and sends a link to the generated application draft on the dashboard.
2. **Given** the user is in the Telegram Bot, **When** they upload a PDF containing a job description, **Then** the bot parses the PDF and returns a confirmation.
3. **Given** the user is in the Telegram Bot, **When** they upload a screenshot of a job post, **Then** the bot processes the image and returns a confirmation.
4. **Given** a new user has registered on the Web Dashboard, **When** they click "Link Telegram" to get a pairing token and send it to the Telegram Bot, **Then** the bot pairs their accounts and confirms the connection.

---

### User Story 2 - Review and Approve Application on Web Dashboard (Priority: P1)

**Why this priority**: Critical security and quality checkpoint. Prevents unapproved or incorrect emails from being sent to recruiters, protecting the candidate's professional reputation.

**Independent Test**: Navigate to the Web Dashboard, edit an email draft and subject line for a pending application, select a custom resume and certificate, and click approve to send the email.

**Acceptance Scenarios**:

1. **Given** a pending job application on the dashboard, **When** the user clicks "Approve", **Then** the system sends the tailored email using the user's connected mail account and updates the application status to "Sent".
2. **Given** a generated email draft on the dashboard, **When** the user edits the body text and subject line, **Then** the system saves the changes as the final draft to be sent.
3. **Given** a list of user resumes, **When** the user selects an alternative resume for a draft, **Then** the system attaches that specific resume instead of the default.

---

### User Story 3 - Manage Profile, Resumes, and Certificates (Priority: P2)

**Why this priority**: Required for personalization. The system needs the user's resume, certificates, and profile details to analyze skill matches and tailor drafts.

**Independent Test**: Upload a resume PDF and an AI certification PDF to the Resume Manager and verify they show up in the attachment selection when reviewing drafts.

**Acceptance Scenarios**:

1. **Given** the Resume Manager interface, **When** the user uploads a resume PDF, **Then** the system adds it to their resume options and allows them to mark it as the default.
2. **Given** the Certificates interface, **When** the user uploads a credential PDF, **Then** the system displays it in the list of available certificates to attach.

---

### User Story 4 - View Applications History & Dashboard Analytics (Priority: P3)

**Why this priority**: Enables tracking and progress visualization, helping the candidate manage their job search lifecycle.

**Independent Test**: Access the dashboard landing page and verify stats for total applications, pending drafts, interviews, rejections, and response rate.

**Acceptance Scenarios**:

1. **Given** the dashboard landing page, **When** applications have been sent, **Then** the user sees updated metrics for total sent applications, monthly counts, and response rates.
2. **Given** the Applications list, **When** the user views a historical application, **Then** the system displays the sent date, company, role, ATS compatibility score, final email draft, and attachment details.

---

### Edge Cases

- **No Recruiter Email Extracted**: The system attempts to extract the recruiter email from the provided content. If not found, the Telegram Bot asks the user to provide it. If the user indicates it is missing or skips, the system generates the draft with no email address specified, allowing it to be edited later on the Web Dashboard.
- **Delivery Credentials Revoked / Email Send Failure**: If the system fails to send an email via SMTP or Gmail API (due to credential revocation, network errors, etc.), it must immediately show a failure alert on all active platforms (Telegram Bot notification and a Web Dashboard popup/notification) and set the application status to `Failed`.
- **PDF Extraction Failure**: If a PDF file cannot be parsed, the system must notify the user in the Telegram Bot and provide a text input prompt for them to copy-paste the description.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept job descriptions via URL, text, PDF, and screenshots from the Telegram bot.
- **FR-002**: System MUST parse and extract company name, job title, required/preferred skills, recruiter email, and deadlines from job posts.
- **FR-003**: System MUST support managing multiple resumes, profile details, and certificates.
- **FR-004**: System MUST calculate ATS compatibility, skill match, and experience match scores between the user's profile and the job description.
- **FR-005**: System MUST generate tailored email subjects, application emails, and optional cover letters.
- **FR-006**: System MUST prevent any job application from being sent without explicit user approval.
- **FR-007**: System MUST support sending approved job applications from the user's authenticated email account.
- **FR-008**: System MUST persist a full history of all applications, draft versions, final sent emails, and attachments in a database.
- **FR-009**: System MUST allow editing the generated email subject, body, and attached files prior to approval.
- **FR-010**: System MUST support secure pairing of Telegram sessions with Web Dashboard profiles using a temporary pairing token generated by the web app.

### Key Entities *(include if feature involves data)*

- **User Profile**: Holds personal details, skills, credentials, and settings.
- **Resume**: Represents a PDF resume document (default or alternative).
- **Certificate**: Represents a professional certificate or project report PDF.
- **Job Opportunity**: Extracted details of the job (company, role, recruiter email, description).
- **Application Draft**: The AI-generated email body, subject lines, cover letter, and recommended attachments.
- **Application Record**: Represents a finalized, sent application with date, status (Sent, Interview, Offer, Rejected), and final artifacts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully upload a job post and receive a reviewable application draft link in under 60 seconds.
- **SC-002**: Extraction of company name and job title must achieve at least 95% accuracy on standard text and PDF inputs.
- **SC-003**: 100% of emails sent must have explicit user approval logged in the database.
- **SC-004**: The system must track and store 100% of sent applications and their corresponding attachments.

## Assumptions

- Users have a Telegram account and a web browser capable of running the dashboard.
- Users have a Google/Gmail account or an SMTP service to send emails.
- Resumes and certificates are uploaded in PDF format.
- The system behaves as a single-user personal career assistant.
- Users have unlimited storage for personal use, but database schemas and APIs support per-user size and file count caps to control operational costs when commercialized.
