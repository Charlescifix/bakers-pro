---
name: Amplify Deployment Failure
about: Track Amplify frontend deployment failures and Railway integration settings
title: "Amplify: frontend deployment failure"
labels: deployment
assignees: ''
---

# Amplify frontend deployment fails or deploys with broken Railway API integration

## Summary

The BakerProfit OS frontend can fail during AWS Amplify builds, or deploy successfully but fail to call the Railway backend, because frontend build/runtime configuration was not fully pinned for the current Vite toolchain and Railway deployment flow.

## Findings

- Amplify must build with a Node runtime compatible with the current Vite toolchain. The frontend now declares `node >=20.19.0`, and `amplify.yml` explicitly selects Node 22 before `npm ci`.
- Frontend dependencies were previously declared with broad `latest` ranges. This made future lockfile refreshes risky because build tooling could upgrade without review.
- `npm run lint` previously failed because ESLint was installed without a flat config file; it now runs ESLint, the local TypeScript lint pass, and `tsc -b`.
- TypeScript 6 is verified by `npm run build` and `npm run lint`, both of which run `tsc -b`; no frontend Zod imports were found in `frontend/src` during review.
- Amplify must define `VITE_API_BASE_URL=https://<railway-backend-domain>/api/v1`; otherwise the Vite production bundle falls back to localhost.
- Railway must define `CORS_ORIGINS` with every active Amplify/custom frontend origin.
- Amplify app-root settings must match the checked-in `amplify.yml`: this repository-level build spec assumes the build starts at the repository root and then runs commands in `frontend/`.
- Because the frontend uses React Router `BrowserRouter`, Amplify needs an SPA rewrite rule that serves `/index.html` for application routes.

## Acceptance criteria

- [ ] Amplify build logs show Node 22 before dependency installation.
- [ ] `cd frontend && npm ci` passes.
- [ ] `cd frontend && npm run build` passes.
- [ ] `cd frontend && npm run lint` passes.
- [ ] Amplify `VITE_API_BASE_URL` points to the Railway backend `/api/v1` URL.
- [ ] Railway `CORS_ORIGINS` includes the Amplify domain and any custom frontend domains.
- [ ] Amplify app-root configuration matches the repository-root `amplify.yml` strategy.
- [ ] Amplify rewrite rules support direct visits to frontend routes such as `/dashboard`.

## Implementation notes

This repository fix PR handles the commit-able items: Node pinning in Amplify, dependency range pinning, frontend `engines`, ESLint configuration, and the local TypeScript lint pass. Deployment owners still need to apply the Amplify and Railway console environment-variable/rewrite settings.
