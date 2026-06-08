# Draft PR: Frontend Amplify Deployment Review

## Summary

This draft PR documents the likely causes of the AWS Amplify frontend deployment failure for the BakerProfit OS application, where the backend is deployed on Railway and the frontend is deployed on AWS Amplify.

No application source code changes are proposed in this draft. The goal is to provide a reviewable deployment diagnosis and a concrete remediation checklist before changing build or runtime configuration.

## Current Architecture Observed

- Backend: FastAPI application served by Railway through `Procfile` using `uvicorn app.main:app`.
- Backend API prefix: all v1 API routers are mounted under `/api/v1`.
- Backend health endpoint: `/health`.
- Frontend: Vite + React application located in `frontend/`.
- Frontend deployment target: AWS Amplify static hosting.
- Frontend build command: `tsc -b && vite build`.
- Amplify build spec: repository-root `amplify.yml` that runs `cd frontend && npm ci` and `cd frontend && npm run build`.

## Findings

### 1. Node version mismatch is the most likely build failure

The frontend currently uses many `latest` package ranges in `frontend/package.json`, including Vite, TypeScript, ESLint, React Router, and the Vite React plugin.

The current lockfile resolves to packages that require modern Node versions:

- `vite@8.0.16` requires Node `^20.19.0 || >=22.12.0`.
- `@vitejs/plugin-react@6.0.2` requires Node `^20.19.0 || >=22.12.0`.
- `react-router-dom@7.17.0` requires Node `>=20.0.0`.

The build succeeds locally with Node `v20.20.2`, but Amplify may fail if the configured build image or app settings use an older Node runtime.

#### Suggested fix

Pin the Node version in `amplify.yml` before installing dependencies:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - nvm install 22
        - nvm use 22
        - cd frontend && npm ci
    build:
      commands:
        - cd frontend && npm run build
  artifacts:
    baseDirectory: frontend/dist
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

Alternatively, pin dependencies to versions compatible with the Amplify build image currently in use.

### 2. Amplify app-root configuration must match `amplify.yml`

The committed `amplify.yml` assumes Amplify starts from the repository root and then changes into `frontend/` manually.

This is valid only when Amplify is configured with the repository root as the app root.

If Amplify is configured as a monorepo app with app root set to `frontend`, the current commands can fail because Amplify may already be executing from the frontend folder. In that case, `cd frontend` would point to a non-existent nested folder.

#### Suggested fix for repo-root mode

Keep the existing shape of `amplify.yml` and verify that Amplify is not separately configured with app root `frontend`.

#### Suggested fix for monorepo mode

Use Amplify's monorepo `applications` syntax and remove `cd frontend` from commands:

```yaml
version: 1
applications:
  - appRoot: frontend
    frontend:
      phases:
        preBuild:
          commands:
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: dist
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
```

Only one of these approaches should be used.

### 3. Missing `VITE_API_BASE_URL` will break the deployed frontend at runtime

The frontend API client uses this fallback:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';
```

If `VITE_API_BASE_URL` is not set in Amplify, the production bundle will call `localhost:8000`, which works only during local development and fails from an Amplify-hosted browser session.

#### Suggested fix

Add this environment variable in Amplify:

```bash
VITE_API_BASE_URL=https://<railway-backend-domain>/api/v1
```

Then redeploy the frontend. Vite embeds `VITE_*` variables at build time, so changing this value requires a new Amplify build.

### 4. Railway CORS must include Amplify origins

The backend default CORS origins are local development URLs only:

```bash
http://localhost:5173,http://localhost:4173,http://localhost:3000
```

The FastAPI app uses those origins for `CORSMiddleware`.

If Railway does not override `CORS_ORIGINS`, browser requests from Amplify will be blocked by CORS even if the frontend deploy succeeds.

#### Suggested fix

Set this environment variable in Railway:

```bash
CORS_ORIGINS=https://<amplify-domain>,https://<custom-frontend-domain>,http://localhost:5173,http://localhost:4173
```

### 5. Lint currently fails if deployment runs it

The package defines:

```json
"lint": "eslint ."
```

But the repository does not include an ESLint flat config file. With the currently installed ESLint version, `npm run lint` fails because ESLint cannot find `eslint.config.js`, `eslint.config.mjs`, or `eslint.config.cjs`.

The committed Amplify build spec does not run lint, so this is not necessarily the current deployment blocker. However, it can break Amplify if the console build settings or future CI changes include linting.

#### Suggested fix

Add an ESLint config compatible with the installed ESLint version, pin ESLint to a known supported version, or remove the lint script until linting is configured.

### 6. BrowserRouter requires Amplify SPA rewrites

The frontend uses `BrowserRouter`, so static hosting must rewrite deep links such as `/dashboard`, `/orders`, and `/reports` back to `/index.html`.

Without this, direct navigation or browser refresh on nested routes can return 404 even after a successful deployment.

#### Suggested fix

Add an Amplify rewrite rule that serves `/index.html` for frontend application routes.

## Verification Performed

The following checks were run locally from this repository:

```bash
cd frontend && npm ci
cd frontend && npm run build
cd frontend && npm run lint
node -v && npm -v
git status --short --ignored
```

Results:

- `npm ci` passed.
- `npm run build` passed.
- `npm run lint` failed due to missing ESLint flat config.
- Local Node version was `v20.20.2` and npm version was `11.4.2`.
- No source files were modified during the initial inspection.

## Recommended Order of Operations

1. Confirm the exact Amplify failure log.
2. Confirm whether Amplify is building from repository root or from app root `frontend`.
3. Pin Amplify Node to Node 22 or at least Node 20.19+.
4. Set Amplify `VITE_API_BASE_URL` to the Railway backend `/api/v1` URL.
5. Set Railway `CORS_ORIGINS` to include the Amplify and custom frontend domains.
6. Add Amplify SPA rewrite rules for React Router routes.
7. Decide whether to add ESLint config or remove the current lint script.
8. Replace broad `latest` frontend dependency ranges with pinned or bounded semver ranges.

## Proposed Follow-up Code Changes

This draft does not change source code. A follow-up implementation PR could include:

- Updating `amplify.yml` to pin Node and match the selected Amplify app-root strategy.
- Adding `engines` to `frontend/package.json`.
- Replacing `latest` dependency ranges with stable semver ranges.
- Adding an ESLint flat config or removing the lint script.
- Adding deployment documentation for Amplify and Railway environment variables.

## Review Questions

- Is Amplify currently configured to build from the repository root or from `frontend`?
- What Node version appears in the failing Amplify build log?
- Is `VITE_API_BASE_URL` currently set in Amplify?
- Are all active Amplify/custom domains included in Railway `CORS_ORIGINS`?
- Should the repository standardize on Node 22 for frontend builds?
