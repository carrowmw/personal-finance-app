# Vendor Management (Solo Developer)

## Summary

This application uses a small number of third-party vendors to provide hosting and financial data access. Because the project is operated by a single developer, vendor management is lightweight but deliberate.

## Vendor intake

When selecting a vendor, the following are evaluated:

- Vendor reputation and security posture (public security documentation, compliance statements if available)
- Data access scope and whether least-privilege access can be applied
- Ability to revoke/rotate credentials and access tokens
- Availability of MFA for vendor dashboards
- Contractual/privacy considerations appropriate for the intended use

## Vendors used (examples)

- Plaid (financial data connectivity)
- Hosting provider (API + web)
- Managed database provider (PostgreSQL)

## Ongoing monitoring

- Review vendor security notices and status pages when applicable.
- Rotate secrets promptly if exposure is suspected.
- Periodically review configured integrations, API keys, and dashboard access.

## Enforcement

- Vendor access is limited to what is required for functionality.
- Secrets are stored in environment variables / provider secret managers and are not committed to source control.
- MFA is enabled on vendor dashboards where supported.
