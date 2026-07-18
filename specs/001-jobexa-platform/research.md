# Research: Jobexa Platform

## Technology Decisions & Rationale

### 1. Backend Web Framework: FastAPI
- **Decision**: FastAPI (Python 3.11/3.12)
- **Rationale**: 
  - Direct alignment with the Constitution's strict typing requirement (Principle VI) via built-in Pydantic integration.
  - Native asynchronous support (`async/await`) is critical for handling concurrent Telegram Bot webhooks and Web Dashboard API calls without blocking.
  - Automatic OpenAPI documentation generation.
- **Alternatives Considered**: 
  - Django: Rejected due to heavier footprint and slower async development ecosystem.
  - Node.js (Express): Rejected to keep the codebase unified in Python, which is optimal for AI prompt engineering and agent routing.

### 2. Multi-Agent AI Orchestration
- **Decision**: Custom Router Pattern utilizing NVIDIA NIM API
- **Rationale**:
  - The Constitution (Principle II) mandates specialized modular agents over monolithic prompts.
  - NVIDIA NIM provides low-latency inference for optimized models (e.g., Llama-3, Nemotron-4, DeepSeek, Qwen).
  - Standardized JSON schemas via Pydantic will format agent-to-agent exchanges.
- **Alternatives Considered**:
  - LangChain / CrewAI: Rejected to avoid unnecessary third-party dependencies and performance overhead, favoring simple, direct API calls with strict schema verification.

### 3. Database: PostgreSQL (Neon / Supabase)
- **Decision**: PostgreSQL with SQLAlchemy ORM and Alembic Migrations
- **Rationale**:
  - Provides robust transaction locking (ACID compliance) required to synchronize Telegram Bot state changes and Dashboard reviews in real-time without race conditions.
  - Supabase/Neon offer managed serverless instances, keeping startup costs at zero.
- **Alternatives Considered**:
  - SQLite: Rejected due to write concurrency locks which would cause failures when the bot and web app try to write simultaneously.
  - MongoDB: Rejected because relational integrity is critical for storing profiles, multiple resumes, certificates, and application status histories.

### 4. Background Task Processing
- **Decision**: Celery (with Redis) or FastAPI `BackgroundTasks`
- **Rationale**:
  - Generating email drafts, tailoring resumes, and calculating ATS scores takes multiple seconds (up to 15-30s).
  - Background tasks are mandatory to keep non-LLM API responses under the 300ms limit (Principle IX).
- **Alternatives Considered**:
  - Inline synchronous execution: Rejected as it blocks API threads and creates a poor user experience.

### 5. Document Storage
- **Decision**: Supabase Storage / AWS S3
- **Rationale**:
  - High availability, direct URL generation with expiry times, and zero-cost tier access.
  - Storing PDF blobs directly in PostgreSQL is rejected to keep database size low and performance high.
- **Alternatives Considered**:
  - Local Disk: Rejected since Render (backend hosting) uses ephemeral file systems.
