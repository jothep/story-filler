# Changelog

All notable changes to the Maori Story Filler project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- **[RESOLVED]** Fixed backend Python package vulnerabilities (2026-03-09, commit 0e3100c) ✅
  - Upgraded Django: 5.2.7 → 5.2.12
    - CVE-2025-64459 (CRITICAL): SQL injection
    - CVE-2025-64458 (HIGH): DoS on Windows
    - CVE-2026-1207 (HIGH): SQL injection via RasterField
    - CVE-2026-1287 (HIGH): SQL injection via column aliases
    - CVE-2026-25673 (HIGH): DoS via URL normalization
  - Upgraded Pillow: 11.3.0 → 12.1.1
    - CVE-2026-25990 (HIGH): Out-of-bounds Write via PSD Image
  - All 9 backend tests passing with upgraded versions

- **[RESOLVED]** Fixed all Docker image vulnerabilities (2026-03-08) ✅
  - **Iterative resolution process:**
    1. **Option 1 (FAILED)**: serve@latest - npm dependencies remained outdated
    2. **Option 2 (PARTIAL)**: nginx:alpine - eliminated Node.js issues but Alpine had CVEs
    3. **Option 3 (SUCCESS)**: Added Alpine package upgrade - resolved all vulnerabilities
  - **Final solution:**
    - Switched from serve to nginx:alpine
    - Added `apk update && apk upgrade` for system library updates
    - Upgraded zlib: 1.3.1-r2 → 1.3.2-r0 (fixes CVE-2026-22184 CRITICAL)
    - Upgraded libpng: 1.6.54-r0 → 1.6.55-r0 (fixes CVE-2026-25646 HIGH)
  - **Result:**
    - ✅ Zero HIGH/CRITICAL vulnerabilities in Trivy scan
    - ✅ 90% image size reduction (~180MB → ~20MB)
    - ✅ Eliminated Node.js runtime dependencies
    - ✅ Improved security posture and performance

- Fixed 5 HIGH severity npm vulnerabilities in frontend dependencies (2026-03-08)
  - Updated minimatch to v10.2.3+ (CVE-2026-26996, CVE-2026-27903, CVE-2026-27904)
  - Updated rollup to v4.59.0 (Path Traversal vulnerability)
  - Updated react-router (CSRF and XSS vulnerabilities)
  - Updated ajv and js-yaml (ReDoS and prototype pollution)
  - 10 packages updated via `npm audit fix`

### Added
- **Application Configuration System** (2026-03-09, commit 1f9967a)
  - Added AppConfig model for centralized settings management
  - Created `/api/config/` endpoint for frontend configuration
  - Django admin interface for managing app settings
  - Menu BGM path now configurable via API instead of hardcoded
  - Comprehensive tests: 9 backend tests + 4 frontend tests
  - Followed TDD: tests written first, then implementation

- nginx-based production Dockerfile for frontend (frontend/Dockerfile.nginx)
  - Multi-stage build: Node.js for build, nginx:alpine for serving
  - Eliminates runtime Node.js dependencies
  - 90% smaller image size (~20MB vs ~180MB)
  - Improved security and performance

### Changed
- **BREAKING**: Frontend now uses nginx:alpine instead of serve
  - Updated `.github/workflows/frontend-ci.yml` to use Dockerfile.nginx
  - Updated `Infra/frontend-deployment.yaml` port mapping (3000 → 80)
  - Container now exposes port 80 instead of 3000
  - No functional changes to application behavior
  - **Migration**: Kubernetes deployments must update port configuration

### Fixed
- **Hardcoded BGM path removed** (2026-03-09, commit 1f9967a)
  - Removed hardcoded BGM path from Menu.jsx line 61
  - BGM path now fetched from `/api/config/` endpoint
  - Graceful fallback when BGM config is unavailable
  - Content managers can now update BGM via Django admin

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

### Upgrading from Unreleased (Post 2026-03-09)

#### Backend
1. Run database migrations: `python manage.py migrate`
   - Migration `0007_appconfig` creates AppConfig table
2. Configure Menu BGM via Django admin:
   - Navigate to `/admin/` → Application Configurations
   - Add new config: key=`menu_bgm_path`, value=`/media/bgm/Schumann_Fantasy.mp3`
   - Or use any BGM path available in your media storage

#### Frontend
- No changes required - BGM configuration is backward compatible
- If no config is set, BGM will be disabled with warning in console

#### Database
- **New migration required**: `0007_appconfig`
- Run `python manage.py migrate` before deploying

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
None at this time.

### In Progress
- S3 storage support for media files (optional enhancement)
- Additional frontend test coverage

### Recently Resolved
- ✅ Frontend: Menu.jsx hardcoded BGM path (2026-03-09) - Now configurable via API

---

## Contributing

When making changes, please:
1. Update this CHANGELOG.md with your changes
2. Follow the existing format (Added/Changed/Fixed/Removed/Security)
3. Include commit hashes for reference
4. Update SECURITY.md for any security-related changes
5. Run tests before committing (`npm test`, `python manage.py test`)
6. Follow TDD principles: write tests first, then implement features
