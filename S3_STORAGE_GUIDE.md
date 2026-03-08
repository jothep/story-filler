# S3 Storage Configuration Guide

This guide explains how to configure media file storage for the Maori Story Filler project using three different modes: Local Storage, MinIO, and AWS S3.

## Table of Contents

- [Overview](#overview)
- [Mode 1: Local Storage (Default)](#mode-1-local-storage-default)
- [Mode 2: MinIO (Self-hosted S3)](#mode-2-minio-self-hosted-s3)
- [Mode 3: AWS S3](#mode-3-aws-s3)
- [Migration Guide](#migration-guide)
- [Troubleshooting](#troubleshooting)

---

## Overview

### Supported Storage Modes

| Mode | Use Case | Cost | Scalability | Setup Complexity |
|------|----------|------|-------------|------------------|
| **Local** | Development, small deployments | Free | Limited by disk | ⭐ Easy |
| **MinIO** | Self-hosted production | Server cost only | High (horizontal scaling) | ⭐⭐ Medium |
| **AWS S3** | Cloud production | Pay-per-use (~$2-5/month) | Unlimited | ⭐⭐ Medium |

### Architecture

```
┌─────────────┐
│   Django    │
│   Backend   │
└──────┬──────┘
       │
       ├─ USE_S3=false ──→ Local Filesystem (backend/media/)
       │
       ├─ USE_S3=true  ──→ AWS S3 (s3://bucket-name/)
       │   (no endpoint)
       │
       └─ USE_S3=true  ──→ MinIO (http://minio:9000/bucket/)
           (with endpoint)
```

---

## Mode 1: Local Storage (Default)

### Configuration

**Environment Variables:**
```bash
USE_S3=false  # or omit entirely (default)
```

**Media Path:**
- Development: `backend/media/`
- Production: `/app/media/` (Docker container)

### When to Use
- ✅ Development environment
- ✅ Small deployments (<50GB media)
- ✅ Single-server setup
- ✅ Budget-constrained projects

### Limitations
- ❌ Not suitable for multi-instance deployments
- ❌ Requires manual backup
- ❌ No CDN acceleration
- ❌ Storage limited by disk space

### Deployment

**Docker:**
```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - ./media:/app/media  # Mount local directory
```

**Kubernetes:**
```yaml
# Requires PersistentVolumeClaim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: media-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 50Gi
```

---

## Mode 2: MinIO (Self-hosted S3)

### What is MinIO?

MinIO is an open-source, S3-compatible object storage server that you can run on your own infrastructure.

### Configuration

**Step 1: Start MinIO**

```bash
# Using docker-compose
docker-compose -f docker-compose.minio.yml up -d

# Access MinIO Console: http://localhost:9001
# Username: REMOVED_CREDENTIAL
# Password: REMOVED_CREDENTIAL
```

**Step 2: Create Bucket**

The `docker-compose.minio.yml` automatically creates the `maori-story` bucket. To create manually:

```bash
# Using MinIO Client (mc)
mc alias set myminio http://localhost:9000 REMOVED_CREDENTIAL REMOVED_CREDENTIAL
mc mb myminio/maori-story
mc anonymous set download myminio/maori-story
```

**Step 3: Configure Backend**

**Environment Variables:**
```bash
USE_S3=true
AWS_ACCESS_KEY_ID=REMOVED_CREDENTIAL
AWS_SECRET_ACCESS_KEY=REMOVED_CREDENTIAL
AWS_STORAGE_BUCKET_NAME=maori-story
AWS_S3_ENDPOINT_URL=http://minio:9000
AWS_S3_REGION_NAME=us-east-1
```

### When to Use
- ✅ Self-hosted production environment
- ✅ Data sovereignty requirements
- ✅ Cost-sensitive deployments
- ✅ Need S3 compatibility without cloud vendor lock-in

### Advantages
- ✅ No recurring cloud costs
- ✅ Full control over data
- ✅ S3-compatible API
- ✅ Horizontal scalability (MinIO in distributed mode)
- ✅ Built-in versioning and lifecycle policies

### Deployment

**Docker Compose (Development):**

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - USE_S3=true
      - AWS_S3_ENDPOINT_URL=http://minio:9000
      # ... other S3 variables
    depends_on:
      - minio

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    # ... see docker-compose.minio.yml
```

**Kubernetes (Production):**

```yaml
# minio-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: minio
        image: minio/minio:latest
        ports:
        - containerPort: 9000
        - containerPort: 9001
        env:
        - name: MINIO_ROOT_USER
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: root-user
        - name: MINIO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: root-password
        volumeMounts:
        - name: data
          mountPath: /data
        command:
        - minio
        - server
        - /data
        - --console-address
        - ":9001"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: minio-pvc
```

---

## Mode 3: AWS S3

### Configuration

**Step 1: Create S3 Bucket**

```bash
# Using AWS CLI
aws s3 mb s3://maori-story-media --region ap-southeast-2

# Set bucket policy (optional - for public read access)
aws s3api put-bucket-policy \
  --bucket maori-story-media \
  --policy file://bucket-policy.json
```

**bucket-policy.json:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::maori-story-media/*"
    }
  ]
}
```

**Step 2: Create IAM User**

```bash
# Create IAM user
aws iam create-user --user-name maori-story-app

# Attach S3 policy
aws iam attach-user-policy \
  --user-name maori-story-app \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Create access keys
aws iam create-access-key --user-name maori-story-app
```

**Step 3: Configure Backend**

**Environment Variables:**
```bash
USE_S3=true
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=maori-story-media
AWS_S3_REGION_NAME=ap-southeast-2
```

### When to Use
- ✅ Production deployments
- ✅ High availability requirements
- ✅ Global CDN acceleration needed
- ✅ Don't want to manage storage infrastructure

### Advantages
- ✅ 99.999999999% (11 9's) durability
- ✅ Automatic backups and versioning
- ✅ CloudFront CDN integration
- ✅ Pay only for what you use
- ✅ Automatic scaling
- ✅ Advanced features (lifecycle policies, glacier archiving)

### Cost Estimation

**Assumptions:**
- Storage: 10GB media files
- Requests: 1,000 GET/day, 100 PUT/day
- Region: ap-southeast-2 (Sydney)

**Monthly Costs:**
- Storage: 10GB × $0.023 = $0.23
- GET requests: 30,000 × $0.00038/1,000 = $0.01
- PUT requests: 3,000 × $0.0047/1,000 = $0.01
- Data transfer (1GB/day): 30GB × $0.114/GB = $3.42
- **Total: ~$3.67/month**

---

## Migration Guide

### Migrating from Local to S3/MinIO

**Step 1: Backup existing media files**

```bash
# Backup local media directory
tar -czf media-backup-$(date +%Y%m%d).tar.gz backend/media/
```

**Step 2: Upload to S3/MinIO**

**For AWS S3:**
```bash
aws s3 sync backend/media/ s3://maori-story-media/
```

**For MinIO:**
```bash
mc mirror backend/media/ myminio/maori-story/
```

**Step 3: Update environment variables**

```bash
# Stop the application
docker-compose down

# Update .env file with S3 configuration
# See Mode 2 or Mode 3 sections above

# Restart the application
docker-compose up -d
```

**Step 4: Verify**

```bash
# Test file upload via Django admin
# Check that new files appear in S3/MinIO
# Verify old files are still accessible
```

### Migrating from S3 to MinIO

```bash
# Use rclone or aws-cli with custom endpoint
aws s3 sync \
  s3://aws-bucket/ \
  s3://minio-bucket/ \
  --endpoint-url http://minio:9000
```

---

## Troubleshooting

### Issue: "Access Denied" errors

**Solution:**
Check IAM permissions or MinIO access policies:

```bash
# AWS S3
aws s3api get-bucket-policy --bucket maori-story-media

# MinIO
mc admin policy info myminio readwrite
```

### Issue: Files not accessible after S3 migration

**Solution:**
Ensure bucket policy allows public read (if needed):

```bash
# MinIO
mc anonymous set download myminio/maori-story

# AWS S3
aws s3api put-bucket-acl --bucket maori-story-media --acl public-read
```

### Issue: "Invalid Endpoint" error with MinIO

**Solution:**
- Ensure `AWS_S3_ENDPOINT_URL` includes protocol (`http://` or `https://`)
- Check MinIO is accessible from backend container
- Verify network connectivity: `curl http://minio:9000/minio/health/live`

### Issue: Slow uploads to S3

**Solution:**
- Use S3 Transfer Acceleration (additional cost)
- Choose region closer to your servers
- Consider MinIO for local deployments

### Issue: Large media files causing timeouts

**Solution:**
Add timeout configurations:

```python
# settings.py (if using S3)
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_QUERYSTRING_EXPIRE = 3600  # Pre-signed URL expiry (1 hour)
```

---

## Testing

### Test Local Storage

```bash
python manage.py test core.tests.StorageConfigurationTest.test_default_uses_local_storage
```

### Test S3 Configuration

```python
# backend/core/tests.py
from django.test import TestCase
from django.conf import settings

class S3StorageTest(TestCase):
    def test_s3_configuration(self):
        if settings.USE_S3:
            self.assertTrue(hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'))
            self.assertIsNotNone(settings.AWS_ACCESS_KEY_ID)
```

---

## Best Practices

1. **Development**: Use local storage
2. **Testing**: Use MinIO in CI/CD
3. **Staging**: Use MinIO or S3
4. **Production**: Use AWS S3 or production MinIO cluster

5. **Security**:
   - Never commit AWS credentials to git
   - Use IAM roles when possible (EC2/ECS)
   - Enable S3 bucket versioning
   - Configure lifecycle policies for old files

6. **Performance**:
   - Enable CloudFront CDN for AWS S3
   - Use nginx caching for MinIO
   - Compress images before upload (already implemented)

7. **Cost Optimization**:
   - Set S3 lifecycle policies to move old files to Glacier
   - Clean up unused files periodically
   - Use S3 Intelligent-Tiering for variable access patterns

---

## References

- [Django Storages Documentation](https://django-storages.readthedocs.io/)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
