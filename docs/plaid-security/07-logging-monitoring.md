# Logging & Monitoring

## Purpose

Describe how production events are logged and how security-relevant issues are detected and triaged for a single-developer application.

## Logging approach

- Application logs:
  - API runtime logs are captured by the hosting provider (stdout/stderr) and used for debugging and incident triage.
  - Sensitive values (passwords, Plaid tokens, database credentials) are not intentionally logged.
- Platform logs:
  - Hosting provider logs and access logs (where enabled) provide request/availability signals.
  - Database provider logs (where enabled) provide connection and performance visibility.

## Audit trail (lightweight)

- Source control provides an audit trail for code changes.
- Hosting provider dashboards provide an audit trail for deployments and configuration changes (where supported).

## Monitoring & alerting

- Service health is monitored using provider-level monitoring and/or simple health checks.
- Alerts are enabled where available for:
  - service downtime or repeated errors
  - suspicious account activity on critical services (email, source control, hosting provider, Plaid dashboard)

## Incident triage

- Incidents are handled using the workflow in the incident response document:
  - rotate/revoke secrets
  - investigate logs
  - patch root cause

## Retention

- Log retention is configured via provider defaults and is reviewed periodically to ensure sensitive data is not present.
