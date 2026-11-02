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
npm audit
npm run lint
npm run format:check
npm run test:lint
npm test -- run
npm run build
npm run test:pages
```

The unit and component tests cover content, answer validation, request ownership and audio lifecycle, using controlled HTTP and media behavior. The separate Pages checks inspect the generated files and their HTTP responses. Neither suite substitutes for browser gameplay checks; the latest local results and browser scope are recorded in [verification](../docs/verification.md#frontend-tooling-migration-3-november-2026).

### JavaScript, React and type checks

`npm run lint` runs two required checks:

1. **Oxlint** reads `oxlint.config.mjs`. It checks JavaScript, React, Hooks and
   environment boundaries. Browser code cannot use Node globals; build scripts
   use Node globals; tests require explicit Vitest imports. Unused suppression
   comments also fail the check.
2. **TypeScript checkJs** checks the existing JavaScript/JSX using `jsconfig.json`.
   JSDoc describes API data, component props, contexts and browser references.
   It does not compile a second application or add a browser dependency. Tests
   and build scripts retain lint and syntax checks without application-level
   semantic type checking.

The migration reviews the intent of the previous **61 JavaScript, 19 React and
2 Hooks rules**. Most map directly to Oxlint. The remaining checks use the parser,
JSX reference tracking, or TypeScript:

- Component prop contracts use strict checkJs and JSDoc. Missing and incorrectly
  typed props fail.
  A PropTypes assignment alone no longer satisfies the static check.
- Removed React APIs fail against the installed React type definitions.
  `react/no-unsafe` also rejects deprecated lifecycle names and their `UNSAFE_`
  aliases; this is stricter than the previous React 19 deprecation check.
- `scripts/lint-component-names.mjs` covers anonymous React `memo`/`forwardRef`
  callbacks that Oxlint's display-name rule currently misses. It reuses the
  TypeScript program to distinguish React APIs from unrelated local functions.
- A syntax pass also rejects legacy octal literals in CommonJS scripts.

`npm run test:lint` runs 229 positive and negative examples against the actual
configuration and type checker, including rule options, file scopes, suppression
comments and command failure. This preserves the reviewed checks without
claiming that two different analysis engines behave identically for every
possible program. Keep these examples when updating either tool.

Prettier remains the formatting check. Type annotations describe contracts;
they do not validate JSON returned by a server at runtime.

## Dependency maintenance

The 3 November 2026 frontend tooling migration replaces ESLint 9 and its React
plugins with **Oxlint 1.90.0 and TypeScript 6.0.3**. React, Vite, the application
runtime and Prettier are retained. Use Node 24 and `npm ci` to install the reviewed
lock; update `package.json` and `package-lock.json` together.

### Remaining development dependency findings

The previous six moderate package findings came from one minimatch advisory,
[GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249), in the
ESLint dependency tree. That tree is now removed. Fresh full and production-only
npm audits report **zero known findings**. Both CI workflows now fail on any
audit severity, including low and moderate development findings.

The review also checked the native linter, beyond npm's advisory database:
registry signatures, release provenance, and the Rust dependency lock at the
verified Oxlint release commit. See [dependency findings](../docs/dependency-findings.md)
and [verification](../docs/verification.md) for the dated results and their scope.
The optional Go-based `oxlint-tsgolint` tool is not installed; checkJs uses the
TypeScript package instead.

Future releases can introduce new advisories. Repeat the checks above after
updating dependencies; do not force incompatible overrides or weaken rules to
make an audit pass. Useful references are the [Oxlint migration guide](https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html)
and [TypeScript JavaScript checking guide](https://www.typescriptlang.org/docs/handbook/type-checking-javascript-files.html).

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
