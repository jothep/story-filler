# Frontend Application (React/MUI)

This is the Single Page Application (SPA) built with React, Vite, and Material-UI (MUI).

---

### Getting Started (Local Development)

This project uses Node.js **v24** for development and CI.

1.  **Install Dependencies:**
    ```bash
    npm ci
    ```
2.  **Run Locally (Development Mode):**
    ```bash
    npm run dev
    ```
    The application should be available at `http://localhost:5173`.
    *Note: Remember to run your Django backend for API calls to work.*

### Continuous Integration (CI) Checks

To ensure your local environment matches the pipeline before pushing code, use these commands:

| CI Step | Local Command | Purpose |
| :--- | :--- | :--- |
| **Install** | `npm ci` | Strict install using `package-lock.json`. |
| **Lint** | `npm run lint` | Static code analysis. |
| **Test** | `npm test -- run` | Execute unit tests (Vitest). |
| **Build** | `npm run build` | Generate production files for Docker. |

### Docker & Deployment

The CI pipeline automatically builds and pushes the image:

1.  **Dockerfile Context:** `./frontend`
2.  **Base Image:** `nginx:1.27-alpine` (Multistage build)
3.  **Key Configuration:** A custom `nginx.conf` is used to ensure Single Page Application (SPA) routing works correctly (e.g., refreshing a nested URL does not result in a 404).

---