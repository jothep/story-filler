# Maori Story Filler - System Architecture Documentation

**Document Version**: 1.0  
**Last Updated**: 2026-05-01  
**Author**: Xiang Zhu

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagrams](#architecture-diagrams)
3. [Component Details](#component-details)
4. [Deployment Architectures](#deployment-architectures)
5. [Technology Stack](#technology-stack)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Data Flow](#data-flow)
8. [Security Architecture](#security-architecture)
9. [Scalability & Performance](#scalability--performance)
10. [Monitoring & Logging](#monitoring--logging)

---

## System Overview

### Purpose
Educational web application for learning Māori language through interactive story-filling exercises.

### Architecture Style
- **Pattern**: Three-tier architecture (Presentation, Application, Data)
- **Deployment**: Serverless on Google Cloud Platform (current production)
- **API**: RESTful API with Django REST Framework
- **Frontend**: Single Page Application (SPA) with React

### Current Production Stack
- ⭐ **Frontend**: GitHub Pages (global CDN, free)
- ⭐ **Backend**: Google Cloud Run (serverless, auto-scaling 0-100)
- ⭐ **Database**: Neon PostgreSQL (serverless, auto-suspend)
- ⭐ **Storage**: Google Cloud Storage (media files)
- ⭐ **Cost**: $0/month (within free tiers)

### Key Characteristics
- ✅ **Serverless**: Zero server management, auto-scaling
- ✅ **Cost-Effective**: $0/month for current traffic (~5K requests/month)
- ✅ **Scalable**: Auto-scales from 0 to 100 instances
- ✅ **Global**: CDN distribution via GitHub Pages
- ✅ **Secure**: HTTPS everywhere, encrypted secrets, input validation
- ✅ **Observable**: Cloud Run logs, Neon metrics, GitHub Actions

---

## Architecture Diagrams

> **Note**: The diagrams below show the **Kubernetes deployment architecture**. For the **current production architecture** (GitHub Pages + Cloud Run + Neon), see:
> - **Detailed docs**: [architecture-production-gcp.md](architecture-production-gcp.md)
> - **Mermaid diagrams**: [architecture-diagrams.md](architecture-diagrams.md#0-current-production-architecture-gcp)

### 1. High-Level System Architecture (Kubernetes Alternative)

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Browser    │  │    Mobile    │  │   Tablet     │         │
│  │  (Desktop)   │  │   Browser    │  │   Browser    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                  │                  │
│         └─────────────────┼──────────────────┘                  │
│                           │ HTTPS                               │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     INGRESS / LOAD BALANCER                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Nginx Ingress Controller / Cloud Load Balancer           │ │
│  │  - SSL Termination                                         │ │
│  │  - Path-based Routing                                      │ │
│  │  - Rate Limiting (150MB body size)                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────┬──────────────────────┬──────────────────────────┘
                │                      │
    ┌───────────▼──────────┐  ┌───────▼──────────┐
    │   /api/*, /admin/*   │  │      / (SPA)     │
    │   /static/*, /media/ │  │                  │
    └───────────┬──────────┘  └───────┬──────────┘
                │                      │
┌───────────────▼──────────────────────▼──────────────────────────┐
│                      APPLICATION LAYER                          │
│  ┌───────────────────────────┐  ┌──────────────────────────┐   │
│  │   Backend Service         │  │   Frontend Service       │   │
│  │   (Django + Gunicorn)     │  │   (React SPA + nginx)    │   │
│  │                           │  │                          │   │
│  │  Port: 8000               │  │  Port: 80                │   │
│  │  Replicas: 1-N            │  │  Replicas: 1-N           │   │
│  │  Framework: Django 5.2    │  │  Build: Vite             │   │
│  │  WSGI: Gunicorn (gevent)  │  │  Server: nginx:alpine    │   │
│  │  Workers: 3               │  │  Size: ~20MB             │   │
│  │                           │  │                          │   │
│  │  APIs:                    │  │  Features:               │   │
│  │  - /api/stories/          │  │  - Story List UI         │   │
│  │  - /api/config/           │  │  - Drag-n-Drop           │   │
│  │  - /admin/ (Django)       │  │  - BGM Player            │   │
│  │  - /media/ (files)        │  │  - NES.css Theme         │   │
│  │  - /static/ (assets)      │  │  - Accessibility         │   │
│  └─────────────┬─────────────┘  └──────────────────────────┘   │
│                │                                                 │
│                │ PersistentVolumeClaim                          │
│                │ (media files)                                  │
│                │                                                 │
└────────────────┼─────────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL 16 (StatefulSet)                              │  │
│  │  - Database: django_db                                    │  │
│  │  - Port: 5432                                             │  │
│  │  - Storage: 5Gi PVC (ReadWriteOnce)                      │  │
│  │  - Health Checks: pg_isready                              │  │
│  │  - Resources: 256Mi-1Gi memory, 250m-1000m CPU           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Media Storage (Optional S3)                              │  │
│  │  - Local: /app/media (PVC)                                │  │
│  │  - MinIO: Self-hosted S3-compatible                       │  │
│  │  - AWS S3: Cloud object storage                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 2. Request Flow Diagram

```
┌─────────┐
│ Browser │
└────┬────┘
     │ 1. HTTP Request
     │    GET https://app.example.com/
     ▼
┌─────────────────┐
│ Nginx Ingress   │──────┐
│ Controller      │      │ Path Routing Rules:
└────┬─────┬──────┘      │ - / → Frontend Service
     │     │             │ - /api/* → Backend Service
     │     │             │ - /admin/* → Backend Service
     │     └─────────────┤ - /media/* → Backend Service
     │                   │ - /static/* → Backend Service
     │ 2a. SPA Request   └─────────────┐
     ▼                                 │ 2b. API Request
┌──────────────┐                       ▼
│   Frontend   │              ┌────────────────┐
│   Service    │              │    Backend     │
│  (nginx:80)  │              │    Service     │
└──────┬───────┘              │  (Django:8000) │
       │                      └────────┬───────┘
       │ 3. Return index.html          │
       │    + static assets            │ 3. Query DB
       ▼                               ▼
┌─────────┐                   ┌────────────────┐
│ Browser │                   │   PostgreSQL   │
│ Renders │                   │   (Port 5432)  │
└────┬────┘                   └────────┬───────┘
     │                                 │
     │ 4. Fetch data via API           │
     │    GET /api/stories/            │
     │ ────────────────────────────────┤
     │                                 │ 4. Return JSON
     │ ◄───────────────────────────────┤    {stories: [...]}
     │                                 │
     │ 5. Interactive Session          │
     │    - BGM player (fetch audio)   │
     │    - Drag-and-drop words        │
     │    - POST /api/story/1/submit   │
     ▼                                 ▼
   [User interacts]          [Backend processes]
```

### 3. CI/CD Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    SOURCE CODE REPOSITORY                        │
│                      GitHub (main branch)                        │
└────────────┬────────────────┬──────────────────────┬─────────────┘
             │                │                      │
   ┌─────────▼──────┐  ┌──────▼──────┐  ┌──────────▼──────────┐
   │ Push to        │  │ Push to     │  │   CodeQL            │
   │ backend/**     │  │ frontend/** │  │   Security Scan     │
   └─────────┬──────┘  └──────┬──────┘  └──────────┬──────────┘
             │                │                      │
┌────────────▼────────────────▼──────────────────────▼─────────────┐
│                    GITHUB ACTIONS CI/CD                          │
│                                                                   │
│  ┌────────────────────────────┐  ┌──────────────────────────┐   │
│  │  Backend Pipeline          │  │  Frontend Pipeline       │   │
│  │  (.github/workflows/       │  │  (.github/workflows/     │   │
│  │   deploy-backend.yml)      │  │   deploy-frontend.yml)   │   │
│  │                            │  │                          │   │
│  │  Steps:                    │  │  Steps:                  │   │
│  │  1. Checkout code          │  │  1. Checkout code        │   │
│  │  2. Setup Python 3.13      │  │  2. Setup Node.js 20     │   │
│  │  3. Install dependencies   │  │  3. npm ci               │   │
│  │  4. Flake8 (style check)   │  │  4. ESLint               │   │
│  │  5. Pylint (static check)  │  │  5. Vitest (6 tests)     │   │
│  │  6. Django tests (9 tests) │  │  6. Create .env.prod     │   │
│  │  7. Auth to GCP            │  │  7. npm run build        │   │
│  │  8. Setup gcloud SDK       │  │  8. Upload artifact      │   │
│  │  9. Configure Docker Auth  │  │  9. Deploy to GH Pages   │   │
│  │ 10. Build Docker image     │  │                          │   │
│  │ 11. Trivy security scan    │  │  Output:                 │   │
│  │ 12. Push to Artifact Reg   │  │  - Static site on        │   │
│  │ 13. Deploy to Cloud Run    │  │    GitHub Pages          │   │
│  │ 14. Output service URL     │  │  - VITE_API_URL set      │   │
│  │                            │  │    from secrets          │   │
│  │  Output:                   │  │                          │   │
│  │  - Image: us-central1-     │  └──────────┬───────────────┘   │
│  │    docker.pkg.dev/.../     │             │                   │
│  │    backend:SHA             │             │                   │
│  │  - Cloud Run service URL   │             │                   │
│  └──────────┬─────────────────┘             │                   │
└─────────────┼───────────────────────────────┼───────────────────┘
              │                               │
              ▼                               ▼
┌──────────────────────────┐    ┌────────────────────────────┐
│  Google Cloud Platform   │    │      GitHub Pages          │
│  - Artifact Registry     │    │  - Static hosting          │
│  - Cloud Run Service     │    │  - CDN distribution        │
│    (Backend API)         │    │  - HTTPS by default        │
│  - Secret Manager        │    │  - URL: jothep.github.io/  │
│  - Cloud SQL (Postgres)  │    │    maori-story-fill        │
└──────────────────────────┘    └────────────────────────────┘
```

### 4. Kubernetes Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      KUBERNETES CLUSTER                          │
│                     (Namespace: story-fill)                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Ingress Controller                        │ │
│  │  (nginx.ingress.kubernetes.io)                             │ │
│  │  - SSL/TLS Termination                                     │ │
│  │  - Path-based routing                                      │ │
│  │  - Body size limit: 150MB                                  │ │
│  └───────┬────────────────────────────────────────────────────┘ │
│          │                                                       │
│  ┌───────▼─────────────────────────────────────────────┐        │
│  │  Ingress Resource (maori-story-ingress)             │        │
│  │  Rules:                                             │        │
│  │  - / → frontend-svc:80                              │        │
│  │  - /api/ → backend-svc:80                           │        │
│  │  - /admin/ → backend-svc:80                         │        │
│  │  - /static/ → backend-svc:80                        │        │
│  │  - /media/ → backend-svc:80                         │        │
│  └───────┬──────────────────────┬──────────────────────┘        │
│          │                      │                               │
│  ┌───────▼───────────┐  ┌───────▼────────────┐                 │
│  │  frontend-svc     │  │  backend-svc       │                 │
│  │  (ClusterIP)      │  │  (ClusterIP)       │                 │
│  │  Port: 80         │  │  Port: 80 → 8000   │                 │
│  └───────┬───────────┘  └───────┬────────────┘                 │
│          │                      │                               │
│  ┌───────▼───────────┐  ┌───────▼────────────┐                 │
│  │  Frontend         │  │  Backend           │                 │
│  │  Deployment       │  │  Deployment        │                 │
│  │  Replicas: 1      │  │  Replicas: 1       │                 │
│  │                   │  │                    │                 │
│  │  ┌─────────────┐  │  │  ┌──────────────┐ │                 │
│  │  │   Pod       │  │  │  │   Pod        │ │                 │
│  │  │  Image:     │  │  │  │  Image:      │ │                 │
│  │  │  jasko/     │  │  │  │  jasko/      │ │                 │
│  │  │  frontend:  │  │  │  │  backend:    │ │                 │
│  │  │  v1         │  │  │  │  v0.2        │ │                 │
│  │  │             │  │  │  │              │ │                 │
│  │  │  nginx:80   │  │  │  │  django:8000 │ │                 │
│  │  └─────────────┘  │  │  └──────┬───────┘ │                 │
│  └───────────────────┘  │         │         │                 │
│                         │  ┌──────▼───────┐ │                 │
│                         │  │ Volume Mount │ │                 │
│                         │  │ /app/media   │ │                 │
│                         │  └──────┬───────┘ │                 │
│                         │         │         │                 │
│                         └─────────┼─────────┘                 │
│                                   │                            │
│  ┌────────────────────────────────▼──────────────────────┐    │
│  │  PersistentVolumeClaim (maori-story-media-pvc)       │    │
│  │  AccessMode: ReadWriteOnce                           │    │
│  │  Storage: 5Gi                                        │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  StatefulSet: postgres-statefulset                     │   │
│  │  Replicas: 1                                           │   │
│  │                                                         │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  Pod: postgres-statefulset-0                     │  │   │
│  │  │  Image: postgres:16.10-alpine3.22                │  │   │
│  │  │  Port: 5432                                      │  │   │
│  │  │  Resources:                                      │  │   │
│  │  │    requests: 256Mi mem, 250m CPU                 │  │   │
│  │  │    limits: 1Gi mem, 1000m CPU                    │  │   │
│  │  │                                                   │  │   │
│  │  │  Probes:                                         │  │   │
│  │  │    readiness: pg_isready (20s delay)            │  │   │
│  │  │    liveness: pg_isready (60s delay)             │  │   │
│  │  │                                                   │  │   │
│  │  │  ┌────────────────────────────────────┐         │  │   │
│  │  │  │  Volume: postgres-data             │         │  │   │
│  │  │  │  Mount: /var/lib/postgresql/data   │         │  │   │
│  │  │  └────────────────────────────────────┘         │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │  Service: postgres-svc (ClusterIP:5432)                │   │
│  │  VolumeClaimTemplate: 5Gi                              │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Secrets                                               │   │
│  │  - postgres-secret (DB credentials)                    │   │
│  │  - maori-story-backend-secrets (env vars)              │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Jobs (One-time)                                       │   │
│  │  - backend-migrate-job (DB migrations)                 │   │
│  │  - backend-create-superuser-job (Admin user)           │   │
│  └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 3.1 Frontend Service

**Technology**: React 19 + Vite + nginx:alpine

**Responsibilities**:
- Serve Single Page Application
- Client-side routing (React Router)
- Interactive UI with drag-and-drop (dnd-kit)
- Background music player (custom hook)
- NES.css retro styling

**Key Files**:
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Menu.jsx          # Main menu (177 lines)
│   │   ├── StoryPage.jsx     # Story interaction
│   │   └── Congratulations.jsx
│   ├── components/
│   │   ├── InfoCredits.jsx   # Credits modal (136 lines)
│   │   ├── Roll.jsx          # Background animation
│   │   ├── LoadingSpinner.jsx
│   │   └── ErrorMessage.jsx
│   ├── hooks/
│   │   ├── useBgmPlayer.js   # Audio logic (100 lines)
│   │   └── useStories.js     # API data fetching
│   ├── constants/
│   │   ├── theme.js          # Design tokens (54 lines)
│   │   └── credits.js        # Content config (27 lines)
│   └── App.jsx               # Root component + routing
├── Dockerfile.nginx          # Multi-stage build
└── package.json              # Dependencies
```

**Dependencies** (Production):
- react: ^19.1.1
- react-dom: ^19.1.1
- react-router-dom: ^7.9.4
- @dnd-kit/core: ^6.3.1
- nes.css: ^2.2.1

**Build Process**:
1. `npm ci` - Install dependencies
2. `npm run lint` - ESLint checks
3. `npm test` - Vitest tests (6 tests)
4. `npm run build` - Vite production build
5. Docker multi-stage build:
   - Stage 1: Node.js build (~800MB)
   - Stage 2: nginx:alpine serve (~20MB final)

**Container**:
- **Image**: jasko/maori-story-frontend:v1
- **Base**: nginx:alpine
- **Size**: ~20MB
- **Port**: 80
- **CPU/Memory**: Not limited (lightweight static server)

**Environment Variables**:
- `VITE_API_URL`: Backend API endpoint (set at build time)

---

### 3.2 Backend Service

**Technology**: Django 5.2 + Django REST Framework + Gunicorn

**Responsibilities**:
- RESTful API endpoints
- Database ORM (Django models)
- Admin interface (Django admin)
- Media file management (images, audio)
- Static file serving (WhiteNoise)
- Optional S3 storage integration

**Key Modules**:
```
backend/
├── maori_story_project/
│   ├── settings.py           # Django configuration
│   ├── urls.py               # URL routing
│   └── wsgi.py               # WSGI entry point
├── story/
│   ├── models.py             # Story, Paragraph, Word, AppConfig
│   ├── serializers.py        # DRF serializers
│   ├── views.py              # API views
│   ├── admin.py              # Django admin config
│   └── tests.py              # 9 backend tests
├── media/                    # User-uploaded files (PVC mount)
├── staticfiles/              # Collected static assets
├── logs/                     # Application logs
├── requirements.txt          # Python dependencies
└── dockerfile                # Container build
```

**API Endpoints**:
- `GET /api/stories/` - List all stories
- `GET /api/stories/{id}/` - Story detail with paragraphs/words
- `GET /api/config/` - App configuration (e.g., BGM path)
- `GET /admin/` - Django admin panel
- `GET /media/*` - Media files (images, audio)
- `GET /static/*` - Static assets (CSS, JS)

**Dependencies** (Production):
- django: 5.2.13
- djangorestframework: 3.16.1
- django-cors-headers: 4.9.0
- gunicorn: 23.0.0 (WSGI server)
- psycopg2-binary: 2.9.11 (PostgreSQL driver)
- pillow: 12.2.0 (image processing)
- django-storages[google]: 1.14.4 (S3 support)
- whitenoise: 6.11.0 (static files)
- gevent: 25.9.1 (async workers)

**Container**:
- **Image**: jasko/maori-story-backend:v0.2
- **Base**: python:3.13-slim
- **Size**: ~300MB
- **Port**: 8000
- **Command**: `gunicorn maori_story_project.wsgi:application --bind 0.0.0.0:8000 --workers 3 --worker-class gevent`

**Environment Variables**:
- `DATABASE_URL`: PostgreSQL connection string
- `DJANGO_SECRET_KEY`: Secret key for Django
- `DJANGO_DEBUG`: Debug mode (False in production)
- `ALLOWED_HOSTS`: Comma-separated allowed hosts
- `USE_S3`: Enable S3 storage (optional)
- `AWS_*` / `MINIO_*`: S3 configuration (if USE_S3=true)

**Storage Options**:
1. **Local**: `/app/media` (PersistentVolumeClaim)
2. **MinIO**: Self-hosted S3-compatible storage
3. **AWS S3**: Cloud object storage

**Database Optimizations**:
- `select_related()` for foreign keys (reduce N+1 queries)
- `prefetch_related()` for reverse relations
- Query reduction: 35+ queries → 5-6 queries (85% improvement)

**Media File Processing**:
- Auto-resize images to max 1920x1080
- Compress to 85% quality
- Validate file size (10MB images, 20MB audio)
- Validate file extensions

---

### 3.3 Database Service

**Technology**: PostgreSQL 16 (Alpine)

**Responsibilities**:
- Persistent data storage
- Relational data integrity
- ACID transactions
- Full-text search (future)

**Schema Overview**:
```sql
-- Core Models
story_story
├── id (PK)
├── title
└── description

story_paragraph
├── id (PK)
├── story_id (FK → story_story)
├── order
├── original_text
└── audio_file

story_word
├── id (PK)
├── story_id (FK → story_story)
├── paragraph_id (FK → story_paragraph, nullable)
├── word_text
├── word_type (MAORI / EXTRA)
└── order

story_storypicture
├── id (PK)
├── story_id (FK → story_story)
└── picture

story_appconfig
├── id (PK)
├── key (unique)
├── value
└── description
```

**Configuration**:
- **Image**: postgres:16.10-alpine3.22
- **Port**: 5432
- **Database**: django_db
- **Storage**: 5Gi PersistentVolume (ReadWriteOnce)
- **Resources**:
  - Requests: 256Mi memory, 250m CPU
  - Limits: 1Gi memory, 1000m CPU

**Health Checks**:
- **Readiness**: `pg_isready -d django_db -U postgres` (20s initial delay)
- **Liveness**: `pg_isready -d django_db -U postgres` (60s initial delay)

**Backup Strategy**:
- Manual: `pg_dump` to local file
- Automated: Kubernetes CronJob (future)
- Volume snapshots (cloud provider)

---

### 3.4 Ingress / Load Balancer

**Technology**: Nginx Ingress Controller / Cloud Load Balancer

**Responsibilities**:
- SSL/TLS termination
- Path-based routing
- Request size limits
- Rate limiting (future)
- CORS handling (delegated to backend)

**Routing Rules**:
| Path Pattern | Backend Service | Purpose |
|-------------|-----------------|---------|
| `/` | frontend-svc:80 | React SPA |
| `/api/*` | backend-svc:80 | REST API |
| `/admin/*` | backend-svc:80 | Django admin |
| `/static/*` | backend-svc:80 | CSS, JS, images |
| `/media/*` | backend-svc:80 | User uploads |

**Configuration**:
```yaml
annotations:
  nginx.ingress.kubernetes.io/proxy-body-size: "150m"
```

---

## Deployment Architectures

> **⭐ CURRENT PRODUCTION**: See [architecture-production-gcp.md](architecture-production-gcp.md) for complete details

### 4.1 Production Deployment (Google Cloud Platform) - CURRENT ⭐

**Services Used**:
1. **GitHub Pages** (Frontend)
   - Static site hosting with global CDN
   - HTTPS by default
   - **Cost**: FREE (unlimited for public repos)

2. **Cloud Run** (Backend)
   - Serverless container platform
   - Auto-scaling (0-100 instances)
   - Managed SSL certificates
   - **Cost**: FREE tier 2M requests/month

3. **Neon PostgreSQL** (Database) ⭐ NEW
   - Serverless PostgreSQL 16
   - Auto-suspend after 5min idle
   - Point-in-time restore (7 days)
   - Built-in connection pooling
   - **Cost**: FREE tier 500MB storage

4. **Cloud Storage** (Media Files)
   - Images and audio files
   - Public access for `/media/*`
   - **Cost**: $0.02/GB/month (~$0.01/month current usage)

5. **Artifact Registry** (Container Images)
   - Docker image storage
   - Trivy vulnerability scanning
   - **Cost**: FREE tier 0.5GB

6. **Secret Manager** (Secrets)
   - DATABASE_URL, API keys
   - Encrypted at rest
   - **Cost**: FREE tier 6 secrets

**Architecture**:
```
[User] → [GitHub Pages CDN] → [Cloud Run API] → [Neon PostgreSQL]
                                      ↓
                               [Cloud Storage]
                                      ↓
                              [Secret Manager]
```

**Total Monthly Cost**: **$0 - $0.01** (essentially free) 🎉

**Scaling Characteristics**:
- **Current**: ~5K requests/month, 100MB database, 10MB storage
- **Free Tier Limits**: 2M requests/month, 500MB database, unlimited storage
- **Headroom**: 400x capacity before hitting limits

**Full Documentation**: [architecture-production-gcp.md](architecture-production-gcp.md)

---

### 4.2 Kubernetes Deployment (Self-hosted / Oracle Cloud)

**Cluster Setup**:
- **Platform**: Any Kubernetes 1.25+
- **Nodes**: 1-3 worker nodes (t3.small or equivalent)
- **Namespace**: `story-fill`
- **Ingress**: nginx-ingress-controller

**Resources**:
```
Frontend:  1 replica × 50Mi mem = 50Mi
Backend:   1 replica × 512Mi mem = 512Mi
Postgres:  1 replica × 1Gi mem = 1Gi
---------------------------------------
Total:     ~1.5Gi memory minimum
```

**Storage**:
- **media-pvc**: 5Gi ReadWriteOnce (backend media files)
- **postgres-data**: 5Gi ReadWriteOnce (database storage)

**Deployment Process**:
1. Create namespace: `kubectl create namespace story-fill`
2. Create secrets: `kubectl create secret generic postgres-secret ...`
3. Apply PVC: `kubectl apply -f Infra/pvc.yaml`
4. Deploy PostgreSQL: `kubectl apply -f Infra/postgres-deployment.yaml`
5. Run migrations: `kubectl apply -f Infra/backend-migrate-job.yaml`
6. Deploy backend: `kubectl apply -f Infra/backend-deployment.yaml`
7. Deploy frontend: `kubectl apply -f Infra/frontend-deployment.yaml`
8. Deploy ingress: `kubectl apply -f Infra/ingress.yaml`

---

### 4.3 Docker Compose Deployment (Single Server)

**Use Case**: Development, small-scale production, personal hosting

**Services**:
- nginx: Reverse proxy (ports 80, 443)
- frontend: React SPA
- backend: Django API
- db: PostgreSQL 16

**File**: `docker-compose.prod.yml`

**Deployment**:
```bash
# Set environment variables
export DB_PASSWORD=<secure-password>
export DJANGO_SECRET_KEY=<secure-key>

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create admin user
docker-compose exec backend python manage.py createsuperuser
```

**Volumes**:
- `postgres_data`: Database storage
- `media_data`: Media files
- `static_data`: Static assets

**Networking**:
- All services on `maori-network` bridge network
- Only nginx exposes ports (80, 443)

---

## Technology Stack

### 5.1 Frontend Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| UI Framework | React | 19.1.1 | Component-based UI |
| Build Tool | Vite | 7.1.7 | Fast build & HMR |
| Routing | React Router | 7.9.4 | Client-side routing |
| Styling | NES.css | 2.2.1 | Retro 8-bit theme |
| Drag-n-Drop | @dnd-kit/core | 6.3.1 | Interactive UI |
| Testing | Vitest | 3.2.4 | Unit & component tests |
| Linting | ESLint | 9.38.0 | Code quality |
| Web Server | nginx | alpine | Static file serving |

**Browser Support**:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

### 5.2 Backend Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Framework | Django | 5.2.13 | Web framework |
| API | Django REST Framework | 3.16.1 | RESTful API |
| WSGI Server | Gunicorn | 23.0.0 | Production server |
| Worker Type | gevent | 25.9.1 | Async I/O |
| Database Driver | psycopg2 | 2.9.11 | PostgreSQL |
| Image Processing | Pillow | 12.2.0 | Media optimization |
| Storage | django-storages | 1.14.4 | S3 integration |
| Static Files | WhiteNoise | 6.11.0 | Static serving |
| CORS | django-cors-headers | 4.9.0 | Cross-origin |
| Testing | unittest | built-in | Unit tests |
| Linting | Flake8, Pylint | latest | Code quality |

---

### 5.3 Infrastructure Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Database | PostgreSQL | 16.10 | Relational DB |
| Container Runtime | Docker | 20.10+ | Containerization |
| Orchestration | Kubernetes | 1.25+ | Container orchestration |
| Ingress | Nginx Ingress | latest | Load balancing |
| CI/CD | GitHub Actions | - | Automation |
| Image Registry | Docker Hub / Artifact Registry | - | Image storage |
| Security Scan | Trivy | latest | Vulnerability scanning |
| Version Control | Git | 2.40+ | Source control |

---

## CI/CD Pipeline

### 6.1 Backend Pipeline

**Trigger**: Push to `backend/**` or manual dispatch

**Workflow File**: `.github/workflows/deploy-backend.yml`

**Stages**:

1. **Code Quality** (Parallel)
   - Flake8: Style checking (continue-on-error)
   - Pylint: Static analysis (fail-under 7.0, continue-on-error)
   - Purpose: Catch code smells, enforce standards

2. **Testing** (Sequential)
   - Run Django test suite (9 tests)
   - In-memory SQLite database
   - Exit code 1 on failure (blocks deployment)

3. **Build & Scan** (Sequential)
   - Authenticate to Google Cloud
   - Build Docker image (tag: SHA + latest)
   - Trivy security scan (exit on HIGH/CRITICAL)
   - Push to Artifact Registry

4. **Deploy** (Sequential)
   - Update Cloud Run service
   - Use new image (SHA tag)
   - Output service URL

**Environment Variables**:
- `GCP_REGION`: us-central1
- `GCP_PROJECT_ID`: jaskojothep
- `ARTIFACT_REGISTRY`: maori-story
- `SERVICE_NAME`: maori-story-backend

**Secrets Required**:
- `GCP_CREDENTIALS`: Service account JSON

**Duration**: ~5-8 minutes

---

### 6.2 Frontend Pipeline

**Trigger**: Push to `frontend/**` or manual dispatch

**Workflow File**: `.github/workflows/deploy-frontend.yml`

**Stages**:

1. **Build Job**
   - Checkout code
   - Setup Node.js 20
   - `npm ci` (clean install)
   - ESLint (fail on errors)
   - Vitest tests (6 tests, fail on errors)
   - Create `.env.production` (inject API URL)
   - `npm run build` (Vite production build)
   - Upload artifact (dist folder)

2. **Deploy Job**
   - Deploy to GitHub Pages
   - Output page URL

**Environment Variables**:
- `VITE_API_URL`: Injected from `secrets.CLOUD_RUN_URL`

**Secrets Required**:
- `CLOUD_RUN_URL`: Backend API endpoint

**Permissions**:
- `contents: read`
- `pages: write`
- `id-token: write`

**Duration**: ~3-5 minutes

---

### 6.3 Security Scanning (CodeQL)

**Trigger**: Push to main, scheduled weekly

**Workflow File**: `.github/workflows/codeql-analysis.yml`

**Purpose**:
- Static application security testing (SAST)
- Detect security vulnerabilities
- Find code quality issues

**Languages Analyzed**:
- JavaScript (frontend)
- Python (backend)

**Output**: Security alerts on GitHub Security tab

---

## Data Flow

### 7.1 Story Loading Flow

```
1. User navigates to https://app.example.com/
   ↓
2. Browser requests index.html from Frontend Service (nginx)
   ↓
3. React app initializes, renders Menu component
   ↓
4. useStories hook calls: GET /api/stories/
   ↓
5. Request routed via Ingress to Backend Service
   ↓
6. Django view queries PostgreSQL:
   SELECT * FROM story_story;
   ↓
7. Serializer formats data to JSON
   ↓
8. Response returns to frontend: {stories: [{id, title}, ...]}
   ↓
9. React renders story list (NES.css styled buttons)
   ↓
10. User clicks story button
   ↓
11. React Router navigates to /story/:id
   ↓
12. StoryPage component calls: GET /api/stories/:id/
   ↓
13. Backend queries with optimizations:
    - select_related('story')
    - prefetch_related('paragraphs', 'words')
   ↓
14. Response includes full story data:
    {
      story: {id, title, pictures: [...]},
      paragraphs: [{id, text, audio, words: [...]}],
      words: [{id, text, type, paragraph_id}]
    }
   ↓
15. React renders interactive story page:
    - Paragraph slots (dnd-kit drop zones)
    - Word bank (dnd-kit draggables)
    - Audio player for each paragraph
```

---

### 7.2 Media File Flow

```
1. Admin uploads audio file via Django admin
   ↓
2. Django model save() method triggers:
   - Validate file size (< 20MB)
   - Validate extension (.mp3, .wav, .ogg)
   ↓
3. File saved to storage:
   - Local: /app/media/audio/file.mp3 (PVC)
   - S3: s3://bucket/media/audio/file.mp3
   ↓
4. Database record updated with file path
   ↓
5. User requests story, gets paragraph data with audio_file URL
   ↓
6. Browser requests: GET /media/audio/file.mp3
   ↓
7. Ingress routes to Backend Service
   ↓
8. Django serves file:
   - Local: Read from PVC, stream response
   - S3: Generate signed URL, redirect (or proxy)
   ↓
9. Browser receives audio file, plays via HTML5 Audio API
```

---

### 7.3 Configuration Flow (BGM Example)

```
1. Admin sets BGM path in Django admin:
   - Key: menu_bgm_path
   - Value: /media/bgm/Schumann_Fantasy.mp3
   ↓
2. Frontend loads Menu page
   ↓
3. useBgmPlayer hook calls: GET /api/config/?key=menu_bgm_path
   ↓
4. Backend queries: AppConfig.objects.get(key='menu_bgm_path')
   ↓
5. Returns JSON: {key: 'menu_bgm_path', value: '/media/bgm/...'}
   ↓
6. Hook constructs full URL:
   - Dev: http://localhost:8000/media/bgm/...
   - Prod: https://api.example.com/media/bgm/...
   ↓
7. Creates Audio element: new Audio(url)
   ↓
8. Attempts autoplay (may be blocked by browser MEI)
   ↓
9. If blocked: Shows hint "Click to start music ⇑"
   ↓
10. User clicks BGM checkbox → toggleMusic() → audio.play()
```

---

## Security Architecture

### 8.1 Authentication & Authorization

**Current Implementation**:
- Django admin: Session-based authentication
- API endpoints: Public (no authentication required)

**Future Enhancements** (Recommended):
- JWT tokens for API authentication
- OAuth2 for social login
- User accounts for progress tracking

---

### 8.2 Data Security

**In Transit**:
- ✅ HTTPS enforced via Ingress/Cloud Run
- ✅ TLS 1.2+ minimum
- ✅ CORS policies configured

**At Rest**:
- ✅ Database encryption (managed by cloud provider)
- ✅ Volume encryption (Kubernetes PVC)
- ✅ Secret encryption (Kubernetes secrets, base64)

**Secrets Management**:
- ✅ Environment variables (not committed to git)
- ✅ Kubernetes secrets (base64 encoded)
- ✅ GCP Secret Manager (Cloud Run)
- ❌ TODO: Rotate secrets regularly

---

### 8.3 Input Validation

**Backend**:
- ✅ Django form validation
- ✅ DRF serializer validation
- ✅ File type validation (images, audio)
- ✅ File size limits (10MB images, 20MB audio)
- ✅ SQL injection protection (Django ORM)

**Frontend**:
- ✅ React prop-types validation
- ✅ Input sanitization (React escapes by default)
- ✅ XSS protection (no dangerouslySetInnerHTML)

---

### 8.4 Dependency Security

**Process**:
1. **Automated Scanning**
   - Trivy: Docker image vulnerabilities (CI/CD)
   - npm audit: JavaScript package vulnerabilities
   - pip-audit: Python package vulnerabilities (future)

2. **Regular Updates**
   - Dependency updates tracked in CHANGELOG.md
   - Security patches applied promptly
   - Test suite run after updates

3. **Recent Fixes** (2026-03):
   - Django 5.2.7 → 5.2.13 (9 CVEs)
   - Pillow 11.3.0 → 12.2.0 (1 CVE)
   - Frontend npm packages (10 packages updated)
   - Docker base images (Alpine package updates)

---

### 8.5 Rate Limiting & DoS Protection

**Current**:
- ❌ No rate limiting implemented

**Recommended**:
- Nginx rate limiting (req/s per IP)
- Django Ratelimit middleware
- Cloud provider DDoS protection
- Request body size limit: 150MB (configured)

---

## Scalability & Performance

### 9.1 Horizontal Scaling

**Frontend**:
- ✅ Stateless (can scale to N replicas)
- ✅ Served from CDN (GitHub Pages)
- ✅ Small image size (~20MB)

**Backend**:
- ✅ Stateless (except media files on PVC)
- ⚠️ Media on PVC: Use ReadWriteMany or migrate to S3
- ✅ Database connection pooling (future)
- ✅ Can scale to N replicas with S3 storage

**Database**:
- ❌ Single instance (StatefulSet replicas: 1)
- 🔄 Future: Read replicas for query scaling
- 🔄 Future: Connection pooling (PgBouncer)

---

### 9.2 Caching Strategy

**Current**:
- ❌ No caching implemented

**Recommended**:
1. **Browser Caching**
   - Static assets: `Cache-Control: public, max-age=31536000`
   - API responses: `Cache-Control: max-age=300` (5 min)

2. **Server-side Caching**
   - Redis: API response caching
   - Django cache framework
   - Database query caching

3. **CDN Caching**
   - Frontend assets (GitHub Pages CDN)
   - Media files (CloudFront / Cloud CDN)

---

### 9.3 Database Optimization

**Implemented**:
- ✅ `select_related()`: Reduce JOIN queries (35+ → 5-6)
- ✅ `prefetch_related()`: Optimize reverse relations
- ✅ Database indexes on foreign keys

**Future Enhancements**:
- Add indexes on frequently queried fields
- Implement full-text search (PostgreSQL FTS)
- Partition large tables (if needed)
- Query result caching (Redis)

---

### 9.4 Performance Metrics

**Load Testing** (Future):
- Concurrent users: Target 100 simultaneous users
- Response time: < 200ms (API), < 1s (page load)
- Throughput: 100 req/s minimum

**Monitoring** (Future):
- Prometheus + Grafana
- Application Performance Monitoring (APM)
- Real User Monitoring (RUM)

---

## Monitoring & Logging

### 10.1 Application Logging

**Backend Logging**:
```python
# Configured in settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        }
    },
    'loggers': {
        'story': {
            'handlers': ['file'],
            'level': 'INFO',
        }
    }
}
```

**Log Levels**:
- INFO: Successful operations, requests
- WARNING: Recoverable errors, missing files
- ERROR: Failed operations, exceptions
- CRITICAL: System failures

**Log Locations**:
- Local: `backend/logs/django.log`
- Kubernetes: `kubectl logs <pod-name>`
- Cloud Run: Google Cloud Logging

---

### 10.2 Health Checks

**Backend**:
- Endpoint: `/admin/` (Django admin as health check)
- Kubernetes readiness: Not configured
- Kubernetes liveness: Not configured

**Database**:
- Readiness: `pg_isready -d django_db -U postgres` (20s delay)
- Liveness: `pg_isready -d django_db -U postgres` (60s delay)

**Recommended**:
- Add `/health/` endpoint (backend)
- Return JSON: `{status: 'ok', database: 'connected', storage: 'ok'}`

---

### 10.3 Metrics Collection (Future)

**Infrastructure Metrics**:
- CPU usage per pod
- Memory usage per pod
- Network I/O
- Disk I/O

**Application Metrics**:
- Request count (by endpoint)
- Response time (by endpoint)
- Error rate (4xx, 5xx)
- Database query time

**Business Metrics**:
- Active users
- Stories completed
- Most popular stories
- Average completion time

**Tools**:
- Prometheus: Metrics collection
- Grafana: Dashboards
- Alertmanager: Alerting rules

---

### 10.4 Error Tracking (Future)

**Recommended Tools**:
- Sentry: Application error tracking
- Rollbar: Real-time error monitoring
- Google Cloud Error Reporting

**Integration**:
```python
# Backend (Django + Sentry)
import sentry_sdk
sentry_sdk.init(dsn="...")

# Frontend (React + Sentry)
import * as Sentry from "@sentry/react";
Sentry.init({dsn: "..."});
```

---

## Appendix

### A. Architecture Diagram Code (Mermaid)

Save the following code as `architecture.mermaid` and render with Mermaid:

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Browser<br/>Desktop/Mobile]
    end

    subgraph "Ingress Layer"
        Ingress[Nginx Ingress<br/>SSL/TLS, Routing]
    end

    subgraph "Application Layer"
        Frontend[Frontend Service<br/>React + nginx<br/>Port 80]
        Backend[Backend Service<br/>Django + Gunicorn<br/>Port 8000]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL 16<br/>StatefulSet<br/>Port 5432)]
        PVC[PersistentVolume<br/>Media Files<br/>5Gi]
    end

    Browser -->|HTTPS| Ingress
    Ingress -->|/ → SPA| Frontend
    Ingress -->|/api/*, /admin/*| Backend
    Ingress -->|/media/*, /static/*| Backend
    Backend -->|SQL Queries| DB
    Backend -->|Read/Write| PVC

    style Browser fill:#e1f5ff
    style Ingress fill:#fff9c4
    style Frontend fill:#c8e6c9
    style Backend fill:#c8e6c9
    style DB fill:#ffccbc
    style PVC fill:#ffccbc
```

### B. CI/CD Pipeline Code (Mermaid)

```mermaid
graph LR
    A[Push to main] --> B{Changed Files?}
    B -->|backend/**| C[Backend Pipeline]
    B -->|frontend/**| D[Frontend Pipeline]
    
    C --> C1[Flake8 + Pylint]
    C1 --> C2[Django Tests]
    C2 --> C3[Build Docker]
    C3 --> C4[Trivy Scan]
    C4 --> C5[Push to Registry]
    C5 --> C6[Deploy Cloud Run]
    
    D --> D1[ESLint]
    D1 --> D2[Vitest Tests]
    D2 --> D3[Build Vite]
    D3 --> D4[Upload Artifact]
    D4 --> D5[Deploy GH Pages]
    
    style A fill:#e1f5ff
    style C fill:#c8e6c9
    style D fill:#c8e6c9
    style C6 fill:#fff9c4
    style D5 fill:#fff9c4
```

### C. Data Model Diagram (Mermaid)

```mermaid
erDiagram
    STORY ||--o{ PARAGRAPH : contains
    STORY ||--o{ WORD : "has words"
    STORY ||--o{ STORY_PICTURE : "has pictures"
    PARAGRAPH ||--o{ WORD : "words in paragraph"
    
    STORY {
        int id PK
        string title
        text description
    }
    
    PARAGRAPH {
        int id PK
        int story_id FK
        int order
        text original_text
        file audio_file
    }
    
    WORD {
        int id PK
        int story_id FK
        int paragraph_id FK "nullable"
        string word_text
        string word_type "MAORI/EXTRA"
        int order
    }
    
    STORY_PICTURE {
        int id PK
        int story_id FK
        file picture
    }
    
    APP_CONFIG {
        int id PK
        string key "unique"
        string value
        text description
    }
```

---

### D. Deployment Comparison Matrix

| Feature | Kubernetes | Cloud Run | Docker Compose |
|---------|-----------|-----------|----------------|
| **Complexity** | High | Low | Medium |
| **Cost** | Variable | Low (pay-per-use) | Fixed (server cost) |
| **Scalability** | Excellent | Excellent | Poor |
| **Management** | Self-managed | Fully managed | Self-managed |
| **Storage** | PVC (5Gi) | Cloud Storage | Docker volumes |
| **Database** | Self-hosted PG | Cloud SQL | Self-hosted PG |
| **SSL** | Cert-manager | Automatic | Manual (Let's Encrypt) |
| **Use Case** | Production (self-hosted) | Production (cloud) | Dev / Small prod |
| **Monthly Cost** | $10-50 (nodes) | $0-10 (usage) | $5-20 (VPS) |

---

### E. Port Reference

| Service | Internal Port | External Port | Protocol |
|---------|--------------|---------------|----------|
| Frontend | 80 | 80 (via Ingress) | HTTP |
| Backend | 8000 | 80 (via Service) | HTTP |
| PostgreSQL | 5432 | 5432 (ClusterIP) | PostgreSQL |
| Nginx (Docker Compose) | 80, 443 | 80, 443 | HTTP/HTTPS |

---

### F. Environment Variables Reference

#### Backend
```bash
# Required
DATABASE_URL=postgresql://user:${DB_PASSWORD}@host:5432/db
DJANGO_SECRET_KEY=<random-50-char-string>
ALLOWED_HOSTS=example.com,api.example.com

# Optional
DJANGO_DEBUG=False
USE_S3=false
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_STORAGE_BUCKET_NAME=<bucket>
AWS_S3_REGION_NAME=us-east-1
```

#### Frontend
```bash
# Build-time only
VITE_API_URL=https://api.example.com
```

---

### G. Useful Commands

#### Kubernetes
```bash
# Deploy all services
kubectl apply -f Infra/

# Check pod status
kubectl get pods -n story-fill

# View logs
kubectl logs -n story-fill <pod-name> -f

# Execute command in pod
kubectl exec -n story-fill <pod-name> -it -- /bin/bash

# Port forward for testing
kubectl port-forward -n story-fill svc/maori-story-backend-svc 8000:80
```

#### Docker Compose
```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend python manage.py migrate

# Restart service
docker-compose restart backend
```

#### Django Management
```bash
# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-01 | Initial architecture documentation |

---

**Document End**
