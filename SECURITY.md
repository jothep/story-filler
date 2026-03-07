# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by creating a GitHub issue or contacting the maintainers directly.

## Security Updates

This document tracks security vulnerabilities and their resolutions in the Maori Story Filler project.

---

## [2026-03-08] Frontend NPM Dependency Vulnerabilities - RESOLVED

### Summary
Fixed 5 HIGH severity vulnerabilities in frontend npm dependencies affecting minimatch, rollup, react-router, and other packages.

### Affected Components
- **Frontend Application**: npm dependencies

### Vulnerabilities Fixed

#### 1. minimatch (v10.1.2 → v10.2.3+)
- **CVE-2026-26996** (HIGH): Denial of Service via specially crafted glob patterns
- **CVE-2026-27903** (HIGH): Denial of Service due to unbounded recursive backtracking
- **CVE-2026-27904** (HIGH): Denial of Service via catastrophic backtracking in glob expressions
- **Impact**: ReDoS (Regular Expression Denial of Service) attacks could cause application hangs
- **Resolution**: Updated to minimatch v10.2.3+

#### 2. rollup (v4.52.5 → v4.59.0)
- **CVE-2026-XXXXX** (HIGH): Arbitrary File Write via Path Traversal
- **Impact**: Potential for malicious file operations during build process
- **Resolution**: Updated to rollup v4.59.0

#### 3. react-router (v7.0.0-7.12.0 → latest)
- **GHSA-h5cw-625j-3rxh** (HIGH): CSRF issue in Action/Server Action Request Processing
- **GHSA-2w69-qvjg-hvjx** (HIGH): XSS via Open Redirects
- **GHSA-8v8x-cx79-35w7** (HIGH): SSR XSS in ScrollRestoration
- **GHSA-9jcx-v3wj-wh4m** (HIGH): Unexpected external redirect via untrusted paths
- **Impact**: Cross-Site Scripting and CSRF vulnerabilities
- **Resolution**: Updated to patched react-router version

#### 4. ajv (< v6.14.0)
- **GHSA-2g4f-4pwh-qvx6** (MODERATE): ReDoS when using `$data` option
- **Impact**: Denial of Service via malicious JSON schemas
- **Resolution**: Updated to ajv v6.14.0+

#### 5. js-yaml (v4.0.0-4.1.0)
- **GHSA-mh29-5h37-fv8m** (MODERATE): Prototype pollution in merge (`<<`)
- **Impact**: Potential for prototype pollution attacks
- **Resolution**: Updated to patched js-yaml version

### Resolution Details
- **Date**: 2026-03-08
- **Action Taken**: Ran `npm audit fix` in frontend directory
- **Packages Updated**: 10 packages
- **Verification**:
  - ✅ All tests passing (`npm test`)
  - ✅ Linting passing (`npm run lint`)
  - ✅ `npm audit` reports 0 vulnerabilities

### References
- [npm audit documentation](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [GitHub Advisory Database](https://github.com/advisories)

---

## [2026-03-08] Docker Image Vulnerabilities from `serve` Package - IN PROGRESS

### Summary
Trivy security scan detected 5 HIGH severity vulnerabilities in the frontend Docker image, originating from the `serve` package's dependencies (minimatch and tar).

### Affected Components
- **Frontend Docker Image**: `serve` package installed via `npm install -g serve`

### Vulnerabilities Detected

#### 1. minimatch (package.json - from serve dependencies)
- **CVE-2026-26996** (HIGH): Denial of Service via specially crafted glob patterns
- **CVE-2026-27903** (HIGH): Denial of Service due to unbounded recursive backtracking
- **CVE-2026-27904** (HIGH): Denial of Service via catastrophic backtracking
- **Installed Version**: 10.1.2 or 3.1.5 (depending on serve's dependency tree)
- **Fixed Version**: 10.2.3+, 9.0.7+, 8.0.6+, etc.

#### 2. tar (package.json - from serve dependencies)
- **CVE-2026-26960** (HIGH): Arbitrary file read/write via malicious archive hardlink creation
- **CVE-2026-29786** (HIGH): Hardlink Path Traversal via Drive-Relative Linkpath
- **Installed Version**: 7.5.7
- **Fixed Version**: 7.5.10+

### Root Cause Analysis
- Application's `package-lock.json` was already updated with secure versions
- However, the Docker image installs `serve` globally: `npm install -g serve`
- This bypasses the application's `package-lock.json` and uses `serve`'s own dependencies
- `serve` package may have outdated transitive dependencies (minimatch, tar)

### Resolution Approach (Option 1 - ATTEMPTING)
**Updated frontend Dockerfile to use latest serve version:**
```dockerfile
# Before:
RUN npm install -g serve

# After:
RUN npm cache clean --force && npm install -g serve@latest
```

**Changes Made:**
- Force clean npm cache to ensure fresh dependency resolution
- Explicitly install `serve@latest` to get the most recent version
- This should pull in updated dependencies with security patches

**Status**: Testing in CI/CD pipeline
- If successful: Trivy scan will pass with 0 HIGH/CRITICAL vulnerabilities
- If unsuccessful: Will implement Option 2 (nginx-based image)

### Alternative Solution (Option 2 - BACKUP PLAN)
Replace `serve` with `nginx:alpine` for production serving:
- **Benefits**:
  - Smaller image size (~20MB vs ~180MB)
  - No Node.js runtime dependencies
  - Better performance for static file serving
  - nginx has better security maintenance
- **Trade-off**: Different technology stack (nginx vs Node.js)
- **Implementation**: Use `frontend/Dockerfile.nginx` (already prepared)

### Timeline
- **2026-03-08 22:30**: Issue identified in Trivy scan
- **2026-03-08 22:45**: Option 1 implemented, waiting for CI/CD validation
- **Next**: If Option 1 fails, will implement Option 2 immediately

### Verification Steps
1. ✅ Updated Dockerfile with `serve@latest`
2. ⏳ Waiting for CI/CD to rebuild Docker image
3. ⏳ Waiting for Trivy scan results
4. ⏳ If scan passes, vulnerability resolved
5. ⏳ If scan fails, switch to nginx approach

---

## Security Best Practices

### For Contributors
1. **Always run `npm audit`** before committing dependency updates
2. **Run automated security scans** via GitHub Actions (Trivy)
3. **Keep dependencies up to date** to receive security patches
4. **Review security advisories** for critical dependencies

### For Deployers
1. **Use environment variables** for all secrets (never hardcode)
2. **Regularly update Docker base images** to get OS-level security patches
3. **Monitor CI/CD pipeline** for Trivy vulnerability scan results
4. **Enable dependabot** or similar tools for automatic security updates

### Current Security Measures
- ✅ Automated Trivy scanning in CI/CD pipeline
- ✅ Docker multi-stage builds to minimize attack surface
- ✅ Non-root user in Docker containers
- ✅ CORS configured with explicit allowed origins
- ✅ Django SECRET_KEY stored in environment variables
- ✅ Input validation and sanitization in Django models
- ✅ Automated testing in CI/CD pipeline
- ✅ ESLint security rules enabled
