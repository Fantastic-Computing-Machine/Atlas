<![CDATA[<div align="center">

# ⚛️ Atlas

**AI-powered Gmail control layer — organize & research your inbox.**

[![License: MIT](https://img.shields.io/badge/License-MIT-8b5cf6.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776ab.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://postgresql.org)

Atlas is a user-configurable AI layer for Gmail that organizes email into user-defined labels and answers natural-language research questions over a user-defined mailbox scope.

</div>

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment](#deployment)
  - [Step 1 — Infrastructure Services](#step-1--infrastructure-services)
  - [Step 2 — Google OAuth Setup](#step-2--google-oauth-setup)
  - [Step 3 — Environment Configuration](#step-3--environment-configuration)
  - [Step 4 — Backend Setup](#step-4--backend-setup)
  - [Step 5 — Frontend Setup](#step-5--frontend-setup)
  - [Step 6 — Database Migrations](#step-6--database-migrations)
  - [Step 7 — Run the Application](#step-7--run-the-application)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

### 📬 Inbox Organization by Intent
- Define custom labels with plain-English descriptions
- AI classifies incoming and historical email into your labels
- Preview proposed categorization before applying
- Confidence thresholds and approval workflows
- Corrections feed back into future classification

### 🔍 Scoped Research & Retrieval
- Ask natural-language questions over your mailbox
- Define what Atlas can search (e.g., "Primary only", "Everything except Promotions")
- Get evidence-backed answers with source citations
- Supports find, count, summarize, extract, and timeline queries

### 🔐 Privacy-First Design
- Local-first / single-tenant architecture
- Read-only Gmail access by default
- User controls exactly which mailbox categories Atlas can access
- Encrypted token storage with Fernet encryption

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Frontend (React 19 + Vite)                 │
│                        http://localhost:5173                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │  ConnectPage  │  │  Dashboard   │  │     ScopesPage       │    │
│  └──────────────┘  └──────────────┘  └──────────────────────┘    │
└────────────────────────────┬───────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼───────────────────────────────────────┐
│                     Backend (FastAPI + Uvicorn)                    │
│                       http://localhost:8000                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Auth API │  │Scopes API│  │Messages  │  │ Health Check     │  │
│  │          │  │          │  │   API    │  │                  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────────────┘  │
│       │              │             │                               │
│  ┌────▼──────────────▼─────────────▼─────────────────────────┐    │
│  │                     Services Layer                         │    │
│  │  AuthService · GmailService · SyncService · ScopeService  │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────┬──────────────────┬─────────────────────────────────────┘
           │                  │
    ┌──────▼──────┐    ┌──────▼──────┐
    │ PostgreSQL  │    │    Redis    │
    │   :5432     │    │   :6380     │
    └─────────────┘    └─────────────┘
```

---

## Tech Stack

| Layer          | Technology                                      |
|----------------|------------------------------------------------|
| **Frontend**   | React 19, React Router 7, Vite 8               |
| **Backend**    | Python 3.11, FastAPI, Uvicorn, Pydantic v2      |
| **Database**   | PostgreSQL 16 (asyncpg), Alembic migrations     |
| **Cache/Queue**| Redis 7 (Celery worker backend)                 |
| **AI/LLM**     | Google Gemini 2.5 Flash                         |
| **Auth**       | Google OAuth 2.0, Fernet token encryption       |
| **Gmail**      | Google Gmail API (readonly + labels)             |
| **Infra**      | Docker Compose                                   |

---

## Prerequisites

Ensure you have the following installed before proceeding:

| Tool            | Version  | Purpose                          |
|-----------------|----------|----------------------------------|
| **Docker**      | 20.10+   | Run PostgreSQL & Redis           |
| **Docker Compose** | v2+   | Orchestrate infrastructure       |
| **Python**      | 3.11+    | Backend runtime                  |
| **Node.js**     | 18+      | Frontend build & dev server      |
| **npm**         | 9+       | Frontend package management      |
| **Git**         | 2.30+    | Version control                  |

---

## Quick Start

For those who want to get running immediately:

```bash
# 1. Clone the repository
git clone https://github.com/Fantastic-Computing-Machine/Atlas.git
cd Atlas

# 2. Start infrastructure
docker compose up -d

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials (see Configuration section)

# 4. Set up backend
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# 5. Set up frontend
cd ../frontend
npm install

# 6. Run both servers (in separate terminals)
# Terminal 1 — Backend
cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Configuration

All configuration is managed through the `.env` file in the project root. Copy the example to get started:

```bash
cp .env.example .env
```

### Environment Variables

#### Database
| Variable           | Default                                                  | Description                    |
|--------------------|----------------------------------------------------------|--------------------------------|
| `DATABASE_URL`     | `postgresql+asyncpg://atlas:atlas_dev_password@localhost:5432/atlas` | Async database connection URL  |
| `DATABASE_URL_SYNC`| `postgresql+psycopg2://atlas:atlas_dev_password@localhost:5432/atlas` | Sync database URL (for Alembic) |

#### Redis
| Variable    | Default                    | Description              |
|-------------|----------------------------|--------------------------|
| `REDIS_URL` | `redis://localhost:6380/0` | Redis connection URL     |

> **Note:** The Docker Compose file maps Redis container port `6379` → host port `6380` to avoid conflicts with any locally installed Redis.

#### Google OAuth 2.0
| Variable               | Default                                    | Description                   |
|------------------------|--------------------------------------------|-------------------------------|
| `GOOGLE_CLIENT_ID`     | —                                          | OAuth client ID from GCP      |
| `GOOGLE_CLIENT_SECRET` | —                                          | OAuth client secret from GCP  |
| `GOOGLE_REDIRECT_URI`  | `http://localhost:8000/api/auth/callback`  | OAuth callback URL            |
| `GMAIL_SCOPES`         | `gmail.readonly,gmail.labels`              | Comma-separated Gmail scopes  |

#### Security
| Variable        | Default | Description                                                |
|-----------------|---------|------------------------------------------------------------|
| `ENCRYPTION_KEY`| —       | Fernet key for encrypting OAuth tokens at rest             |
| `SECRET_KEY`    | —       | Application secret for session signing                     |

Generate security keys with:
```bash
# Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Application
| Variable       | Default                  | Description                     |
|----------------|--------------------------|---------------------------------|
| `APP_ENV`      | `development`            | Environment: development / production |
| `APP_DEBUG`    | `true`                   | Enable debug mode               |
| `APP_HOST`     | `0.0.0.0`               | Backend bind address            |
| `APP_PORT`     | `8000`                   | Backend port                    |
| `FRONTEND_URL` | `http://localhost:5173`  | Frontend URL (for CORS)         |

#### Sync Settings
| Variable            | Default | Description                                |
|---------------------|---------|--------------------------------------------|
| `INITIAL_SYNC_DAYS` | `180`   | How many days of email history to sync     |
| `SYNC_BATCH_SIZE`   | `100`   | Messages to process per sync batch         |

#### LLM (Google Gemini)
| Variable       | Default             | Description                |
|----------------|---------------------|----------------------------|
| `GEMINI_API_KEY`| —                  | Google Gemini API key      |
| `GEMINI_MODEL` | `gemini-2.5-flash`  | Model to use for AI tasks  |

---

## Deployment

### Step 1 — Infrastructure Services

Atlas requires PostgreSQL and Redis. Both are configured via Docker Compose:

```bash
# Start Postgres and Redis containers
docker compose up -d

# Verify they're running and healthy
docker compose ps
```

Expected output:
```
NAME             IMAGE                STATUS                   PORTS
atlas-postgres   postgres:16-alpine   Up (healthy)             0.0.0.0:5432->5432/tcp
atlas-redis      redis:7-alpine       Up (healthy)             0.0.0.0:6380->6379/tcp
```

**Default database credentials:**
- **Database:** `atlas`
- **User:** `atlas`
- **Password:** `atlas_dev_password`
- **Host:** `localhost:5432`

To stop infrastructure:
```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop containers AND delete all data
```

---

### Step 2 — Google OAuth Setup

Atlas requires Google Cloud OAuth 2.0 credentials to connect to Gmail.

1. **Go to** the [Google Cloud Console](https://console.cloud.google.com/apis/credentials)

2. **Create a project** (or select an existing one)

3. **Enable the Gmail API:**
   - Navigate to **APIs & Services → Library**
   - Search for **Gmail API** and enable it

4. **Configure the OAuth Consent Screen:**
   - Go to **APIs & Services → OAuth consent screen**
   - Choose **External** (or Internal for Google Workspace)
   - Fill in the application name: `Atlas`
   - Add the scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.labels`
   - Add your email to **Test users** (required for unverified apps)

5. **Create OAuth 2.0 Credentials:**
   - Go to **APIs & Services → Credentials**
   - Click **Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:8000/api/auth/callback`
   - Copy the **Client ID** and **Client Secret**

6. **(Optional) Get a Gemini API Key:**
   - Go to [Google AI Studio](https://aistudio.google.com/apikey)
   - Create an API key for Gemini

---

### Step 3 — Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
# Google OAuth (required)
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here

# Security keys (generate with commands above)
ENCRYPTION_KEY=<your-generated-fernet-key>
SECRET_KEY=<your-generated-secret-key>

# Gemini (required for AI features)
GEMINI_API_KEY=<your-gemini-api-key>
```

---

### Step 4 — Backend Setup

```bash
cd backend

# Create Python virtual environment
python3.11 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### Step 5 — Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install
```

---

### Step 6 — Database Migrations

Apply all database migrations to create the schema:

```bash
cd backend

# Ensure virtual env is active
source .venv/bin/activate

# Run migrations
alembic upgrade head
```

This creates the following tables:

| Table                | Purpose                                      |
|----------------------|----------------------------------------------|
| `users`              | User accounts                                |
| `mailbox_connections`| Gmail OAuth connections and sync state        |
| `scopes`             | User-defined mailbox search scopes            |
| `messages`           | Synced Gmail message metadata                 |
| `threads`            | Thread-level aggregation                      |
| `labels`             | User-defined label definitions                |
| `label_policies`     | Label classification rules and thresholds     |
| `extractions`        | AI-extracted entities and classifications     |
| `query_runs`         | Natural-language query execution logs         |
| `action_runs`        | Label application action logs                 |

To check the current migration state:
```bash
alembic current    # shows the current revision
alembic history    # shows all revisions
```

---

### Step 7 — Run the Application

You need **two terminal sessions** — one for the backend and one for the frontend.

#### Terminal 1 — Backend API Server

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at:
- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/health

#### Terminal 2 — Frontend Dev Server

```bash
cd frontend
npm run dev
```

The frontend will be available at:
- **Application:** http://localhost:5173

#### Verify Everything is Working

```bash
# Check backend health
curl http://localhost:8000/api/health
# → {"status": "ok", "service": "atlas"}

# Check infrastructure
docker compose ps
redis-cli -p 6380 ping
# → PONG
```

---

## API Reference

### System

| Method | Endpoint         | Description       |
|--------|------------------|--------------------|
| `GET`  | `/api/health`    | Health check       |

### Authentication

| Method | Endpoint               | Description                              |
|--------|------------------------|------------------------------------------|
| `GET`  | `/api/auth/connect`    | Initiate Google OAuth flow               |
| `GET`  | `/api/auth/callback`   | Handle OAuth callback from Google        |
| `GET`  | `/api/auth/status`     | Check connection status for a user       |
| `POST` | `/api/auth/disconnect` | Revoke access and disconnect Gmail       |

### Scopes

| Method   | Endpoint                       | Description                         |
|----------|--------------------------------|-------------------------------------|
| `POST`   | `/api/scopes`                  | Create a new mailbox scope          |
| `GET`    | `/api/scopes`                  | List all scopes for a user          |
| `GET`    | `/api/scopes/{scope_id}`       | Get a specific scope                |
| `PUT`    | `/api/scopes/{scope_id}`       | Update a scope                      |
| `DELETE` | `/api/scopes/{scope_id}`       | Delete a scope                      |
| `POST`   | `/api/scopes/{scope_id}/preview`| Preview emails matching the scope  |

### Messages

| Method | Endpoint                  | Description                        |
|--------|---------------------------|------------------------------------|
| `GET`  | `/api/messages`           | List synced messages               |
| `GET`  | `/api/messages/sync/status`| Get current sync status           |
| `POST` | `/api/messages/sync`      | Trigger a mailbox sync             |
| `GET`  | `/api/messages/labels`    | List Gmail labels for the account  |

Full interactive API documentation is available at **http://localhost:8000/docs** when the backend is running.

---

## Project Structure

```
Atlas/
├── .env                          # Environment configuration (not in git)
├── .env.example                  # Environment template
├── docker-compose.yml            # PostgreSQL + Redis infrastructure
├── LICENSE                       # MIT License
├── PLAN.md                       # Detailed product & implementation plan
├── README.md                     # This file
│
├── backend/                      # Python FastAPI backend
│   ├── alembic/                  # Database migration scripts
│   │   ├── env.py                # Alembic environment configuration
│   │   └── versions/             # Migration version files
│   ├── alembic.ini               # Alembic configuration
│   ├── requirements.txt          # Python dependencies
│   ├── .venv/                    # Python virtual environment (not in git)
│   └── app/                      # Application source code
│       ├── main.py               # FastAPI app entrypoint & router registration
│       ├── config.py             # Pydantic settings (loads from .env)
│       ├── database.py           # SQLAlchemy async engine & session factory
│       ├── api/                  # Route handlers
│       │   ├── auth.py           # OAuth connect/callback/status/disconnect
│       │   ├── scopes.py         # CRUD for mailbox scopes
│       │   └── messages.py       # Message listing, sync, labels
│       ├── models/               # SQLAlchemy ORM models
│       │   ├── user.py           # User model
│       │   ├── mailbox.py        # MailboxConnection model
│       │   ├── scope.py          # Scope model
│       │   ├── message.py        # Message & Thread models
│       │   ├── label.py          # Label & LabelPolicy models
│       │   ├── query.py          # QueryRun model
│       │   └── action.py         # ActionRun model
│       ├── schemas/              # Pydantic request/response schemas
│       ├── services/             # Business logic layer
│       │   ├── auth_service.py   # OAuth token management & encryption
│       │   ├── gmail_service.py  # Gmail API interactions
│       │   ├── sync_service.py   # Mailbox sync orchestration
│       │   └── scope_service.py  # Scope compilation & query building
│       └── workers/              # Background task definitions (Celery)
│
└── frontend/                     # React 19 frontend
    ├── index.html                # HTML entry point
    ├── package.json              # Node dependencies & scripts
    ├── vite.config.js            # Vite build configuration
    └── src/
        ├── main.jsx              # React entry point
        ├── App.jsx               # Router & layout with sidebar navigation
        ├── index.css             # Global styles & design system
        ├── App.css               # App-specific styles
        ├── pages/
        │   ├── ConnectPage.jsx   # Gmail OAuth connection page
        │   ├── DashboardPage.jsx # Inbox overview dashboard
        │   └── ScopesPage.jsx    # Scope management page
        └── services/
            └── api.js            # Backend API client
```

---

## Data Model

```mermaid
erDiagram
    users ||--o{ mailbox_connections : has
    users ||--o{ scopes : defines
    users ||--o{ labels : creates
    users ||--o{ query_runs : executes
    users ||--o{ action_runs : triggers

    labels ||--o{ label_policies : "configured by"

    mailbox_connections ||--o{ messages : syncs
    messages }o--|| threads : "belongs to"
    messages ||--o{ extractions : "analyzed by"

    users {
        uuid id PK
        string email
        string auth_provider
        string encrypted_token_ref
        timestamp created_at
    }

    mailbox_connections {
        uuid id PK
        uuid user_id FK
        string provider
        json granted_scopes
        string sync_cursor
        timestamp watch_expiration
        string status
    }

    scopes {
        uuid id PK
        uuid user_id FK
        string name
        json include_system_labels
        json exclude_system_labels
        int default_date_window
    }

    messages {
        string gmail_message_id PK
        string thread_id FK
        timestamp internal_date
        string from_header
        string subject
        string snippet
        json label_ids
    }

    labels {
        uuid id PK
        uuid user_id FK
        string gmail_label_id
        string name
        string description
    }

    label_policies {
        uuid id PK
        uuid label_id FK
        string description
        float confidence_threshold
        string apply_mode
    }

    extractions {
        uuid id PK
        string message_id FK
        json classifier_outputs
        json entities_json
        float confidence
    }
```

---

## Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| **M1: Inbox Foundation** | ✅ Complete | OAuth, sync, scopes, message store |
| **M2: Label Organization** | 🔧 In Progress | AI classification, label policies, preview-approve workflow |
| **M3: Query & Research** | 📋 Planned | NL query engine, evidence-backed answers |
| **M4: Continuous Monitoring** | 📋 Planned | Gmail watch, incremental sync, auto-suggestions |
| **M5: Hardening** | 📋 Planned | Privacy controls, audit logging, compliance |

---

## Troubleshooting

### Docker containers won't start
```bash
# Check if ports are already in use
lsof -i :5432    # PostgreSQL
lsof -i :6380    # Redis

# View container logs
docker compose logs postgres
docker compose logs redis
```

### Database connection errors
```bash
# Verify PostgreSQL is accepting connections
docker exec atlas-postgres pg_isready -U atlas
# → accepting connections

# Check database exists
docker exec atlas-postgres psql -U atlas -d atlas -c "\l"
```

### Migration errors
```bash
# Check current migration state
cd backend && .venv/bin/alembic current

# Force to a specific revision (use with caution)
alembic stamp head
alembic upgrade head
```

### Frontend can't reach backend
- Ensure the backend is running on port `8000`
- Check CORS settings in `.env` — `FRONTEND_URL` must match the frontend URL
- Verify with: `curl http://localhost:8000/api/health`

### OAuth callback fails
- Ensure `GOOGLE_REDIRECT_URI` in `.env` matches the URI configured in Google Cloud Console
- Default: `http://localhost:8000/api/auth/callback`
- Your email must be added as a **test user** in the OAuth consent screen

### Redis connection refused
```bash
# Check Redis is responding
redis-cli -p 6380 ping
# → PONG

# If using default port 6379 locally, update .env:
REDIS_URL=redis://localhost:6380/0
```

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

© 2026 Fantastic Computing Machine
]]>
