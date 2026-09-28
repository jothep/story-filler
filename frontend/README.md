# Story Filler frontend

The maintained application uses React, Vite, React Router and NES.css. The separate MUI prototype is under `demo/`; it is not this frontend.

## Local development

For the four-service local environment, use the root [Compose instructions](../docs/local-platform-lab.md). Its frontend URL is `http://localhost/story-filler/`, and Nginx routes same-origin API requests to Django.

For a host-run frontend, install dependencies and start Vite from this directory:

```bash
npm ci
npm run dev
```

Open `http://localhost:5173/story-filler/`. Use a Node version supported by the locked Vite version (20.19+, 22.12+, or 24). The checked-in Vite proxies expect a separately prepared backend/Ingress entry point at `http://127.0.0.1:8080`; running Vite alone does not start that service or provide story data. `VITE_API_URL` can instead select an explicit API origin at build/start time, with corresponding backend CORS configuration. Keep local credentials in ignored local files.

The Vite base is `/story-filler/`. The router and error recovery derive their base from Vite, and imported assets are rewritten during the build.

## Checks

```bash
npm run lint
npm test -- run
npm run build
```

The six component tests mock HTTP and audio. A build verifies asset generation; it does not prove a deployment or complete browser gameplay.

## Serving the build

- GitHub Pages publishes `dist` at `https://jothep.github.io/story-filler/`. Navigation from the menu uses React Router. Directly opening or refreshing a nested story URL on Pages still needs a hosting fallback; this repository does not add one.
- `Dockerfile` uses `serve` on port 3000. Production-style Compose puts Nginx in front and strips `/story-filler/` before proxying to it.
- `Dockerfile.nginx` serves the build under `/usr/share/nginx/html/story-filler/` on port 80, using `nginx.conf` for the prefix and SPA fallback. The manual image workflow uses this file; Docker Hub push is optional, defaults off and requires separately configured credentials that were not migrated. Historical Kubernetes image tags are retained in `Infra/`; rebuild and select a matching new image before reproducing the lab.

The Nginx image source and Compose configuration have been reviewed for the migrated path. A fresh container build/start and cluster exercise remain separate checks; see the [migration record](../docs/repository-migration.md).
