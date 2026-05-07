---
name: ucsd-dsmlp-app
description: Use when building a UCSD campus-hostable web app package for review, Docker image build, GitHub intake, or DSMLP/Kubernetes deployment.
---

# UCSD DSMLP App Package

Use this skill whenever the user asks for a campus app, internal tool, dashboard, tracker, form, workflow, or any web app that may be hosted on UCSD infrastructure.

## Goal

Create a working Craft preview and a separate UCSD review package.

Craft preview:

```text
outputs/web/
```

UCSD review package:

```text
outputs/ucsd-package/
  app/
  app.manifest.json
  README.md
```

## Non-Negotiable Rules

- Do not directly deploy to DSMLP, Kubernetes, or GitHub.
- Do not create kubeconfigs, cluster credentials, namespace commands, or cluster-admin instructions.
- Do not write secrets, tokens, passwords, GitHub credentials, DSMLP credentials, or API keys into generated files.
- If runtime configuration is required, list it in `app.manifest.json`.
- Prefer Next.js for web apps unless the user clearly needs another runtime.
- Use mock data for prototypes unless the user provides real approved data.
- Keep uploaded/user-provided data handling explicit in the README.

## Package Contract

Create `outputs/ucsd-package/app/` as the runnable app package. It must include:

- `Dockerfile`
- `package.json`
- application source
- health endpoint matching the manifest

For Next.js, the health endpoint should normally be:

```text
outputs/ucsd-package/app/app/api/health/route.ts
```

The Dockerfile is built from `outputs/ucsd-package/app` as its build context. Use paths relative to that directory:

```dockerfile
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
```

Do not use `COPY app/package.json ...` inside `outputs/ucsd-package/app/Dockerfile`.

## Manifest

Create `outputs/ucsd-package/app.manifest.json`.

Default manifest:

```json
{
  "schema_version": "1",
  "app_name": "short-kebab-case-name",
  "description": "One sentence describing the app.",
  "runtime": "nextjs",
  "container_port": 3000,
  "health_path": "/api/health",
  "build": {
    "install": "npm ci",
    "build": "npm run build",
    "start": "npm start"
  },
  "resources": {
    "cpu": "500m",
    "memory": "1Gi"
  },
  "env": [],
  "storage": {
    "persistent": false
  }
}
```

Use `npm install` instead of `npm ci` only if there is no lockfile.

## README

Create `outputs/ucsd-package/README.md` with:

- app purpose
- features
- local run instructions
- Docker build/run instructions
- environment variables
- known limitations
- data used, including whether mock or uploaded data was used
- reviewer notes for UCSD intake

## Final Response

When finished, tell the user:

- the preview is in `outputs/web`
- the UCSD review package is in `outputs/ucsd-package`
- the package is ready for a controlled UCSD intake action, not direct deployment
