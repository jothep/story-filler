# Cloud Run Environment Variables Management

This document describes how to manage environment variables for the backend service deployed on Google Cloud Run.

## Current Environment Variables

The backend service requires the following environment variables:

### Required Variables
- `DATABASE_URL` - PostgreSQL connection string (Neon database)
- `SECRET_KEY` - Django secret key for cryptographic signing
- `DEBUG` - Set to `False` for production
- `ALLOWED_HOSTS` - Allowed host/domain names (set to `*` for Cloud Run)
- `USE_GCS` - Set to `true` to enable Google Cloud Storage for media files
- `GS_BUCKET_NAME` - GCS bucket name for media storage

### CORS and CSRF Configuration
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed origins
  - Example: `http://localhost:5173,http://localhost:8080,https://jothep.github.io`
- `CSRF_TRUSTED_ORIGINS` - Comma-separated list of trusted origins for CSRF
  - Example: `http://localhost:8000,http://localhost`
- `CSRF_TRUSTED_ORIGIN_WILDCARDS` - Wildcard patterns for trusted origins
  - Example: `https://*.run.app`

## How to Update Environment Variables

### Method 1: Using gcloud CLI (Recommended)

Update individual variables:
```bash
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --update-env-vars="KEY=value"
```

Set all variables at once (replaces all existing variables):
```bash
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --set-env-vars="KEY1=value1,KEY2=value2,..."
```

### Method 2: Using YAML file

Create a file `env-vars.yaml`:
```yaml
DATABASE_URL: "your-database-url"
SECRET_KEY: "your-secret-key"
DEBUG: "False"
ALLOWED_HOSTS: "*"
USE_GCS: "true"
GS_BUCKET_NAME: "your-bucket-name"
CORS_ALLOWED_ORIGINS: "http://localhost:5173,http://localhost:8080,https://jothep.github.io"
CSRF_TRUSTED_ORIGINS: "http://localhost:8000,http://localhost"
CSRF_TRUSTED_ORIGIN_WILDCARDS: "https://*.run.app"
```

Apply the configuration:
```bash
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --env-vars-file=env-vars.yaml
```

### Method 3: Using Google Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on `maori-story-backend` service
3. Click "EDIT & DEPLOY NEW REVISION"
4. Scroll to "Container(s), Volumes, Networking, Security"
5. Under "Variables & Secrets" tab, add/edit environment variables
6. Click "DEPLOY"

## Important Notes

- ⚠️ **CI/CD does NOT automatically update environment variables**
  - The deployment workflow only updates the container image
  - Environment variables must be managed manually
  
- 🔒 **Never commit sensitive values to git**
  - Use GitHub Secrets for CI/CD
  - Use Secret Manager for production secrets
  
- 📝 **Document changes**
  - Keep this file updated when adding/removing variables
  - Update `.env.example` files accordingly

## Viewing Current Variables

List all environment variables:
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="table(spec.template.spec.containers[0].env)"
```

Check specific variable:
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)" | grep KEY_NAME
```

## Troubleshooting

### Service fails to start
- Check logs: `gcloud run services logs read maori-story-backend --region=us-central1 --limit=50`
- Verify all required variables are set
- Check for typos in variable names

### CORS errors in browser
- Verify `CORS_ALLOWED_ORIGINS` includes the frontend URL
- Check that the URL matches exactly (including protocol)
- Remember: Origin includes protocol and domain, but NOT path

### Database connection errors
- Verify `DATABASE_URL` format is correct
- Check Neon database is accessible from Cloud Run
- Ensure connection string includes `?sslmode=require`
