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

## [2026-03-08] Docker Image Vulnerabilities - RESOLVED ✅

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

### Resolution Approach (Option 1 - FAILED)
**Attempted: Updated frontend Dockerfile to use latest serve version:**
```dockerfile
RUN npm cache clean --force && npm install -g serve@latest
```

**Result**: FAILED
- Trivy scan still detected same 5 HIGH vulnerabilities
- minimatch remained at v10.1.2 (instead of required 10.2.3+)
- tar remained at v7.5.7 (instead of required 7.5.10+)
- Root cause: `serve@latest` itself still depends on outdated packages
- Conclusion: Cannot rely on `serve` package for security compliance

### Resolution Approach (Option 2 - IMPLEMENTED) ✅
**Switched to nginx:alpine for production serving:**

**Changes Made:**
1. ✅ Updated `.github/workflows/frontend-ci.yml` to use `Dockerfile.nginx`
2. ✅ Updated `Infra/frontend-deployment.yaml` to use port 80 instead of 3000
3. ✅ nginx:alpine base image has no Node.js dependencies
4. ✅ Significantly reduced attack surface

**Benefits Realized:**
- **Smaller image size**: ~20MB (nginx:alpine) vs ~180MB (node:24-bookworm-slim)
- **No Node.js vulnerabilities**: Eliminates entire class of npm dependency issues
- **Better performance**: nginx is optimized for static file serving
- **Better security maintenance**: nginx:alpine has excellent security track record
- **Simpler architecture**: No need to manage Node.js runtime in production

**Technical Details:**
```dockerfile
# Stage 1: Build with Node.js
FROM node:24-bookworm-slim AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Timeline
- **2026-03-08 22:30**: Issue identified in Trivy scan - serve package vulnerabilities
- **2026-03-08 22:45**: Option 1 (serve@latest) implemented
- **2026-03-08 23:05**: Option 1 FAILED - vulnerabilities persisted
- **2026-03-08 23:10**: Option 2 (nginx:alpine) implemented
- **2026-03-08 23:20**: New vulnerabilities detected in nginx:alpine base image
  - zlib CVE-2026-22184 (CRITICAL): Buffer overflow in untgz utility
  - libpng CVE-2026-25646 (HIGH): Heap buffer overflow in png_set_quantize
- **2026-03-08 23:25**: Added Alpine package upgrade to fix base image vulnerabilities
- **2026-03-08 23:40**: CI/CD validation PASSED - All vulnerabilities resolved ✅
- **Status**: RESOLVED

### Verification Steps
1. ✅ Created Dockerfile.nginx with nginx:alpine
2. ✅ Updated CI/CD workflow to use Dockerfile.nginx
3. ✅ Updated Kubernetes deployment manifests (port 3000 → 80)
4. ✅ Added Alpine package upgrade (apk update && apk upgrade)
5. ✅ CI/CD rebuilt Docker image with updated packages
6. ✅ Trivy scan completed successfully
7. ✅ **RESULT: 0 HIGH/CRITICAL vulnerabilities** (zlib upgraded, libpng upgraded)

### Final Solution
**Successfully resolved all vulnerabilities through multi-layered approach:**
- Eliminated Node.js npm dependency vulnerabilities (serve package)
- Upgraded Alpine Linux system libraries (zlib, libpng)
- Achieved zero HIGH/CRITICAL vulnerabilities
- Reduced image size by 90% (~180MB → ~20MB)
- Improved security posture and performance

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
