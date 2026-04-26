# Network Segmentation (Solo Developer / Managed Cloud)

## Summary

This application is operated by a single developer and is hosted using managed cloud services. There is no on-prem production environment.

## Approach

- Internet exposure is limited to the public web/API entrypoint.
- The database is hosted as a managed PostgreSQL service and is not intended to be publicly accessible.
- Administrative access to cloud/provider consoles is restricted to a single administrator account protected by MFA.

## Practical controls (typical production setup)

Depending on the selected hosting provider, segmentation/isolation is achieved via provider-native controls such as:

- Network-level access controls (security groups / firewall rules / IP allowlists).
- Private networking between application and database when available.
- Separation of production vs. non-production environments using distinct projects/accounts and separate secrets.

## Notes

Because this is a small, personal-use application and relies on managed cloud services, formal multi-subnet network segmentation may not be applicable in the same way as a larger organization’s VPC design. The intent is still followed by limiting exposure to only what must be internet-facing and keeping sensitive services (e.g., database) non-public.
