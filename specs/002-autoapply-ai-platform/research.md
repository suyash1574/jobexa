# Technical Research: Jobexa AutoApply AI Platform

## Decision 1: Gmail API OAuth 2.0 Integration

- **Decision**: Implement multi-tenant Google OAuth 2.0 authorization.
- **Rationale**: Storing raw email passwords in a database violates security best practices. Google OAuth 2.0 allows users to consent to specific scopes (`https://www.googleapis.com/auth/gmail.send` and `https://www.googleapis.com/auth/gmail.readonly`) for their individual accounts. Access and refresh tokens are stored securely in PostgreSQL (encrypted).
- **Alternatives Considered**: 
  - *Gmail SMTP with App Passwords*: Rejected because Google is deprecating app passwords for standard logins, deliverability is lower, and it doesn't allow reading thread history for response tracking.
  - *System Domain Sender*: Rejected because sending all emails from one address reduces personalization and can trigger spam filters across the whole platform.

---

## Decision 2: Dynamic PDF Resume Optimization

- **Decision**: Implement Markdown-to-PDF compilation using `weasyprint` or HTML-to-PDF engines.
- **Rationale**: Markdown offers a clean separation of content and style. The Resume Optimizer Agent edits the markdown resume variant, and the system compiles it to a PDF on the fly. This ensures structural consistency, is highly testable, and supports standard CSS styling.
- **Alternatives Considered**:
  - *LaTeX to PDF*: Rejected because compiling LaTeX requires a large system TeX installation (e.g. TeX Live), which exceeds Render's container constraints and increases cold start times.
  - *Docx to PDF*: Rejected because converting Microsoft Word files in headless Linux environments requires installing LibreOffice, which is heavy and slow.

---

## Decision 3: Duplicate Application Prevention

- **Decision**: Use PostgreSQL pg_trgm (trigram) extensions for fuzzy company matching and role titles within a 30-day threshold.
- **Rationale**: Reposted jobs often have tiny variations ("Software Engineer II" vs "Software Engineer - Backend"). A trgm fuzzy match (similarity threshold > 0.8) on the company name combined with role title semantic comparison successfully prevents duplicates without failing on minor formatting changes.
- **Alternatives Considered**:
  - *Exact URL Matching*: Rejected because the same job posted on LinkedIn and Indeed has completely different URLs.
  - *Exact String Matching*: Rejected because company name typos ("Google" vs "Google LLC") bypass exact matches.

---

## Decision 4: Recruiter Reply Tracking

- **Decision**: Poll sent thread status via Gmail API using the `threadId` cached during initial dispatch.
- **Rationale**: Checking thread history is highly focused. By polling only `https://gmail.googleapis.com/gmail/v1/users/me/threads/{threadId}`, we avoid scanning the user's entire inbox, keeping permissions narrow and p95 API response times low. If the thread message count increases and the last message is from the recruiter's domain, a reply is registered.
- **Alternatives Considered**:
  - *Inbox-wide Webhooks (Pub/Sub)*: Rejected due to high architectural overhead and the need for broad Gmail Inbox read permissions.
  - *Manual-only tracking*: Preserved as a dashboard manual fallback, but automated polling is the primary cancel signal.
