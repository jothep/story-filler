# Maori Story Filler

Maori Story Filler is an interactive web application designed to teach Māori vocabulary through a gamified, fill-in-the-blanks story experience. Users progress through stories by dragging and dropping the correct words into blank spaces.

This project is fully containerized and designed for a Kubernetes-native deployment, with a complete CI/CD pipeline for automated testing and image publishing.

## Project Status

- ✅ **CI/CD Pipeline**: All tests passing, automated security scanning enabled
- ✅ **Security**: Zero known vulnerabilities (see [SECURITY.md](SECURITY.md))
- ✅ **Code Quality**: Comprehensive error handling, structured logging, optimized queries
- 📚 **Documentation**: Complete guides for deployment, cost analysis, and refactoring

## Documentation

- [CHANGELOG.md](CHANGELOG.md) - Version history and updates
- [SECURITY.md](SECURITY.md) - Security policy and vulnerability reports
- [CODE_ANALYSIS.md](CODE_ANALYSIS.md) - Detailed codebase analysis
- [COST_COMPARISON.md](COST_COMPARISON.md) - Cloud deployment cost comparison
- [TERRAFORM_GUIDE.md](TERRAFORM_GUIDE.md) - Terraform infrastructure automation
- [REFACTORING_PLAN.md](REFACTORING_PLAN.md) - Project refactoring roadmap
## Key Features (v0.2.0)

### User Experience
- Interactive drag-and-drop story filling with dnd-kit
- Retro 8-bit aesthetic using NES.css
- Audio playback for pronunciation learning
- Comprehensive error handling with user-friendly messages
- Loading states and graceful error recovery

### Code Quality & Performance
- **85% Query Reduction**: Optimized database queries (35+ → 5-6 queries)
- **Error Boundaries**: JavaScript error catching and graceful degradation
- **Structured Logging**: Rotating file logs with detailed error tracking
- **Automatic Media Compression**: Images optimized to save 50-80% storage
- **File Validation**: Size and extension validation for uploads

### Security
- Zero known vulnerabilities (regularly scanned with Trivy)
- Non-root Docker containers
- Environment-based secret management
- CORS configured with explicit origins
- Input validation and sanitization

## Architecture Overview

* **Frontend**: A React single-page application (SPA) built with Vite. It uses dnd-kit for drag-and-drop interactions and NES.css for its retro 8-bit aesthetic. Includes comprehensive error handling, loading states, and PropTypes validation. Served in production using nginx:alpine for optimal security and performance.

* **Backend**: A Django REST Framework API that serves all story content, paragraphs, and word banks. It uses Gunicorn as the application server, WhiteNoise to serve static files, and psycopg2 to connect to the database. Features optimized queries, structured logging, and automatic media compression.

* **Database**: A PostgreSQL database deployed as a Kubernetes StatefulSet for persistent data storage.

* **CI/CD**: Automated via GitHub Actions. Pushes to the main branch trigger two separate workflows (for frontend and backend) which:
  - Install dependencies
  - Run linters (ESLint, Flake8) and tests (Vitest, Django TestCase)
  - Build Docker images with multi-stage builds
  - Scan images for vulnerabilities using Trivy
  - Push the tagged images to Docker Hub

* **Deployment**: The entire stack is deployed to Kubernetes using the manifests in the Infra/ directory. An Ingress-Nginx controller routes traffic to the appropriate services. Alternative single-machine deployment available via docker-compose.
## Tech Stack
| **Category** | **Technology** |
| :--- | :--- |
| **Frontend** | React, React Router, dnd-kit (Drag & Drop), NES.css |
| **Backend** | Django, Django Rest Framework (DRF), Gunicorn, WhiteNoise |
| **Database** | PostgreSQL |
| **CI/CD** | GitHub Actions, Docker, Trivy |
| **Deployment** | Kubernetes (K8s), Ingress-Nginx |

## Kubernetes Deployment Guide
This guide provides the full, ordered steps to deploy the application from scratch onto a Kubernetes cluster (e.g., Minikube, k3d, Docker Desktop K8s).
All manifests are located in the Infra/ directory and deploy to the story-fill namespace.
### 1. Prerequisites
A running Kubernetes cluster.
kubectl command-line tool installed and configured to your cluster.
A default StorageClass available in your cluster for dynamic Persistent Volume provisioning.
### 2. Install Ingress-Nginx Controller
If your cluster does not have an Ingress controller, you must install one.

### 3. Create Namespace
All resources will be deployed into the story-fill namespace.
kubectl create namespace story-fill

### 4. Create Kubernetes Secrets
Secrets must be created before the applications that depend on them.
A. PostgreSQL Secret (Used by the database itself)
```bash
# Replace with your own secure user and password
kubectl create secret generic postgres-secret -n story-fill \
--from-literal=POSTGRES_USER=${DB_USER} \
--from-literal=POSTGRES_PASSWORD=${MY_PASSWORD}
```

B. Django Backend Secrets (Used by the Django app)
Note: The values for POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD must be set as shown below to match the database service and the secret from Step 4A.
```bash
# Replace with your own values, especially the SECRET_KEY
kubectl create secret generic ${SECRET_NAME} \
--namespace ${K8S_NAMESPACE} \
--from-literal=SECRET_KEY="${SECRET_KEY_VALUE}" \
--from-literal=POSTGRES_PASSWORD="${DB_PASSWORD}" \
--from-literal=DEBUG="${DJANGO_DEBUG}" \
--from-literal=ALLOWED_HOSTS="${ALLOWED_HOSTS_VALUE}" \
--from-literal=POSTGRES_HOST="${DB_HOST}" \
--from-literal=POSTGRES_DB="${DB_NAME}" \
--from-literal=POSTGRES_USER="${DB_USER}" \
--from-literal=POSTGRES_PORT="${DB_PORT}" \
--from-literal=CORS_ALLOWED_ORIGINS="${CORS_ORIGINS}"
```

C. Django Superuser Secret (Used by the initialization job)
```bash
# Set the desired login credentials for the Django Admin panel
kubectl create secret generic django-superuser-creds -n story-fill \
  --from-literal=ADMIN_USER=${ADMIN_USER} \
  --from-literal=ADMIN_EMAIL=${ADMIN_EMAIL} \
  --from-literal=ADMIN_PASS=${ADMIN_PASSWORD}
```

### 5. Create Persistent Volume Claim (PVC)
The backend requires a PVC to store user-uploaded media files (images, audio). The database's PVC is created automatically by its StatefulSet.
```bash
kubectl apply -f Infra/pvc.yaml
```

### 6. Deploy PostgreSQL Database
This applies the postgres-deployment.yaml manifest, which creates the StatefulSet and Service for the database.
```bash
kubectl apply -f Infra/postgres-deployment.yaml
```

IMPORTANT: Wait for the database Pod to be fully ready before proceeding, or the migration job will fail.
```bash
# Run this command to wait until the Pod's 'Ready' status is true
echo "Waiting for PostgreSQL Pod to be ready..."
kubectl wait --for=condition=Ready pod \
  -l app=postgres \
  -n story-fill \
  --timeout=300s
echo "PostgreSQL is ready!"
```

### 7. Run Database Initialization Jobs
With the database running, we can now initialize the schema and create the admin user.
* A. Run Database Migrations
This runs python manage.py migrate inside a K8s Job to create all the tables.
```bash
kubectl apply -f Infra/backend-migrate-job.yaml
```

* B. Create Superuser
This runs the backend-create-superuser-job.yaml manifest to create the admin account.
```bash
kubectl apply -f Infra/backend-create-superuser-job.yaml
```

### 8. Deploy Applications
Now that the database is migrated, the main application services can be deployed.
```bash
# Deploy the Django Backend (Deployment + Service)
kubectl apply -f Infra/backend-deployment.yaml
```

```bash
# Deploy the React Frontend (Deployment + Service)
kubectl apply -f Infra/frontend-deployment.yaml
```

### 9. Apply Ingress Rules
Finally, apply the Ingress rules to route external traffic to your services.
```bash
kubectl apply -f Infra/ingress.yaml
```

## Accessing the Application
The application is now running, but it's only accessible inside the cluster. To access it from your laptop, you must forward a local port to the Ingress controller.
Find your Ingress Controller Service:
(It is usually in the ingress-nginx namespace)
```bash
kubectl get svc -n ingress-nginx
```
Look for a service named ingress-nginx-controller.
Start Port Forwarding:
(This command will run continuously. Leave this terminal open.)
```bash
# This forwards your local port 8080 to the ingress controller's port 80
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
```

Access the Application:
Main App (Frontend): Open your browser to http://localhost:8080
Admin Panel (Backend): Open your browser to http://localhost:8080/admin/
(Log in with the credentials from the django-superuser-creds secret).
## Debugging
If you suspect networking issues between Pods (e.g., the backend can't reach postgres-svc), you can use the debug-pod.yaml manifest.
```bash
# 1. Deploy the debug pod
kubectl apply -f Infra/debug-pod.yaml
```

```bash
# 2. Wait for it to be ready
kubectl wait --for=condition=Ready pod/network-debug-pod -n story-fill
```

```bash
# 3. Exec into the pod's shell
kubectl exec -it network-debug-pod -n story-fill -- /bin/sh
```

```bash
# 4. From inside the pod, test your K8s DNS and network
# You should see a "Connection refused" or HTTP response, *not* "bad address"
curl maori-story-backend-svc
```

```bash
# You should see the port is open
nc -z -v postgres-svc 5432
# Expected: "postgres-svc (10.x.x.x:5432) open"
```
