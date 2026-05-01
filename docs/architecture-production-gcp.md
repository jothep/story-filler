# Production Architecture - GCP Cloud Platform

**Current Production Deployment**  
**Last Updated**: 2026-05-01  
**Stack**: GitHub Pages + Google Cloud Run + Neon PostgreSQL

---

## Architecture Overview

This document describes the **current production architecture** running on Google Cloud Platform with serverless components.

**Key Characteristics**:
- ✅ **Fully Serverless**: No server management required
- ✅ **Cost-Effective**: $0/month (free tiers)
- ✅ **Auto-Scaling**: Scales from 0 to N instances automatically
- ✅ **Global CDN**: GitHub Pages provides worldwide distribution
- ✅ **Managed Database**: Neon provides serverless PostgreSQL

---

## High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[🌐 Web Browser<br/>Desktop / Mobile / Tablet<br/>Any modern browser]
    end

    subgraph "CDN & Static Hosting"
        GHPages[📄 GitHub Pages<br/>Domain: jothep.github.io/maori-story-fill<br/>React SPA + Static Assets<br/>Global CDN<br/>HTTPS by default<br/>Cost: FREE]
    end

    subgraph "Google Cloud Platform"
        direction TB
        
        subgraph "Container Registry"
            ArtifactRegistry[📦 Artifact Registry<br/>us-central1-docker.pkg.dev<br/>Docker Images<br/>Trivy Security Scanning<br/>Cost: FREE 0.5GB storage]
        end
        
        subgraph "Compute"
            CloudRun[🚀 Cloud Run Service<br/>Name: maori-story-backend<br/>Region: us-central1<br/>Django 5.2 + Gunicorn<br/>Min: 0 instances<br/>Max: 100 instances<br/>Port: 8000<br/>Memory: 512Mi<br/>CPU: 1 vCPU<br/>Concurrency: 80<br/>Cost: FREE 2M requests/month]
        end
        
        subgraph "Storage"
            GCS[☁️ Cloud Storage<br/>Bucket: maori-story-media<br/>Media files: images, audio<br/>Public access for /media/*<br/>Optional: CDN enabled<br/>Cost: ~$0.02/GB/month]
        end
        
        subgraph "Secrets Management"
            SecretManager[🔐 Secret Manager<br/>DATABASE_URL<br/>DJANGO_SECRET_KEY<br/>AWS_* credentials<br/>Encrypted at rest<br/>Cost: FREE 6 secrets]
        end
    end

    subgraph "Database Provider - Neon"
        NeonDB[(🐘 Neon PostgreSQL<br/>Serverless Database<br/>Region: US East Ohio<br/>Version: PostgreSQL 16<br/>Storage: 0.5GB used / 500MB free<br/>Auto-suspend after 5min idle<br/>Connection pooling built-in<br/>Cost: FREE tier)]
    end

    subgraph "CI/CD - GitHub Actions"
        direction LR
        BackendCI[⚙️ Backend Pipeline<br/>Test → Build → Scan → Deploy]
        FrontendCI[⚙️ Frontend Pipeline<br/>Test → Build → Deploy]
    end

    %% User Flow
    Browser -->|1. HTTPS Request<br/>GET /| GHPages
    GHPages -->|2. Serve index.html<br/>+ React bundle| Browser
    Browser -->|3. API Calls<br/>GET /api/stories/| CloudRun
    
    %% Backend Dependencies
    CloudRun -->|4. SQL Queries<br/>PostgreSQL protocol| NeonDB
    CloudRun -->|5. Read/Write Media<br/>S3 API| GCS
    CloudRun -->|6. Load Secrets<br/>At startup| SecretManager
    
    %% CI/CD Flow
    BackendCI -.->|Build & Push Image| ArtifactRegistry
    ArtifactRegistry -.->|Pull Image| CloudRun
    FrontendCI -.->|Deploy Static Site| GHPages

    %% Styling
    style Browser fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    style GHPages fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    style CloudRun fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    style NeonDB fill:#ffccbc,stroke:#d84315,stroke-width:3px
    style ArtifactRegistry fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px
    style GCS fill:#b3e5fc,stroke:#0277bd,stroke-width:2px
    style SecretManager fill:#f8bbd0,stroke:#c2185b,stroke-width:2px
    style BackendCI fill:#c5e1a5,stroke:#558b2f,stroke-width:2px
    style FrontendCI fill:#c5e1a5,stroke:#558b2f,stroke-width:2px
```

---

## Detailed Request Flow

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant GHPages as GitHub Pages<br/>(CDN)
    participant CloudRun as Cloud Run<br/>(Backend API)
    participant SecretMgr as Secret Manager
    participant Neon as Neon PostgreSQL
    participant GCS as Cloud Storage

    Note over User,GCS: Initial Page Load
    User->>Browser: Visit https://jothep.github.io/maori-story-fill/
    Browser->>GHPages: GET /
    GHPages-->>Browser: index.html (React SPA)
    Browser->>GHPages: GET /assets/*.js, *.css
    GHPages-->>Browser: Static assets (from CDN)
    Browser->>Browser: React app initializes

    Note over User,GCS: Fetch Stories List
    Browser->>CloudRun: GET /api/stories/<br/>Headers: Origin, Accept
    
    alt Cold Start (first request)
        CloudRun->>CloudRun: Start container instance
        CloudRun->>SecretMgr: Load DATABASE_URL, SECRET_KEY
        SecretMgr-->>CloudRun: Encrypted secrets
        CloudRun->>CloudRun: Initialize Django app
    end
    
    CloudRun->>Neon: SELECT * FROM story_story<br/>Connection pooling
    Neon-->>CloudRun: [{id:1, title:"..."}, ...]
    CloudRun-->>Browser: JSON: {stories: [...]}
    Browser->>Browser: Render story list (NES.css)

    Note over User,GCS: Load Story Details
    User->>Browser: Click story button
    Browser->>CloudRun: GET /api/stories/1/
    CloudRun->>Neon: SELECT with prefetch_related<br/>Story + Paragraphs + Words
    Neon-->>CloudRun: Complete story data
    CloudRun-->>Browser: JSON: {story, paragraphs, words}

    Note over User,GCS: Load Media Files
    Browser->>CloudRun: GET /media/bgm/music.mp3
    CloudRun->>GCS: Read from Cloud Storage bucket
    GCS-->>CloudRun: Audio file stream
    CloudRun-->>Browser: Audio file (binary)
    Browser->>Browser: HTML5 Audio API plays

    Browser->>CloudRun: GET /media/audio/paragraph1.mp3
    CloudRun->>GCS: Read from bucket
    GCS-->>Browser: Audio file (via signed URL or proxy)

    Note over User,GCS: After 5min Idle
    CloudRun->>CloudRun: Scale to zero (no cost)
    Neon->>Neon: Auto-suspend database (no cost)
```

---

## Component Details

### 1. Frontend - GitHub Pages

**Service**: GitHub Pages  
**URL**: https://jothep.github.io/maori-story-fill/  
**Technology**: React 19 SPA  

**Features**:
- ✅ Global CDN distribution (Fastly)
- ✅ Automatic HTTPS with GitHub certificate
- ✅ Zero server maintenance
- ✅ Instant deployments via GitHub Actions
- ✅ Custom domain support (optional)

**Build Process**:
```bash
# In GitHub Actions workflow
npm ci
npm run build  # Vite builds to /dist
# Output: Optimized HTML, JS, CSS bundles
```

**Configuration**:
```javascript
// vite.config.js
export default {
  base: '/maori-story-fill/',  // GitHub Pages subpath
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom']
        }
      }
    }
  }
}
```

**Environment Variables** (build-time):
```bash
VITE_API_URL=https://maori-story-backend-xxx-uc.a.run.app
```

**Cost**: **FREE** (unlimited bandwidth for public repos)

---

### 2. Backend - Google Cloud Run

**Service**: Cloud Run  
**Name**: `maori-story-backend`  
**Region**: `us-central1` (Iowa)  
**URL**: `https://maori-story-backend-xxx-uc.a.run.app`

**Container Configuration**:
```yaml
Platform: managed
Image: us-central1-docker.pkg.dev/jaskojothep/maori-story/backend:latest
Port: 8000
Memory: 512Mi
CPU: 1 vCPU
Min Instances: 0  # Scale to zero when idle
Max Instances: 100
Concurrency: 80  # Requests per instance
Timeout: 300s (5 minutes)
```

**Autoscaling Behavior**:
- **Cold Start**: ~5-10 seconds (includes Django app initialization)
- **Warm Instance**: <100ms response time
- **Scale to Zero**: After 15 minutes of no traffic
- **Scale Up**: Automatic based on request rate

**Environment Variables** (from Secret Manager):
```bash
DATABASE_URL=postgresql://user:${DB_PASSWORD}@ep-xxx.aws.neon.tech/neondb?sslmode=require
DJANGO_SECRET_KEY=xxx...
ALLOWED_HOSTS=maori-story-backend-xxx-uc.a.run.app,jothep.github.io
DJANGO_DEBUG=False
USE_S3=true
GS_BUCKET_NAME=maori-story-media
```

**Health Check**:
- Endpoint: `/admin/` (Django admin as health check)
- Interval: Not explicitly configured (Cloud Run default)

**CORS Configuration**:
```python
CORS_ALLOWED_ORIGINS = [
    'https://jothep.github.io',
]
CORS_ALLOW_CREDENTIALS = True
```

**Cost**: 
- **FREE Tier**: 2 million requests/month
- **Beyond Free**: $0.00002400 per request (~$2.40 per 100K requests)
- **Current Usage**: Well within free tier

---

### 3. Database - Neon PostgreSQL

**Provider**: Neon.tech  
**Type**: Serverless PostgreSQL  
**Version**: PostgreSQL 16  
**Region**: `us-east-2` (US East Ohio)

**Connection**:
```
postgresql://username:${DB_PASSWORD}@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Features**:
- ✅ **Auto-suspend**: Database pauses after 5 minutes of inactivity
- ✅ **Instant activation**: Resumes in <1 second on new query
- ✅ **Connection pooling**: Built-in, handles Django connections
- ✅ **Branching**: Create dev/staging branches (git-like)
- ✅ **Point-in-time restore**: Restore to any point in last 7 days
- ✅ **Automatic backups**: Daily backups included

**Storage**:
- **Used**: ~100MB (stories, paragraphs, words)
- **Free Tier**: 500MB storage
- **Shared compute**: 0.5 vCPU shared

**Performance**:
- **Query Time**: 10-50ms for optimized queries
- **Concurrent Connections**: Up to 100 (pooled)
- **Latency**: ~50ms from Cloud Run (same region recommended)

**Cost**: **FREE** (within 500MB storage limit)

---

### 4. Storage - Google Cloud Storage

**Bucket Name**: `maori-story-media`  
**Region**: `us-central1` (multi-region for CDN)  
**Storage Class**: Standard

**Contents**:
```
gs://maori-story-media/
├── bgm/
│   └── Schumann_Fantasy.mp3 (3.2MB)
├── audio/
│   ├── paragraph1.mp3
│   ├── paragraph2.mp3
│   └── ...
├── images/
│   ├── story1_pic1.jpg (compressed)
│   └── story2_pic1.jpg (compressed)
└── staticfiles/ (collected Django static files)
```

**Access Control**:
- Public read access for `/media/*` paths
- Signed URLs for temporary access (optional)
- CORS enabled for GitHub Pages origin

**Django Integration**:
```python
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = 'maori-story-media'
GS_PROJECT_ID = 'jaskojothep'
MEDIA_URL = 'https://storage.googleapis.com/maori-story-media/'
```

**Cost**:
- **Storage**: $0.020 per GB per month
- **Current**: ~10MB × $0.020 = **$0.0002/month**
- **Bandwidth**: $0.12 per GB (to internet)
- **Operations**: $0.005 per 10,000 Class A operations

**Total Estimated Cost**: **< $0.01/month**

---

### 5. Container Registry - Artifact Registry

**Registry**: `us-central1-docker.pkg.dev`  
**Repository**: `jaskojothep/maori-story`  
**Image**: `backend:latest` and `backend:<git-sha>`

**Security**:
- ✅ Trivy vulnerability scanning in CI/CD
- ✅ Exit on HIGH/CRITICAL vulnerabilities
- ✅ Immutable tags for production (SHA)
- ✅ Private registry (IAM-controlled access)

**Image Details**:
```
Image: us-central1-docker.pkg.dev/jaskojothep/maori-story/backend:latest
Size: ~300MB (compressed)
Base: python:3.13-slim
Layers: Multi-stage build optimized
```

**Cost**: **FREE** (first 0.5GB storage)

---

### 6. Secrets Management - Secret Manager

**Secrets Stored**:
1. `DATABASE_URL` - Neon PostgreSQL connection string
2. `DJANGO_SECRET_KEY` - Django secret key (50 chars)
3. `GCP_SERVICE_ACCOUNT_KEY` - For Cloud Storage access (optional)
4. `CLOUD_RUN_URL` - Backend URL (for frontend builds)

**Security**:
- ✅ Encrypted at rest (Google-managed keys)
- ✅ Audit logging enabled
- ✅ IAM-based access control
- ✅ Automatic rotation (manual trigger)

**Access from Cloud Run**:
```bash
# Mounted as environment variables at runtime
gcloud run services update maori-story-backend \
  --update-secrets=DATABASE_URL=database-url:latest \
  --update-secrets=DJANGO_SECRET_KEY=REMOVED_CREDENTIAL
```

**Cost**: **FREE** (first 6 secret versions free)

---

## CI/CD Pipeline

### Backend Deployment Flow

```mermaid
graph LR
    A[Git Push to main] --> B{backend/** changed?}
    B -->|Yes| C[GitHub Actions Trigger]
    C --> D[Run Tests<br/>9 Django tests]
    D --> E[Flake8 + Pylint]
    E --> F[Build Docker Image]
    F --> G[Trivy Security Scan]
    G --> H{Vulnerabilities?}
    H -->|HIGH/CRITICAL| I[❌ Fail Build]
    H -->|None/Low| J[Push to Artifact Registry]
    J --> K[Deploy to Cloud Run]
    K --> L[Update Service<br/>New revision]
    L --> M[✅ Live in ~2min]

    style A fill:#e1f5ff
    style D fill:#c8e6c9
    style G fill:#fff9c4
    style I fill:#ffcdd2
    style M fill:#c8e6c9
```

**Workflow File**: `.github/workflows/deploy-backend.yml`

**Key Steps**:
1. Checkout code
2. Setup Python 3.13
3. Run Django tests (must pass)
4. Build Docker image (tag: SHA + latest)
5. Scan with Trivy (block on HIGH/CRITICAL)
6. Push to Artifact Registry
7. Deploy to Cloud Run (new revision)
8. Traffic shifts to new revision (0% downtime)

**Duration**: ~5-8 minutes

---

### Frontend Deployment Flow

```mermaid
graph LR
    A[Git Push to main] --> B{frontend/** changed?}
    B -->|Yes| C[GitHub Actions Trigger]
    C --> D[npm ci Install]
    D --> E[ESLint Check]
    E --> F[Vitest Tests<br/>6 tests]
    F --> G[Create .env.production<br/>Inject API URL]
    G --> H[Vite Build<br/>npm run build]
    H --> I[Upload Artifact<br/>/dist folder]
    I --> J[Deploy to GitHub Pages]
    J --> K[✅ Live in ~1min]

    style A fill:#e1f5ff
    style F fill:#c8e6c9
    style H fill:#fff9c4
    style K fill:#c8e6c9
```

**Workflow File**: `.github/workflows/deploy-frontend.yml`

**Key Steps**:
1. Checkout code
2. Setup Node.js 20
3. Run tests (must pass)
4. Inject backend URL from secrets
5. Build with Vite
6. Deploy to `gh-pages` branch
7. GitHub Pages auto-publishes

**Duration**: ~3-5 minutes

---

## Data Flow Examples

### Example 1: User Loads Story List

```
1. User → https://jothep.github.io/maori-story-fill/
   ↓
2. GitHub Pages CDN → Serves index.html (cached globally)
   ↓
3. Browser executes React app
   ↓
4. API Call: GET https://maori-story-backend-xxx.run.app/api/stories/
   ↓
5. Cloud Run (cold start if needed):
   - Load secrets from Secret Manager
   - Initialize Django
   - Connect to Neon DB (resumes if suspended)
   ↓
6. Neon DB: SELECT * FROM story_story;
   ↓
7. Response: [{id:1, title:"..."}, {id:2, ...}]
   ↓
8. Browser renders story buttons
```

**Performance**:
- **Warm path**: ~100-200ms total
- **Cold start**: ~5-10 seconds first time
- **CDN cache hit**: ~20ms for HTML

---

### Example 2: Play Background Music

```
1. Menu page loads
   ↓
2. useBgmPlayer hook: GET /api/config/?key=menu_bgm_path
   ↓
3. Cloud Run: SELECT value FROM app_config WHERE key='menu_bgm_path'
   ↓
4. Response: {value: "/media/bgm/Schumann_Fantasy.mp3"}
   ↓
5. Browser requests: GET /media/bgm/Schumann_Fantasy.mp3
   ↓
6. Cloud Run proxies request to Cloud Storage
   ↓
7. Cloud Storage returns audio file (3.2MB)
   ↓
8. Browser plays via HTML5 Audio API
```

**Optimization Opportunity**:
- Use signed URLs to serve directly from GCS (bypass Cloud Run)
- Enable Cloud CDN for media files

---

## Cost Breakdown (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| **GitHub Pages** | Static hosting + CDN | **FREE** |
| **Cloud Run** | ~10K requests/month | **FREE** (within 2M limit) |
| **Neon PostgreSQL** | 100MB storage, auto-suspend | **FREE** (within 500MB limit) |
| **Cloud Storage** | 10MB storage, ~1GB egress | **< $0.01** |
| **Artifact Registry** | 300MB image | **FREE** (within 0.5GB limit) |
| **Secret Manager** | 4 secrets | **FREE** (within 6 secrets limit) |
| **GitHub Actions** | 2000 minutes/month | **FREE** (within public repo limits) |

**Total Monthly Cost**: **$0 - $0.01** 🎉

---

## Scaling Characteristics

### Current Capacity

| Metric | Current | Limit (Free Tier) | Paid Scaling |
|--------|---------|-------------------|--------------|
| **Concurrent Users** | ~10 | ~100 | Unlimited |
| **Requests/Month** | ~5K | 2M (Cloud Run) | $0.024 per 1K |
| **Database Size** | 100MB | 500MB | $0.10/GB/month |
| **Media Storage** | 10MB | Unlimited* | $0.020/GB/month |
| **Response Time** | 100-200ms (warm) | N/A | Same |

*Cloud Storage has no free tier, but cost is negligible at low usage.

### Horizontal Scaling

**Frontend**:
- ✅ Infinitely scalable (GitHub Pages CDN)
- ✅ Edge caching worldwide
- ✅ No action needed

**Backend (Cloud Run)**:
- ✅ Auto-scales 0-100 instances
- ✅ Each instance: 80 concurrent requests
- ✅ Max capacity: 8,000 concurrent requests
- ⚠️ Cold start latency for new instances

**Database (Neon)**:
- ⚠️ Shared compute on free tier
- ✅ Connection pooling handles bursts
- 🔄 Upgrade to dedicated compute if needed ($10/month)

---

## Monitoring & Observability

### Cloud Run Metrics (Google Cloud Console)

**Available Metrics**:
- Request count
- Request latency (p50, p95, p99)
- Instance count (active)
- CPU utilization
- Memory utilization
- Error rate (4xx, 5xx)

**Logs**:
- Application logs (stdout/stderr)
- Request logs (automatic)
- Cold start logs

**Access**:
```bash
# View logs
gcloud run services logs read maori-story-backend \
  --region=us-central1 \
  --limit=50

# View metrics
# Navigate to: Cloud Console → Cloud Run → Service → Metrics
```

---

### Neon Metrics (Neon Console)

**Available Metrics**:
- Connections (active, idle)
- Storage used / limit
- Compute time used
- Query statistics

**Access**: https://console.neon.tech/

---

## Security Considerations

### Network Security

✅ **HTTPS Everywhere**:
- GitHub Pages: Automatic HTTPS
- Cloud Run: Automatic HTTPS with Google-managed cert
- Neon: SSL/TLS required (`sslmode=require`)

✅ **CORS Policies**:
```python
CORS_ALLOWED_ORIGINS = [
    'https://jothep.github.io',
]
```

✅ **Secret Management**:
- No secrets in code or environment files
- All secrets in GCP Secret Manager
- Encrypted at rest and in transit

---

### Application Security

✅ **Input Validation**:
- Django form validation
- DRF serializer validation
- File type/size validation

✅ **Dependency Scanning**:
- Trivy scans Docker images in CI/CD
- `npm audit` for frontend dependencies
- Exit on HIGH/CRITICAL vulnerabilities

✅ **Authentication** (Admin only):
- Django admin protected by session auth
- CSRF protection enabled
- Password hashing with bcrypt

---

## Disaster Recovery

### Backup Strategy

**Database (Neon)**:
- ✅ Automatic daily backups (retained 7 days)
- ✅ Point-in-time restore (within 7 days)
- ✅ Manual backup via `pg_dump`:
  ```bash
  pg_dump "postgresql://user:${DB_PASSWORD}@ep-xxx.neon.tech/neondb" > backup.sql
  ```

**Media Files (Cloud Storage)**:
- ✅ Versioning enabled (optional)
- ✅ Soft delete (30-day retention)
- ✅ Manual backup via `gsutil`:
  ```bash
  gsutil -m cp -r gs://maori-story-media ./backup/
  ```

**Code & Config**:
- ✅ Version control (GitHub)
- ✅ Immutable Docker images (tagged by SHA)

---

### Recovery Procedures

**Scenario 1: Database Corruption**
```bash
# Restore from Neon backup (via Console)
1. Go to Neon Console → Backups
2. Select restore point
3. Create new branch or restore to main
4. Update DATABASE_URL in Secret Manager if needed
```

**Scenario 2: Accidental Code Deployment**
```bash
# Rollback Cloud Run to previous revision
gcloud run services update-traffic maori-story-backend \
  --region=us-central1 \
  --to-revisions=<previous-revision>=100
```

**Scenario 3: Lost Media Files**
```bash
# Restore from local backup
gsutil -m cp -r ./backup/* gs://maori-story-media/
```

---

## Migration Path

### To Kubernetes (Future)

If traffic grows beyond free tiers, consider migrating to Kubernetes:

**Benefits**:
- Fixed monthly cost (predictable)
- More control over resources
- Lower per-request cost at scale

**Migration Steps**:
1. Use existing Kubernetes manifests in `/Infra` folder
2. Deploy to GKE or self-hosted cluster
3. Update DNS to point to Ingress
4. Migrate database to Cloud SQL or self-hosted PostgreSQL
5. Update CI/CD to deploy to K8s instead of Cloud Run

**Estimated Cost (GKE)**:
- GKE cluster: $74/month (zonal)
- Cloud SQL: $7-25/month (db-f1-micro to db-g1-small)
- **Total**: ~$80-100/month

**Break-even point**: ~4M requests/month or 500MB+ database

---

## Useful Commands

### Cloud Run

```bash
# Deploy new version
gcloud run deploy maori-story-backend \
  --image=us-central1-docker.pkg.dev/jaskojothep/maori-story/backend:latest \
  --region=us-central1

# View service details
gcloud run services describe maori-story-backend --region=us-central1

# View logs (live)
gcloud run services logs tail maori-story-backend --region=us-central1

# Update environment variable
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --update-env-vars=DJANGO_DEBUG=False

# Scale settings
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80
```

### Neon Database

```bash
# Connect via psql
psql "postgresql://user:${DB_PASSWORD}@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Run migrations remotely
export DATABASE_URL="postgresql://user:${DB_PASSWORD}@ep-xxx.neon.tech/neondb?sslmode=require"
python manage.py migrate

# Create backup
pg_dump "postgresql://..." > backup_$(date +%Y%m%d).sql

# Restore backup
psql "postgresql://..." < backup_20260501.sql
```

### Cloud Storage

```bash
# Upload file
gsutil cp local-file.mp3 gs://maori-story-media/bgm/

# Download file
gsutil cp gs://maori-story-media/bgm/file.mp3 ./

# List files
gsutil ls -r gs://maori-story-media/

# Set public access
gsutil iam ch allUsers:objectViewer gs://maori-story-media

# Sync directory
gsutil -m rsync -r ./media/ gs://maori-story-media/media/
```

---

## Troubleshooting

### Issue: Cold Start Latency

**Symptom**: First request after idle takes 5-10 seconds

**Solution**:
```bash
# Set minimum instances (costs money)
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --min-instances=1  # Keeps 1 instance always warm

# Cost: ~$10/month for 1 always-on instance
```

---

### Issue: Database Connection Timeout

**Symptom**: `FATAL: remaining connection slots reserved`

**Solution**:
```python
# Adjust Django connection settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 300,  # 5 minutes
        'OPTIONS': {
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
        }
    }
}
```

---

### Issue: CORS Errors

**Symptom**: Browser blocks API requests from GitHub Pages

**Solution**:
```python
# Verify CORS settings in settings.py
CORS_ALLOWED_ORIGINS = [
    'https://jothep.github.io',
    'http://localhost:5173',  # For local dev
]
CORS_ALLOW_CREDENTIALS = True
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-01 | Initial production architecture documentation |

---

**Document Owner**: Xiang Zhu  
**Last Review**: 2026-05-01  
**Next Review**: 2026-08-01
