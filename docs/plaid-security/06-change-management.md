# Change Management (Build, Test, Review, Release)

## Purpose

Describe the lightweight process used to build, test, review, and deploy changes to production for a single-developer application.

## Scope

- Source code changes (API + web)
- Database schema changes (Prisma migrations)
- Configuration changes (environment variables / secrets)

## Source control

- All changes are tracked in source control.
- Secrets are not committed to the repository.

## Build & release

- Production builds are created from source-controlled code.
- Deployment is performed via a managed hosting provider (PaaS) or equivalent controlled process.

## Testing before deployment

- At minimum, changes are validated in a non-production environment (local development).
- Type checking is run for the TypeScript codebase.
- Dependency vulnerabilities are checked periodically (e.g., `npm audit`).

## Review & approval

- As a single-developer project, changes are self-reviewed prior to deployment.
- Security-impacting changes (auth, secrets, Plaid integration, data access) receive additional manual review.

## Rollback

- If a deployment causes issues, the service is rolled back using provider tooling (redeploy last known good build) and/or hotfix changes.

## Change log

- Significant changes are documented in commit history and/or release notes.
