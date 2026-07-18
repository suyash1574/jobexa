# Telegram Bot Contract: Jobexa Bot

The Jobexa Telegram Bot acts as a low-friction interaction client that communicates with the backend via secure webhooks or polling.

## Command Schemas

### 1. `/start`
Initializes interaction with the bot.
- **Bot Response (Unpaired)**:
  "Welcome to Jobexa! 🤖 Your personal AI career assistant.
  Please link your Telegram session to your Web Dashboard account to get started.
  Run `/link <code>` using the pairing code generated in your Web Dashboard Profile settings."

### 2. `/link <code>`
Pairs the Telegram chat session with the user's dashboard account.
- **Parameters**: `code` (6-digit pairing code from dashboard).
- **Bot Response (Success)**:
  "✅ Accounts paired successfully! You can now send job descriptions, URLs, screenshots, or PDFs to start automating your applications."
- **Bot Response (Failure/Expired)**:
  "❌ Invalid or expired pairing code. Please generate a new code on the Web Dashboard and try again."

### 3. `/help`
Displays bot usage information and available commands.
- **Bot Response**:
  "How to use Jobexa:
  1. Share a LinkedIn/Job URL.
  2. Upload a PDF of the job description.
  3. Upload a screenshot of the job post.
  4. Paste the plain text description.
  
  Available Commands:
  - `/link <code>` - Pair your account.
  - `/status` - Check your dashboard overview statistics.
  - `/help` - View this help menu."

### 4. `/status`
Retrieves dashboard summary statistics.
- **Bot Response**:
  "📊 **Jobexa Stats Overview**:
  - Total Applications: 142
  - Pending Drafts: 5
  - Upcoming Interviews: 12
  - Offers: 2"

---

## Interactive Workflows

### Workflow 1: Submitting a Job Opportunity

1. **User sends content**: User sends a URL, PDF, screenshot, or text.
2. **Analysis start**:
   - Bot responds: "🔍 Processing job description... This might take a moment."
3. **Recruiter Email Extraction check**:
   - **Case A: Recruiter Email Found**:
     - Bot proceeds with draft generation.
   - **Case B: Recruiter Email Missing**:
     - Bot prompts: "⚠️ I couldn't find the recruiter's email in this post. Would you like to provide it now? Or reply 'skip' to edit it on the dashboard."
     - User replies with email or "skip".
     - Bot proceeds.
4. **Draft completion**:
   - Bot responds: "✨ Tailored application draft created!
   - Job: [Role] at [Company]
   - ATS Match: 85%
   - 🔗 Review and approve the draft here: https://jobexa-dashboard/drafts/{id}"

### Workflow 2: Asynchronous Send Failure Alert

If email transmission fails on the backend:
1. **Webhook event triggered**: FastAPI backend notifies the Telegram Bot of send failure.
2. **Bot alerts user**:
   - Bot sends: "🚨 **Failed to send application!**
   - Job: [Role] at [Company]
   - Reason: Credential validation failed. Please check your Gmail connection or SMTP settings on the Web Dashboard."
