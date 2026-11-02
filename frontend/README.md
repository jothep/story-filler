# Story Filler frontend

The maintained application uses React, Vite, React Router and NES.css. The separate MUI prototype is under `demo/`; it is not this frontend.

## Local development

For the four-service local environment, use the root [Compose instructions](../docs/local-platform-lab.md). Its frontend URL is `http://localhost/story-filler/`, and Nginx routes same-origin API requests to Django.

For a host-run frontend, use Node 24, install the locked dependencies and start Vite from this directory:

```bash
nvm use
npm ci
npm run dev
```

`.nvmrc`, the package engine, CI and the Docker build stages use Node 24. If you do not use nvm, select Node 24 with your own version manager. This is a supported LTS release until April 2028; see the [Node release schedule](https://github.com/nodejs/Release#release-schedule).

Open `http://localhost:5173/story-filler/`. The checked-in Vite proxies expect a separately prepared backend/Ingress entry point at `http://127.0.0.1:8080`; running Vite alone does not start that service or provide story data. `VITE_API_URL` can instead select an explicit API origin at build/start time, with corresponding backend CORS configuration. Keep local credentials in ignored local files.

The Vite base is `/story-filler/`. The router and error recovery derive their base from Vite, and imported assets are rewritten during the build.

## Checks

```bash
npm audit --omit=dev
npm audit --audit-level=high
npm run lint
npm test -- run
npm run build
```

The six component tests mock HTTP and audio. A build verifies asset generation; it does not prove a deployment or complete browser gameplay.

## Dependency maintenance

The 2 November 2026 update retained the current React application and lint rules. The main locked-version changes were:

| Package | Previous lock | Current lock |
| --- | --- | --- |
| React Router DOM | 7.13.1 | 7.18.5 |
| Vite | 7.3.2 | 7.3.7 |
| Vitest | 3.2.4 | 4.1.12 |
| jsdom | 27.0.1 | 27.4.0 |
| Vite React plugin | 5.0.4 | 5.2.0 |
| ESLint and `@eslint/js` | 9.38.0 | 9.39.5 |

Unused `vite-plugin-eslint` and `eslint-plugin-react-refresh` dependencies were removed. ESLint runs as its own required check. Compatible transitive updates are recorded in `package-lock.json`; use `npm ci` to install that selection.

On Node 24.22.2, lint, all six tests and the production build passed. The npm audit snapshot changed from 25 affected packages (2 critical, 10 high, 11 moderate and 2 low) to 6 moderate findings. The production dependency audit reported no known vulnerabilities. These are dated results, so both audit commands run again in CI.

### Remaining development dependency findings

The six remaining moderate findings share [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249): `minimatch` and five affected parent packages in the ESLint dependency tree. The advisory describes excessive CPU and memory use from an attacker-controlled glob pattern with `optimizationLevel >= 2`; its fixed version is 11.0.1. This tree belongs to development tooling, not the browser bundle or the Nginx runtime image. The audit result still needs to be tracked.

The current `eslint-plugin-react` release supports ESLint through version 9. Moving its transitive dependencies to minimatch 11 is outside their declared ranges. We have not forced an override, downgraded packages to silence audit, or removed existing lint rules. Full audit fails CI for high or critical findings; production audit fails for any reported severity. Moderate development findings stay visible in the log.

[ESLint 9 reached end of life on 6 August 2026](https://eslint.org/version-support/). Version 9.39.5 is a temporary compatibility choice, not the completed maintenance target. The next lint-maintenance change must move to a supported ESLint version with compatible React rules, preserve the existing checks and rerun the full audit. Recheck the minimatch advisory then; upgrading ESLint alone does not establish that its entire dependency tree is fixed.

For later dependency changes, update package and lock files together, run the checks above, and review major-version migration notes. Do not use `npm audit fix --force` as a substitute for a compatibility review.

## Serving the build

- GitHub Pages publishes `dist` at `https://jothep.github.io/story-filler/`. Navigation from the menu uses React Router. Directly opening or refreshing a nested story URL on Pages still needs a hosting fallback; this repository does not add one.
- `Dockerfile` uses Nginx on port 3000. Production-style Compose keeps the same URL contract: its outer Nginx strips `/story-filler/` before proxying to this internal service. `nginx.root.conf` serves the resulting root paths and supplies the SPA fallback. Missing build assets return 404.
- `Dockerfile.nginx` serves the build under `/usr/share/nginx/html/story-filler/` on port 80, using `nginx.conf` for the prefix and SPA fallback. The manual image workflow uses this file; Docker Hub push is optional, defaults off and requires separately configured credentials that were not migrated. Historical Kubernetes image tags are retained in `Infra/`; rebuild and select a matching new image before reproducing the lab.

Both production images copy only the built static assets into their Nginx runtime stage. Node, npm, test tools and the previous globally installed `serve` package are absent from that stage. Development uses `Dockerfile.dev` and Vite on port 5173.

The Dockerfiles pin official base-image digests. The lock file and digests fix the selected npm dependencies and base images. Runtime stages also apply available Alpine package updates at build time, so builds are not byte-for-byte reproducible across dates. When refreshing image digests, rebuild and scan the resulting runtime images as well as running the npm checks; npm audit does not cover operating-system packages.

## Frontend workflows

`deploy-frontend.yml` validates frontend pull requests with read-only repository access, no deployment configuration and no cloud credentials. It runs dependency audits, lint, tests and a build. Only a successful non-PR run on `main` uploads and deploys the Pages artifact. That build requires the existing `CLOUD_RUN_URL` secret as `VITE_API_URL`; the API URL becomes public frontend configuration in the output, so never put a credential in it. Pages write and identity-token permissions are limited to the deployment job.

`build-frontend-docker.yml` is manual. It repeats the npm checks, builds the standalone Nginx image and scans it with Trivy. High and critical image findings fail the job, including findings without an available fix. An optional Docker Hub push is allowed only from `main`, after the checks pass. Actions and the Trivy engine are version-pinned and should be reviewed during dependency updates.

On 2 November 2026, both production images passed local HTTP checks for the entry HTML, nested story routes, JavaScript asset responses and missing-asset 404s. The standalone root redirect and the existing Compose proxy's `/story-filler/` to port 3000 mapping also passed. Trivy 0.76.1 reported no known vulnerabilities in either built runtime image. These checks do not run the full application against a database or exercise a Kubernetes cluster; see the [migration record](../docs/repository-migration.md) for that separate scope.
