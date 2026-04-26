# HR & Background Checks (Solo Developer)

## Summary

This application is developed and operated by a single individual. There are no employees or contractors.

## Background checks

- Formal background checks are not performed because there are no hires/contractors.
- If contractors are engaged in the future, access would be granted only as needed and would be time-bound, with immediate revocation when no longer required.

## Access controls as compensating measures

- Administrative access to production systems is restricted to a single administrator account protected by MFA.
- Secrets are stored outside of source control and are rotated if compromise is suspected.
- The application enforces least-privilege access to data via authenticated API routes scoped to the user.
