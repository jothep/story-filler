# Architecture Diagrams - Code Snippets

This file contains various architecture diagram codes that can be rendered using different tools.

---

## 1. System Architecture Diagram (Mermaid)

### High-Level 3-Tier Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[🌐 Browser<br/>Desktop/Mobile/Tablet]
    end

    subgraph "Ingress Layer"
        Ingress[⚙️ Nginx Ingress Controller<br/>SSL/TLS Termination<br/>Path-based Routing<br/>Body Size: 150MB]
    end

    subgraph "Application Layer"
        Frontend[📱 Frontend Service<br/>React 19 + Vite<br/>nginx:alpine<br/>Port: 80<br/>Size: ~20MB]
        Backend[🔧 Backend Service<br/>Django 5.2 + DRF<br/>Gunicorn + gevent<br/>Port: 8000<br/>Workers: 3]
    end

    subgraph "Data Layer"
        DB[(🗄️ PostgreSQL 16<br/>StatefulSet<br/>Port: 5432<br/>Storage: 5Gi)]
        PVC[💾 PersistentVolume<br/>Media Files<br/>ReadWriteOnce<br/>5Gi]
        S3[☁️ S3 Storage<br/>Optional<br/>MinIO / AWS S3]
    end

    Browser -->|HTTPS| Ingress
    Ingress -->|/ → SPA| Frontend
    Ingress -->|/api/*, /admin/*| Backend
    Ingress -->|/media/*, /static/*| Backend
    
    Backend -->|SQL Queries<br/>select_related<br/>prefetch_related| DB
    Backend -->|Read/Write<br/>Images, Audio| PVC
    Backend -.->|Optional<br/>django-storages| S3

    style Browser fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style Ingress fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style Frontend fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style Backend fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style DB fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style PVC fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style S3 fill:#b3e5fc,stroke:#0277bd,stroke-width:2px,stroke-dasharray: 5 5
```

---

## 2. Request Flow Diagram (Mermaid)

### User Request → Response Lifecycle

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Ingress as Nginx Ingress
    participant Frontend as Frontend Service
    participant Backend as Backend Service
    participant DB as PostgreSQL
    participant PVC as Media Storage

    User->>Browser: Visit https://app.example.com/
    Browser->>Ingress: GET / (HTTPS)
    Ingress->>Frontend: Route to frontend-svc:80
    Frontend->>Browser: Return index.html + assets
    Browser->>Browser: React app loads

    Browser->>Ingress: GET /api/stories/ (Fetch data)
    Ingress->>Backend: Route to backend-svc:80 → 8000
    Backend->>DB: SELECT * FROM story_story<br/>with select_related()
    DB-->>Backend: [{id:1, title:"..."}, ...]
    Backend-->>Browser: JSON: {stories: [...]}
    Browser->>Browser: Render story list

    User->>Browser: Click story button
    Browser->>Browser: React Router → /story/1

    Browser->>Ingress: GET /api/stories/1/
    Ingress->>Backend: Route to backend
    Backend->>DB: SELECT with prefetch_related<br/>(paragraphs, words)
    DB-->>Backend: Story + Paragraphs + Words
    Backend-->>Browser: JSON: {story, paragraphs, words}
    Browser->>Browser: Render interactive story

    Browser->>Ingress: GET /media/audio/paragraph1.mp3
    Ingress->>Backend: Route to backend
    Backend->>PVC: Read file from /app/media/
    PVC-->>Backend: Audio file stream
    Backend-->>Browser: Audio file (binary)
    Browser->>Browser: Play audio via HTML5 API

    User->>Browser: Drag & drop words
    Browser->>Browser: dnd-kit handles interaction
```

---

## 3. CI/CD Pipeline Diagram (Mermaid)

### GitHub Actions Workflow

```mermaid
graph TB
    Start[🚀 Git Push to main] --> Branch{Changed Files?}
    
    Branch -->|backend/**| BackendPipeline
    Branch -->|frontend/**| FrontendPipeline
    Branch --> CodeQL[🔒 CodeQL Security Scan]

    subgraph BackendPipeline[Backend Pipeline - deploy-backend.yml]
        B1[📋 Checkout Code]
        B2[🐍 Setup Python 3.13]
        B3[📦 Install Dependencies]
        B4[🔍 Flake8 Style Check<br/>continue-on-error]
        B5[🔍 Pylint Static Analysis<br/>continue-on-error]
        B6[✅ Django Tests 9 tests<br/>exit-on-failure]
        B7[🔐 Auth to GCP]
        B8[🛠️ Build Docker Image<br/>SHA + latest tags]
        B9[🛡️ Trivy Security Scan<br/>exit on HIGH/CRITICAL]
        B10[⬆️ Push to Artifact Registry]
        B11[🚀 Deploy to Cloud Run]
        B12[📊 Output Service URL]
        
        B1-->B2-->B3-->B4-->B5-->B6
        B6-->B7-->B8-->B9-->B10-->B11-->B12
    end

    subgraph FrontendPipeline[Frontend Pipeline - deploy-frontend.yml]
        F1[📋 Checkout Code]
        F2[📗 Setup Node.js 20]
        F3[📦 npm ci]
        F4[🔍 ESLint<br/>exit-on-error]
        F5[✅ Vitest Tests 6 tests<br/>exit-on-failure]
        F6[🔧 Create .env.production<br/>Inject API URL]
        F7[🛠️ Vite Build]
        F8[⬆️ Upload Pages Artifact]
        F9[🚀 Deploy to GitHub Pages]
        F10[📊 Output Page URL]
        
        F1-->F2-->F3-->F4-->F5-->F6-->F7-->F8-->F9-->F10
    end

    B12 --> GCP[☁️ Google Cloud Platform<br/>Artifact Registry<br/>Cloud Run Service]
    F10 --> GHP[📄 GitHub Pages<br/>Static Site + CDN]

    style Start fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    style BackendPipeline fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style FrontendPipeline fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style GCP fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style GHP fill:#b3e5fc,stroke:#0277bd,stroke-width:2px
    style CodeQL fill:#ce93d8,stroke:#7b1fa2,stroke-width:2px
```

---

## 4. Database Schema Diagram (Mermaid)

### Entity Relationship Diagram

```mermaid
erDiagram
    STORY ||--o{ PARAGRAPH : "contains"
    STORY ||--o{ WORD : "has words"
    STORY ||--o{ STORY_PICTURE : "has pictures"
    PARAGRAPH ||--o{ WORD : "words belong to"
    
    STORY {
        int id PK "Primary Key"
        varchar title "Story title"
        text description "Story description"
        datetime created_at
        datetime updated_at
    }
    
    PARAGRAPH {
        int id PK
        int story_id FK "Foreign Key → STORY"
        int order "Display order"
        text original_text "Full paragraph text"
        varchar audio_file "Path to audio file"
        datetime created_at
    }
    
    WORD {
        int id PK
        int story_id FK "Foreign Key → STORY"
        int paragraph_id FK "Foreign Key → PARAGRAPH nullable"
        varchar word_text "The word text"
        varchar word_type "MAORI or EXTRA"
        int order "Display order"
        datetime created_at
    }
    
    STORY_PICTURE {
        int id PK
        int story_id FK "Foreign Key → STORY"
        varchar picture "Path to image file"
        datetime created_at
    }
    
    APP_CONFIG {
        int id PK
        varchar key "Unique config key"
        text value "Config value"
        text description "Human-readable description"
        datetime created_at
        datetime updated_at
    }
```

---

## 5. Kubernetes Resource Diagram (Mermaid)

### K8s Components & Dependencies

```mermaid
graph TB
    subgraph namespace[Namespace: story-fill]
        
        subgraph ingress[Ingress Resources]
            IngressRes[Ingress: maori-story-ingress<br/>Class: nginx<br/>Body Size: 150MB]
        end
        
        subgraph frontend[Frontend Resources]
            FrontendSvc[Service: frontend-svc<br/>ClusterIP:80]
            FrontendDeploy[Deployment: frontend-deployment<br/>Replicas: 1<br/>Image: jasko/frontend:v1]
            FrontendPod[Pod: frontend-xxx<br/>Container: nginx:80<br/>Resources: No limits]
        end
        
        subgraph backend[Backend Resources]
            BackendSvc[Service: backend-svc<br/>ClusterIP:80 → 8000]
            BackendDeploy[Deployment: backend-deployment<br/>Replicas: 1<br/>Image: jasko/backend:v0.2]
            BackendPod[Pod: backend-xxx<br/>Container: Django:8000<br/>Gunicorn workers: 3]
            MediaPVC[PVC: media-pvc<br/>5Gi ReadWriteOnce]
        end
        
        subgraph database[Database Resources]
            PostgresSvc[Service: postgres-svc<br/>ClusterIP:5432]
            PostgresSS[StatefulSet: postgres-statefulset<br/>Replicas: 1<br/>Image: postgres:16.10-alpine]
            PostgresPod[Pod: postgres-0<br/>Requests: 256Mi, 250m CPU<br/>Limits: 1Gi, 1000m CPU]
            PostgresPVC[PVC: postgres-data<br/>5Gi ReadWriteOnce]
        end
        
        subgraph secrets[Secrets & ConfigMaps]
            PostgresSecret[Secret: postgres-secret<br/>POSTGRES_USER<br/>POSTGRES_PASSWORD]
            BackendSecret[Secret: backend-secrets<br/>DB credentials<br/>Django secret key]
        end
        
        subgraph jobs[One-time Jobs]
            MigrateJob[Job: backend-migrate-job<br/>Run: python manage.py migrate]
            SuperuserJob[Job: backend-create-superuser-job<br/>Create admin user]
        end
    end
    
    IngressRes --> FrontendSvc
    IngressRes --> BackendSvc
    
    FrontendSvc --> FrontendDeploy
    FrontendDeploy --> FrontendPod
    
    BackendSvc --> BackendDeploy
    BackendDeploy --> BackendPod
    BackendPod --> MediaPVC
    BackendPod --> PostgresSvc
    BackendPod --> BackendSecret
    
    PostgresSvc --> PostgresSS
    PostgresSS --> PostgresPod
    PostgresPod --> PostgresPVC
    PostgresPod --> PostgresSecret
    
    MigrateJob --> PostgresSvc
    SuperuserJob --> PostgresSvc

    style namespace fill:#f5f5f5,stroke:#424242,stroke-width:3px
    style ingress fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style frontend fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style backend fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style database fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style secrets fill:#ce93d8,stroke:#7b1fa2,stroke-width:2px
    style jobs fill:#b3e5fc,stroke:#0277bd,stroke-width:2px
```

---

## 6. Deployment Comparison Diagram (Mermaid)

### Three Deployment Options

```mermaid
graph TB
    subgraph Option1[Option 1: Kubernetes Self-hosted]
        K8sCluster[Kubernetes Cluster<br/>Oracle Cloud / AWS EC2]
        K8sIngress[Nginx Ingress]
        K8sFrontend[Frontend Pods 1-N]
        K8sBackend[Backend Pods 1-N]
        K8sDB[PostgreSQL StatefulSet]
        K8sPVC[PersistentVolumes]
        
        K8sCluster --> K8sIngress
        K8sIngress --> K8sFrontend
        K8sIngress --> K8sBackend
        K8sBackend --> K8sDB
        K8sBackend --> K8sPVC
    end
    
    subgraph Option2[Option 2: Cloud Run + GitHub Pages]
        GHPages[GitHub Pages<br/>Frontend CDN]
        CloudRun[Google Cloud Run<br/>Backend Auto-scale]
        CloudSQL[Cloud SQL<br/>Managed PostgreSQL]
        CloudStorage[Cloud Storage<br/>Media Files]
        
        GHPages -.->|API Calls| CloudRun
        CloudRun --> CloudSQL
        CloudRun --> CloudStorage
    end
    
    subgraph Option3[Option 3: Docker Compose]
        DockerHost[Single Server VPS]
        Nginx[Nginx Container]
        DCFrontend[Frontend Container]
        DCBackend[Backend Container]
        DCDB[PostgreSQL Container]
        Volumes[Docker Volumes]
        
        DockerHost --> Nginx
        Nginx --> DCFrontend
        Nginx --> DCBackend
        DCBackend --> DCDB
        DCBackend --> Volumes
    end

    style Option1 fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    style Option2 fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    style Option3 fill:#b3e5fc,stroke:#0277bd,stroke-width:3px
```

---

## 7. Data Flow Diagram - Story Loading (Mermaid)

### Complete User Journey

```mermaid
flowchart TD
    Start([👤 User visits<br/>https://app.example.com/]) --> LoadHTML[Browser requests /<br/>Ingress routes to Frontend]
    LoadHTML --> ReactInit[React App initializes<br/>Renders Menu component]
    ReactInit --> APICall1[useStories hook<br/>GET /api/stories/]
    
    APICall1 --> BackendReceive[Backend receives request<br/>Django view invoked]
    BackendReceive --> DBQuery1[Query PostgreSQL<br/>SELECT * FROM story_story]
    DBQuery1 --> Serialize1[Serialize to JSON<br/>StoriesList Serializer]
    Serialize1 --> Response1[Return JSON response<br/>{stories: [{id, title}, ...]}]
    
    Response1 --> RenderList[React renders story list<br/>NES.css styled buttons]
    RenderList --> UserClick{User clicks story button}
    
    UserClick --> Navigate[React Router navigates<br/>to /story/:id]
    Navigate --> APICall2[StoryPage component<br/>GET /api/stories/:id/]
    
    APICall2 --> DBQuery2[Optimized query<br/>select_related + prefetch_related<br/>Story + Paragraphs + Words]
    DBQuery2 --> Serialize2[Serialize full story data<br/>Nested relationships]
    Serialize2 --> Response2[Return JSON<br/>{story, paragraphs, words}]
    
    Response2 --> RenderStory[React renders:<br/>- Paragraph slots dnd-kit<br/>- Word bank draggables<br/>- Audio players]
    RenderStory --> AudioRequest[Request audio file<br/>GET /media/audio/file.mp3]
    
    AudioRequest --> ServeMedia[Backend serves from<br/>PVC or S3 storage]
    ServeMedia --> PlayAudio[Browser plays audio<br/>HTML5 Audio API]
    
    PlayAudio --> Interact[User interacts:<br/>- Drag words to slots<br/>- Play audio<br/>- Submit answers]
    Interact --> Complete([✅ Story complete])

    style Start fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style Complete fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style UserClick fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style DBQuery1 fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style DBQuery2 fill:#ffccbc,stroke:#d84315,stroke-width:2px
```

---

## How to Render These Diagrams

### 1. Mermaid Live Editor (Online)
1. Visit https://mermaid.live/
2. Paste any of the code blocks above
3. Download as PNG/SVG

### 2. VS Code (Local)
1. Install extension: "Markdown Preview Mermaid Support"
2. Open this file in VS Code
3. Press `Cmd+Shift+V` (Mac) or `Ctrl+Shift+V` (Windows)
4. View rendered diagrams

### 3. GitHub Markdown (Automatic)
- GitHub automatically renders Mermaid diagrams in `.md` files
- Just commit this file and view on GitHub

### 4. Command Line (mmdc)
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Render to PNG
mmdc -i diagram.mmd -o diagram.png

# Render to SVG
mmdc -i diagram.mmd -o diagram.svg
```

### 5. Include in Documentation
```markdown
# Your Documentation

## Architecture Overview

\`\`\`mermaid
graph TB
    ... paste diagram code here ...
\`\`\`
```

---

## Alternative Diagram Formats

### PlantUML Version (C4 Model)

If you prefer PlantUML, here's the system context diagram:

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

Person(user, "Language Learner", "Student learning Māori")

System_Boundary(system, "Maori Story Filler") {
    Container(frontend, "Frontend", "React, nginx", "Provides UI for story interaction")
    Container(backend, "Backend", "Django, Gunicorn", "Provides REST API and admin")
    ContainerDb(database, "Database", "PostgreSQL", "Stores stories, words, media references")
}

System_Ext(cdn, "GitHub Pages", "Serves static frontend")
System_Ext(storage, "Cloud Storage", "Stores media files")

Rel(user, frontend, "Uses", "HTTPS")
Rel(frontend, backend, "Calls API", "JSON/HTTPS")
Rel(backend, database, "Reads/Writes", "SQL/5432")
Rel(backend, storage, "Stores/Retrieves", "S3 API")
Rel_U(cdn, frontend, "Delivers")

@enduml
```

### Draw.io / diagrams.net XML

For manual editing in Draw.io:
1. Visit https://app.diagrams.net/
2. File → Import From → Text
3. Paste Mermaid code
4. Or manually recreate using shapes

---

## Diagram Maintenance

**When to Update**:
- New services added
- Deployment architecture changes
- Technology stack updates
- Major refactoring

**Version Control**:
- Keep diagrams in version control
- Update alongside code changes
- Include in pull request reviews

**Best Practices**:
- Keep diagrams simple and focused
- Use consistent color coding
- Add legends for symbols
- Include version numbers
- Link to implementation docs

---

**Last Updated**: 2026-05-01  
**Maintained By**: Xiang Zhu
