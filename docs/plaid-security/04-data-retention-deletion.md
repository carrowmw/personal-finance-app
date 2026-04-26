# Data Retention & Deletion

## Purpose

Define what data is retained, why it is retained, and how it can be deleted.

## Data retained

- Authentication data:
  - Email address
  - Password hash (bcrypt)
- Plaid linkage:
  - Plaid item identifier
  - Plaid access token (server-side secret; not shared with clients)
- Financial data used for the application:
  - Account identifiers/metadata
  - Transaction records (amount/date/merchant/category fields)

## Retention period

- Data is retained while the account is active to support the dashboard and transaction history.

## Deletion

- When the user requests deletion (or the account is no longer used), the following are deleted from the database:
  - Plaid item record
  - Accounts and transactions
  - User record
- Deletion is performed by direct database deletion (cascading deletes are configured in the schema).

## Logs

- The application avoids logging sensitive credentials (passwords, Plaid tokens).
- Operational logs (if enabled by hosting provider) are retained per provider defaults and are reviewed for sensitive content.

## Backups

- Database backups (if enabled) are managed by the database provider.
- If backups exist, deleted data may persist until backup rotation completes.
