# Production Deployment Standard

This document is the canonical deployment policy for repositories owned by Nischhalsubba unless a project has a documented technical exception.

## Objectives

1. Preserve free-tier hosting usage.
2. Prevent accidental preview, branch, duplicate, and no-op deployments.
3. Keep production releases intentional, reproducible, auditable, and reversible.
4. Never trade product freshness or required automation for artificial usage savings.

## Default Architecture

- `main` is the only production-eligible branch.
- Feature, development, pull-request, and preview branches must not deploy to production hosting.
- Normal commits to `main` must not automatically deploy.
- Production is released through a manually dispatched GitHub Actions workflow named `Release Production`.
- The workflow validates the exact current `main` SHA before release.
- The workflow runs the project's production quality/build gate before authorizing deployment.
- The workflow re-checks `main` after validation to prevent releasing a stale SHA.
- Production releases are serialized with a single `production-release` concurrency group.
- The current credential-free provider integration uses an empty release commit containing `[deploy]` after validation. Netlify/Vercel repository configuration ignores all other commits.
- Documentation-only and CI-policy-only changes are not production releases.

## Release Marker

`[deploy]` is reserved for an already-validated production release. Do not use it in ordinary commits, pull requests, documentation examples that are committed as messages, or automated maintenance commits unless that automation is explicitly authorized to publish production state.

## Automated Data Exception

Automated jobs may publish without manual approval only when all of the following are true:

1. The automation is a required product-data refresh.
2. It performs change detection before committing.
3. It validates the generated output before committing.
4. It creates no commit when source data is unchanged.
5. Its verified commit contains `[deploy]` so the same production gate is reused.

Biratnagar Menu's verified restaurant source sync is the current approved example.

## Resource-Conservation Rules

- Never manually trigger a second Netlify/Vercel deployment after a Git-triggered production release.
- Never redeploy an identical commit merely to verify it.
- Batch related changes into one production release whenever practical.
- Prefer local validation before remote CI.
- Skip browser installation, integration tests, artifact uploads, or other expensive CI steps when change detection proves they are unnecessary.
- Preserve provider build cache unless debugging requires a forced rebuild.
- Roll back to a known-good existing deployment instead of rebuilding old source.
- Prefer static/CDN delivery over functions for static content.
- Avoid unnecessary polling, cron frequency, SSR, image transformations, and serverless invocations.

## Hosting Selection for New Projects

Choose the simplest platform that satisfies the application runtime:

- Static HTML/CSS/JS or static Vite/React output: prefer Cloudflare Pages when migration cost is low.
- Vercel-specific/Next.js runtime requirements: use Vercel.
- Netlify Forms, Netlify Functions, or other Netlify-specific requirements: use Netlify.
- Do not migrate an existing working production site merely for theoretical savings without measuring migration risk and actual usage.

## Provider Configuration

### Netlify

Repository `netlify.toml` should ignore every build except an authorized `main` release commit. Preserve all existing build, function, header, redirect, and cache configuration.

### Vercel

`vercel.json` should disable automatic deployments for all branches except `main`, then use `ignoreCommand` to ignore ordinary `main` commits unless they are authorized production releases.

## Future Prebuilt Upgrade

The preferred end-state, once provider credentials are intentionally provisioned as GitHub Actions secrets, is:

1. Disable provider Git auto-deployments entirely.
2. Build production artifacts inside the protected GitHub release workflow.
3. Deploy prebuilt output directly to the provider.
4. Perform post-deploy health checks.
5. Record the deployed SHA/artifact digest.
6. Roll back using an existing provider deployment if health checks fail.

Required credentials must be stored only as encrypted GitHub Actions secrets or equivalent secure credentials. They must never be committed to source control.

## Safety Rules

- Never commit provider tokens, API keys, environment secrets, or credentials.
- Never disable a required production flow, scheduled data refresh, form handler, function, or runtime feature merely to save usage.
- Do not alter a project's production branch until repository and hosting settings are migrated together.
- Legacy projects whose Git source cannot be confidently mapped must remain untouched until mapped.

## Standard Release Procedure

1. Work on a feature/fix branch where appropriate.
2. Validate locally.
3. Merge or push the finished batch to `main`.
4. Confirm normal host deployment was skipped.
5. In GitHub Actions, run `Release Production` from `main` and explicitly confirm the release.
6. The workflow validates, confirms the current SHA, and emits the authorized production release.
7. Inspect the single resulting production deployment.
8. Do not manually redeploy unless recovering from a failed trigger or an explicit incident response.

This policy is intentionally conservative: one validated release should correspond to one production deployment.
