# Changelog

All notable changes to the Maori Story Filler project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- **[IN PROGRESS]** Attempting to fix Docker image vulnerabilities from `serve` package (2026-03-08)
  - Updated frontend Dockerfile to use `serve@latest` with cache clean
  - Addresses 5 HIGH severity vulnerabilities in serve's dependencies (minimatch, tar)
  - CVE-2026-26996, CVE-2026-27903, CVE-2026-27904 (minimatch)
  - CVE-2026-26960, CVE-2026-29786 (tar)
  - Prepared fallback solution: nginx-based Dockerfile (Dockerfile.nginx)
  - **Status**: Awaiting CI/CD validation

- Fixed 5 HIGH severity npm vulnerabilities in frontend dependencies (2026-03-08)
  - Updated minimatch to v10.2.3+ (CVE-2026-26996, CVE-2026-27903, CVE-2026-27904)
  - Updated rollup to v4.59.0 (Path Traversal vulnerability)
  - Updated react-router (CSRF and XSS vulnerabilities)
  - Updated ajv and js-yaml (ReDoS and prototype pollution)
  - 10 packages updated via `npm audit fix`

### Added
- Alternative nginx-based Dockerfile for production (frontend/Dockerfile.nginx)
  - Smaller image size (~20MB vs ~180MB)
  - Better security profile (no Node.js runtime dependencies)
  - Prepared as backup if serve@latest doesn't resolve vulnerabilities

### Changed
- Updated frontend Dockerfile to explicitly use `serve@latest`
  - Added npm cache clean to ensure fresh dependency resolution
  - Targets the latest serve version with security patches

### Fixed
- Frontend test suite updated to match new ErrorMessage component UI (2026-03-08)
- ESLint errors in error handling components (2026-03-08)
  - Added PropTypes validation to ErrorMessage and LoadingSpinner
  - Fixed unused variable in ErrorBoundary
  - Escaped apostrophe in error message text

## [0.2.0] - 2026-03-07

### Added
- **Comprehensive Error Handling** (commit ba3d086, fad19d2)
  - Created ErrorBoundary component to catch JavaScript errors
  - Created ErrorMessage component for user-friendly error displays
  - Created LoadingSpinner component with NES.css styling
  - Added error handling and retry functionality in API calls
  - Added graceful degradation for network failures

- **Structured Logging** (commit ba3d086)
  - Configured Django logging with RotatingFileHandler
  - Added separate log files for API requests and general errors
  - INFO level logging for successful operations
  - WARNING/ERROR level logging for failures
  - Logs stored in `backend/logs/` directory

- **Media File Management** (commit ac787a3)
  - Automatic image compression for StoryPicture and Word images
  - Resize images to max 1920x1080, quality 85%
  - File size validation (max 10MB for images, 20MB for audio)
  - File extension validation
  - Reduces storage costs by 50-80%

- **Infrastructure Documentation**
  - CODE_ANALYSIS.md: Detailed codebase analysis
  - COST_COMPARISON.md: Cloud deployment cost analysis (9 options)
  - TERRAFORM_GUIDE.md: Terraform deployment instructions
  - ORACLE_CLOUD_SETUP.md: Oracle Cloud configuration guide
  - REFACTORING_PLAN.md: Project refactoring roadmap

- **Production Deployment Configuration** (commit f25ecab)
  - docker-compose.prod.yml for single-machine deployment
  - nginx.prod.conf for production reverse proxy
  - Deployment scripts (deploy.sh, backup.sh)
  - Instance management scripts (start/stop/status)

- **Terraform Infrastructure** (commit 672610f)
  - Complete AWS EC2 deployment automation
  - VPC, Security Groups, and EC2 instance configuration
  - User data script for automated setup
  - Cost-optimized t3.small instance recommendation

### Changed
- **Database Query Optimization** (commit 4c19778)
  - Eliminated N+1 query problem using select_related() and prefetch_related()
  - Reduced story detail API queries from 35+ to 5-6 (85% improvement)
  - Added optimized querysets for StoryListAPIView and StoryDetailAPIView

- **Error Handling in Serializers** (commit ba3d086)
  - Safe file URL retrieval with try-catch blocks
  - Graceful handling of missing or invalid file paths
  - Detailed error logging for debugging

### Fixed
- CI/CD pipeline test failures (commit 4726a64)
  - Fixed Http404 handling in StoryDetailAPIView
  - Proper exception re-raising for 404 responses
  - All backend tests passing (4/4)

### Removed
- Material-UI dependencies (commit 5434f8d)
  - Removed @mui/material, @emotion/react, @emotion/styled
  - Saved ~10MB in package size, removed 44 packages
  - Fully migrated to NES.css for retro styling

## [0.1.0] - 2024-10-30

### Added
- Initial project setup with Django backend and React frontend
- Kubernetes-native deployment architecture
- GitHub Actions CI/CD pipeline
  - Automated testing and linting
  - Docker image building and publishing
  - Trivy security scanning
- Drag-and-drop story filling interface using dnd-kit
- NES.css retro 8-bit aesthetic
- PostgreSQL database with Django ORM
- Complete Kubernetes manifests for deployment
- Admin panel for content management

### Features
- Interactive Maori language learning through stories
- Word bank drag-and-drop interaction
- Audio playback for paragraphs
- Story completion tracking
- Congratulations page on story completion

### Technical Stack
- Frontend: React 19, Vite, React Router, dnd-kit
- Backend: Django 5.2, Django REST Framework, Gunicorn
- Database: PostgreSQL
- Deployment: Kubernetes, Docker, Ingress-Nginx
- CI/CD: GitHub Actions, Docker Hub, Trivy

---

## Version History Summary

- **v0.2.0** (2026-03-07): Major refactoring - error handling, logging, optimization, documentation
- **v0.1.0** (2024-10-30): Initial release with core functionality

---

## Migration Notes

### Upgrading to v0.2.0

#### Backend
1. Install Pillow dependency: `pip install pillow==11.3.0`
2. Logs directory will be auto-created at `backend/logs/`
3. Existing images will NOT be automatically compressed (only new uploads)
4. Review `backend/maori_story_project/settings.py` for new LOGGING configuration

#### Frontend
1. Run `npm install` to update dependencies
2. Run `npm audit` to verify no vulnerabilities
3. New error handling components are backward compatible
4. PropTypes are now enforced - ensure all components have proper prop definitions

#### Database
- No migrations required for v0.2.0
- All changes are code-level only

---

## Deprecation Notices

None at this time.

---

## Known Issues

### Open
- Frontend: Menu.jsx has hardcoded BGM path at line 61 (`/media/bgm/Schumann_Fantasy.mp3`)
  - Planned fix: Make audio path configurable via API

### In Progress
- S3 storage support for media files (optional enhancement)
- Additional frontend test coverage

---

## Contributing

When making changes, please:
1. Update this CHANGELOG.md with your changes
2. Follow the existing format (Added/Changed/Fixed/Removed/Security)
3. Include commit hashes for reference
4. Update SECURITY.md for any security-related changes
5. Run tests before committing (`npm test`, `python manage.py test`)
6. Follow TDD principles: write tests first, then implement features
