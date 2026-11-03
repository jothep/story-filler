# Changelog

All notable changes to the Maori Story Filler project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **About & Credits content (2026-11-03)**: added an application introduction and acknowledgements for Gemini, Claude and ChatGPT. Kept the author, portfolio and LinkedIn links, simplified the material credits, and removed the generic disclaimer.
- **About and contact links (2026-11-03)**: added the Story Filler portfolio case study and LinkedIn links to About & Credits. Replaced the email address with LinkedIn as the contact route.
- **PostgreSQL-only backend verification (2026-11-03)**: moved all existing Django tests to isolated PostgreSQL in CI and final-image verification. Pinned local Compose to the same PostgreSQL image used by recovery tests. Build-time static collection runs without networking; lint loads PostgreSQL metadata without connecting to a database.
- **Backend base image (2026-11-03)**: moved the runtime to digest-pinned Python 3.13 on Alpine 3.24. A separate build stage compiles two dependencies that have no musllinux wheels; hashes, fixed build tools, the existing runtime versions and non-root UID/GID are preserved. Added pre-merge image, PostgreSQL, static-resource and shutdown checks.
- **Frontend analysis tools (2026-11-03)**: replaced ESLint with Oxlint and strict checking of existing JavaScript through TypeScript/JSDoc. Preserved the reviewed JavaScript, React and Hooks checks through explicit rules and regression cases; retained Prettier. Added readable shared API/context types and safe handling of non-Error request failures.
- **Local recovery review (2026-11-02)**: retired both unsafe backup entry points as well as the already-disabled restore commands. Replaced the old volume-copy guide with explicit source checks, writer coordination, integrity validation and isolated recovery instructions. Removed automatic backup deletion and instructions to overwrite existing volumes.
- **Maintenance review (2026-11-02)**: standardized formatting across the maintained frontend, backend and Python maintenance scripts; removed unused component backups and an unused starter icon. CI now requires formatting, Flake8 and Django-aware Pylint, with the existing score threshold and an explicit failure for errors. React checks remain enabled, Hooks checks are added, and tests/build scripts receive their own lint environments. Runtime dependencies and database migrations are unchanged.
- **Dependency and delivery review (2026-11-02)**: separated direct Python dependency inputs from generated runtime/development hash locks; standardized frontend tooling on Node 24 and locked installs; committed Terraform provider checksums. Production frontend containers now use Nginx, retaining their existing ports and URL paths. The backend image installs binary runtime dependencies without compilers or development tools.
- **Release ordering (2026-11-02)**: separated backend checks, image build/scan/push, and deployment. Releases use the scanned image digest and check the currently serving source commit while holding a deployment lock. Old candidates are skipped; unknown or conflicting metadata stops delivery. Pull requests run without deployment credentials.
- **Local safety review (2026-11-02)**: disabled both legacy volume-restore entry points before any operational command. Updated their historical guide and generated backup instructions; the fifth batch subsequently supplied the replacement tooling described below.

- **Frontend Code Refactoring** (2026-04-30, commit 27bf86e, 273a2d6)
  - Applied Clean Code principles to improve maintainability
  - Menu.jsx reduced from 260 lines to 177 lines (-32%)
  - InfoCredits.jsx reduced from 172 lines to 136 lines (-21%)
  - Extracted audio logic into reusable `useBgmPlayer` custom hook (100 lines)
  - Separated styles from InfoCredits component (95 lines)
  - Created centralized design tokens in `constants/theme.js` (54 lines)
  - Created content configuration in `constants/credits.js` (27 lines)
  - Removed 15+ console.log debugging statements
  - Improved accessibility: ARIA attributes, keyboard navigation (Escape key)
  - Better state management: controlled hover states instead of inline handlers
  - All tests passing (6/6) with no breaking changes
  - Documentation: Created `docs/REFACTORING-2026-04-30.md` with metrics and migration guide

### Security
- **Security closeout published (2026-11-03)**: PR #5 passed all five required checks and independent review, then published both applications. All 11 CodeQL alerts are fixed without dismissals; complete source, dependency and image reports are clear. The first scheduled-maintenance manual execution passed. Documentation-only PRs skip container rebuilding/recovery exercises while retaining stable checks; the extra standalone main-push source scan was removed. See [verified evidence](docs/security-closeout.md#verification-and-publication).
- **CodeQL alert and gate review (2026-11-03)**: reviewed all 11 open source alerts individually. Demo poll responses now declare plain text with `nosniff`, including the unreported stored-HTML path in the list view. API logging escapes request metadata and identifiers while preserving normal messages and exception traces. Pages verification resolves HTML references against a build-directory inventory before any request, fixes the destination to its loopback server and rejects redirects. Existing integer routes and Node's rejection of credential-bearing fetch URLs limit the original reported paths; this is not a claim of demonstrated exploitation. See the [alert matrix and release verification](docs/security-closeout.md).
- **Security enforcement configuration (2026-11-03)**: replaced advisory CodeQL handling with a strict SARIF gate that blocks every result and invalid/incomplete reports. Added a stable merge-check status and fresh source/credential dependencies before main-branch publication. Image gates now include unfixed HIGH/CRITICAL vulnerabilities. Weekly maintenance checks source, fetched history, all dependency locks and both application images without cloud credentials or deployment. Remote scan results and required-check enforcement are recorded separately.
- **SQLite removed from the runtime (2026-11-03)**: removed the unused SQLite library and Python extension together, retaining package-manager consistency and the existing runtime dependencies. Verification rejects SQLite files, modules or package records in the final image.
- **Backend OS advisory reduction (2026-11-03)**: replaced or removed components associated with eight of the previous nine HIGH advisories. Trivy reports no findings for the Alpine candidate, but SQLite CVE-2026-119373 remains affected and is tracked explicitly because the Alpine feed omits it. Full image reports now retain every severity, unfixed finding and package record in CI. See [dependency findings](docs/dependency-findings.md).
- **Frontend development advisories resolved (2026-11-03)**: removed the ESLint/minimatch dependency chain responsible for six moderate package findings. Full and production npm audits now report zero known findings, and both frontend workflows reject every audit severity. Reviewed native-tool provenance and Rust dependencies in addition to npm packages. Backend OS findings remain tracked separately.
- **Dependency follow-up (2026-11-02)**: updated Debian time-zone data and removed seven unused account-management/mount packages and dependencies from the backend runtime. Full OS scan records decreased from 185 to 176; distinct advisories remain unchanged. Corrected Python audits to include preinstalled tooling packages, and added report-to-lock coverage checks with 20 regression tests. Frontend compatibility experiments confirmed why the six moderate development findings remain. No audit threshold was lowered; see the [remaining findings](docs/dependency-findings.md).
- **Dependency and delivery review (2026-11-02)**: updated Python and JavaScript dependencies with current security fixes; pinned the changed workflows' Actions and container base images; added dependency audits in CI. Remaining moderate frontend development-tool findings and unfixed backend operating-system findings are recorded separately in the [verification record](docs/verification.md#local-dependency-and-delivery-review-2-november-2026). The backend runtime omits Python installation tools; frontend runtime images omit Node. Development tools stay outside both runtimes.
- **Local safety review (2026-11-02)**: restored Django's add permission check for application configuration. Public API failures now return safe error messages; database and serialization failures no longer become successful empty responses. Known HTTP errors and valid optional data retain their existing behavior.

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
- **Local backup and recovery tooling (2026-11-02)**: added PostgreSQL 16 logical exports, a checked media archive and versioned checksum manifest. Recovery uses a private snapshot and new labelled Docker resources, with no automatic cutover. Added 51 archive/operation tests and seven real Docker integration scenarios, including timeout, output-limit and database-restore failure cleanup. A separate Linux workflow exercises synthetic data without cloud credentials. The fifth batch was published after independent review, all 210 automated tests and the real recovery scenarios passed; CI also passed without redeploying the application. See the [release record](docs/verification.md#published-recovery-tooling-2-november-2026).
- **Lint regression coverage (2026-11-02)**: 16 frontend positive/negative lint examples and three Django-aware Pylint examples check that real mistakes still fail. Two additional component tests verify that error details appear only in development. The fourth batch was published after all 159 tests passed; see the [verification record](docs/verification.md#local-maintenance-review-2-november-2026).
- **Release-order regression coverage (2026-11-02)**: 23 offline tests exercise real Git histories and simulated Cloud Run metadata, including stale releases, documentation-only newer commits, legacy image tags, digest formats, traffic policies and safe failures. See [release maintenance](scripts/README.md).
- **Local safety review (2026-11-02)**: added 20 backend regression tests and seven offline restore-entry tests. The backend workflow now discovers all `scripts/*_test.py` tests when it runs. See the [verification record](docs/verification.md#local-safety-review-2-november-2026) for local results and deferred work.

- **S3 Storage Support** (2026-03-09, commit 016eef3)
  - Added flexible media storage configuration supporting three modes:
    1. Local filesystem (default, backward compatible)
    2. MinIO self-hosted S3-compatible storage
    3. AWS S3 cloud storage
  - Dependencies: django-storages==1.14.4, boto3==1.35.36
  - Environment-based configuration using USE_S3 flag
  - Created S3_STORAGE_GUIDE.md with comprehensive setup instructions
  - Added docker-compose.minio.yml for quick MinIO deployment
  - Added backend/.env.example with configuration examples for all three modes
  - Storage tests: 2 new tests for storage configuration validation
  - Full backward compatibility - existing local storage deployments unaffected

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
- **GitHub Pages deep links (2026-11-02)**: generate a custom error document that loads the application at the original story URL, including direct opens and refreshes. Two build/HTTP tests check the fallback and resource responses before the Pages artifact is uploaded.
- **Frontend lifecycle review (2026-11-02)**: missing linked words remain readable without becoming drop targets or allowing false completion. Route changes, retries and unmounts cancel obsolete requests and ignore late results. Audio stops with its owning content; blocked or failed playback can be retried without stale callbacks changing the new state. Cancelling a drag clears its overlay and page state.
- **Frontend regression coverage (2026-11-02)**: 54 new tests cover valid and incomplete stories, answer completion across paragraphs, drag cancellation, HTTP errors, overlapping requests, route changes before effects run, unmounts, StrictMode and audio lifecycle events.
- **Legacy Cloud Run release metadata (2026-11-02)**: identify the old source commit when Cloud Run resolves a revision image tag into a digest. The service template must be fully reconciled and bound to the revision serving all traffic. Added nine regression tests for successful transitions and unsafe or incomplete metadata.

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
- Additional frontend test coverage

### Recently Resolved
- ✅ S3 storage support for media files (2026-03-09) - Supports local/MinIO/AWS S3
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
