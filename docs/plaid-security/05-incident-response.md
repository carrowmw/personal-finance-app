# Incident Response (Solo Developer)

## Purpose

Provide a lightweight incident response process appropriate for a single-developer application handling financial data.

## What is an incident

Examples include:

- Suspected compromise of credentials (email, source control, hosting, Plaid)
- Unauthorized access to the API or database
- Accidental exposure of secrets (e.g., committed env vars)

## Detection

- Monitor for unusual login/activity in:
  - Email account
  - Source control
  - Hosting provider
  - Plaid dashboard
- Review hosting logs (if enabled) for anomalous traffic patterns.

## Containment

- Immediately revoke/rotate affected credentials:
  - Plaid secret / keys
  - Database password / connection string
  - JWT secret
- Disable public access paths if needed (e.g., take API offline temporarily).

## Eradication & recovery

- Patch the root cause (dependency update, configuration fix, access policy change).
- Restore service with rotated secrets and verified configuration.

## Post-incident actions

- Document timeline, impact, and corrective actions.
- Confirm sensitive values were not logged or further exposed.

## Notification

- If Plaid data or credentials may be impacted, contact Plaid support with relevant details.
- If any other user data is impacted (unlikely for personal-use), notify affected parties.
