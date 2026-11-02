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
npm run format:check
npm run test:lint
npm test -- run
npm run build
npm run test:pages
```

The unit and component tests cover content, answer validation, request ownership and audio lifecycle, using controlled HTTP and media behavior. The separate Pages checks inspect the generated files and their HTTP responses. Neither suite substitutes for browser gameplay checks; the latest local results and browser scope are recorded in [verification](../docs/verification.md#local-frontend-lifecycle-review-2-november-2026).

### Lint coverage

`eslint.config.js` separates browser application code, Node build/check scripts,
and Vitest tests. Application code retains all 19 previously enabled React rules
and now also checks the Rules of Hooks and complete effect dependencies. Browser
code cannot rely on Node globals such as `process`; Vite configuration and build
scripts use the Node environment. Tests and shared test helpers are checked rather
than ignored, with JSX name checks and explicit imports for Vitest APIs.

`npm run test:lint` runs 16 positive and negative examples against the actual
configuration. They cover list keys, duplicate props, component names, DOM props,
prop declarations, class render returns, unsafe child markup, Hooks, and the
browser/Node/test boundaries. This detects a disabled or mis-scoped check even
when the application itself currently passes lint.

## Dependency maintenance

The 2 November 2026 update retained the current React application and lint rules. The main locked-version changes were:

| Package                 | Previous lock | Current lock |
| ----------------------- | ------------- | ------------ |
| React Router DOM        | 7.13.1        | 7.18.5       |
| Vite                    | 7.3.2         | 7.3.7        |
| Vitest                  | 3.2.4         | 4.1.12       |
| jsdom                   | 27.0.1        | 27.4.0       |
| Vite React plugin       | 5.0.4         | 5.2.0        |
| ESLint and `@eslint/js` | 9.38.0        | 9.39.5       |

Unused `vite-plugin-eslint` and `eslint-plugin-react-refresh` dependencies were removed. ESLint runs as its own required check. Compatible transitive updates are recorded in `package-lock.json`; use `npm ci` to install that selection.

The dependency review used Node 24.22.2 and passed lint, the component tests and the production build. The npm audit snapshot changed from 25 affected packages (2 critical, 10 high, 11 moderate and 2 low) to 6 moderate findings. The production dependency audit reported no known vulnerabilities. These are dated results, so both audit commands run again in CI.

### Remaining development dependency findings

The six remaining moderate findings share [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249): `minimatch` and five affected parent packages in the ESLint dependency tree. The advisory describes excessive CPU and memory use from an attacker-controlled glob pattern with `optimizationLevel >= 2`; its fixed version is 11.0.1. This tree belongs to development tooling, not the browser bundle or the Nginx runtime image. The audit result still needs to be tracked.

Full audit fails CI for high or critical findings; production audit fails for any reported severity. Moderate development findings stay visible in the log.

[ESLint 9 reached end of life on 6 August 2026](https://eslint.org/version-support/). Version 9.39.5 remains a temporary compatibility choice. On 2 November 2026, the latest `eslint-plugin-react` release, 7.37.5, still declared ESLint support only through version 9. Its [ESLint 10 compatibility issue](https://github.com/jsx-eslint/eslint-plugin-react/issues/3977) remained open. Moving to another React lint plugin would require a separate rule-by-rule review because its recommended preset does not preserve all these checks.

The same review found no compatible minimatch patch that resolves the advisory: its affected range remains every version below 11.0.1. ESLint 9 and the React plugin require the 3.x range; ESLint 10.14.0 still requires the 10.x range. Updating ESLint alone therefore does not remove this finding. This maintenance change preserves the lock file and the six reported moderate findings; it does not force a minimatch major-version override or bypass peer dependencies. Recheck both the upstream React compatibility issue and the advisory before the next dependency update.

For later dependency changes, update package and lock files together, run the checks above, and review major-version migration notes. Do not use `npm audit fix --force` as a substitute for a compatibility review.

## Serving the build

- GitHub Pages publishes `dist` at `https://jothep.github.io/story-filler/`. Each build copies `index.html` to `404.html`, so opening or refreshing a nested story URL loads the same app and React Router handles the original path. The HTML retains Pages' HTTP 404 status; this is a client-side navigation fallback, not a server rewrite. Asset URLs remain absolute under `/story-filler/`, and missing assets still return 404. See GitHub's [custom 404 page documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-custom-404-page-for-your-github-pages-site).
- `Dockerfile` uses Nginx on port 3000. Production-style Compose keeps the same URL contract: its outer Nginx strips `/story-filler/` before proxying to this internal service. `nginx.root.conf` serves the resulting root paths and supplies the SPA fallback. Missing build assets return 404.
- `Dockerfile.nginx` serves the build under `/usr/share/nginx/html/story-filler/` on port 80, using `nginx.conf` for the prefix and SPA fallback. The manual image workflow uses this file; Docker Hub push is optional, defaults off and requires separately configured credentials that were not migrated. Historical Kubernetes image tags are retained in `Infra/`; rebuild and select a matching new image before reproducing the lab.

Both production images copy only the built static assets into their Nginx runtime stage. Node, npm, test tools and the previous globally installed `serve` package are absent from that stage. Development uses `Dockerfile.dev` and Vite on port 5173.

After building, `npm run test:pages` checks the fallback against the generated entry page and uses a local Pages-style server to check deep links, their JavaScript and CSS resources, and missing-asset responses. This runs in CI before the Pages artifact is uploaded. Vite preview alone does not reproduce Pages' missing-path response.

The Dockerfiles pin official base-image digests. The lock file and digests fix the selected npm dependencies and base images. Runtime stages also apply available Alpine package updates at build time, so builds are not byte-for-byte reproducible across dates. When refreshing image digests, rebuild and scan the resulting runtime images as well as running the npm checks; npm audit does not cover operating-system packages.

## Frontend workflows

`deploy-frontend.yml` validates frontend pull requests with read-only repository access, no deployment configuration and no cloud credentials. It runs dependency audits, lint, formatting, lint-rule checks, component tests, a build and Pages fallback checks. Only a successful non-PR run on `main` uploads and deploys the Pages artifact. That build requires the existing `CLOUD_RUN_URL` secret as `VITE_API_URL`; the API URL becomes public frontend configuration in the output, so never put a credential in it. Pages write and identity-token permissions are limited to the deployment job.

`build-frontend-docker.yml` is manual. It repeats the npm checks, builds the standalone Nginx image and scans it with Trivy. High and critical image findings fail the job, including findings without an available fix. An optional Docker Hub push is allowed only from `main`, after the checks pass. Actions and the Trivy engine are version-pinned and should be reviewed during dependency updates.

On 2 November 2026, both production images passed local HTTP checks for the entry HTML, nested story routes, JavaScript asset responses and missing-asset 404s. The standalone root redirect and the existing Compose proxy's `/story-filler/` to port 3000 mapping also passed. Trivy 0.76.1 reported no known vulnerabilities in either built runtime image. These checks do not run the full application against a database or exercise a Kubernetes cluster; see the [migration record](../docs/repository-migration.md) for that separate scope.
