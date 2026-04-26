# Consumer Consent (Personal-Use Application)

## Summary

The application obtains user consent before initiating Plaid Link and collecting financial account and transaction data.

## How consent is obtained

- The user must actively initiate the account-linking flow.
- Plaid Link presents the user with institution selection and consent screens.
- The user authenticates with their financial institution through Plaid Link to authorize data access.

## Scope of consent

- The application accesses only the data required for the intended functionality (e.g., transactions and related metadata).
- Plaid access tokens are stored server-side and are not shared with clients.

## User controls

- The user can stop using the application and request deletion of stored data.
- Data deletion follows the application’s retention/deletion process.
