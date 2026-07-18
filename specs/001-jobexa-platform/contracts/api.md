# API Contract: Jobexa Dashboard API

All API requests and responses must conform to the following contracts. All request and response bodies must use JSON unless otherwise specified.

## Authentication Endpoints

### 1. User Registration
`POST /api/v1/auth/register`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "strongpassword123"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "e9a0db13-64a2-4a57-b286-63e809315572",
    "email": "user@example.com",
    "created_at": "2026-07-16T19:24:00Z"
  }
  ```

### 2. User Login (Obtain Token)
`POST /api/v1/auth/token`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "strongpassword123"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```

### 3. Generate Telegram Pairing Token
`POST /api/v1/auth/telegram-pairing-token`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**:
  ```json
  {
    "pairing_token": "893721",
    "expires_at": "2026-07-16T19:34:00Z"
  }
  ```

---

## Documents Management

### 1. List Resumes
`GET /api/v1/resumes`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**:
  ```json
  [
    {
      "id": "0dfbc460-31fa-40d0-8f92-5ec273617300",
      "filename": "suyash_resume_backend.pdf",
      "file_url": "https://supabase-storage/resumes/0dfbc460.pdf",
      "file_size": 240500,
      "role_tag": "Backend Engineer",
      "is_default": true,
      "created_at": "2026-07-16T19:24:00Z"
    }
  ]
  ```

### 2. Upload Resume
`POST /api/v1/resumes`
- **Headers**: `Authorization: Bearer <token>`
- **Request (Multipart Form-Data)**:
  - `file`: PDF file bytes (max 5MB)
  - `role_tag`: Optional string
  - `is_default`: Optional boolean
- **Response (201 Created)**:
  ```json
  {
    "id": "0dfbc460-31fa-40d0-8f92-5ec273617300",
    "filename": "suyash_resume_backend.pdf",
    "file_url": "https://supabase-storage/resumes/0dfbc460.pdf",
    "is_default": true
  }
  ```

---

## Job Application Drafts

### 1. List Drafts
`GET /api/v1/drafts`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**:
  ```json
  [
    {
      "id": "bfa89771-47cc-44a6-9ea1-d419a4e32109",
      "job": {
        "id": "cdba9223-11aa-4b07-a36c-9bc76ee12431",
        "company_name": "Google",
        "job_title": "AI Coding Assistant Developer",
        "recruiter_email": "recruiting@google.com"
      },
      "ats_compatibility_score": 85,
      "status": "Draft",
      "created_at": "2026-07-16T19:25:00Z"
    }
  ]
  ```

### 2. Get Draft Details
`GET /api/v1/drafts/{id}`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**:
  ```json
  {
    "id": "bfa89771-47cc-44a6-9ea1-d419a4e32109",
    "email_subject": "Application for AI Coding Assistant Developer - Suyash",
    "email_body": "Dear Hiring Manager,\n\nI am writing to express my interest...",
    "cover_letter": "Optional cover letter text here...",
    "recommended_resume_id": "0dfbc460-31fa-40d0-8f92-5ec273617300",
    "recommended_certificate_ids": [
      "22b100fa-3e2b-4e8c-8822-11ef88cc1022"
    ],
    "ats_compatibility_score": 85,
    "skill_match_score": 90,
    "experience_match_score": 80
  }
  ```

### 3. Update Draft
`PUT /api/v1/drafts/{id}`
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "email_subject": "Application for AI Developer - Suyash",
    "email_body": "Updated cover letter body...",
    "recommended_resume_id": "0dfbc460-31fa-40d0-8f92-5ec273617300",
    "recommended_certificate_ids": []
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "id": "bfa89771-47cc-44a6-9ea1-d419a4e32109",
    "status": "Ready"
  }
  ```

### 4. Approve and Send Application
`POST /api/v1/drafts/{id}/approve`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**:
  ```json
  {
    "message": "Application sent successfully",
    "application_record_id": "22ff0011-3e44-48b8-b808-1122334455aa"
  }
  ```
- **Response (502 Bad Gateway - Send Failure)**:
  ```json
  {
    "error": "Failed to send email. Credentials revoked or SMTP error.",
    "code": "EMAIL_DELIVERY_FAILED"
  }
  ```

---

## Analytics

### 1. Retrieve Dashboard Stats
`GET /api/v1/analytics/dashboard`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**:
  ```json
  {
    "total_applications": 142,
    "applications_this_month": 24,
    "pending_drafts": 5,
    "interviews": 12,
    "offers": 2,
    "rejections": 18,
    "response_rate": 8.4
  }
  ```
