# TypeScript Rewrite (In Progress)

This workspace now includes a TypeScript monorepo scaffold alongside the existing Flask app.

## Apps

- `apps/api`: NestJS API (finance-only MVP foundations)
- `apps/web`: React + Vite frontend shell
- `packages/contracts`: Shared TypeScript domain contracts

## Quick start

1. Install dependencies
   - `npm install`
2. Run both apps
   - `npm run dev`

## Loading API Secrets From macOS Keychain

1. Add secrets one time (example):
   - `security add-generic-password -a "$USER" -s "pf/DATABASE_URL" -w "postgresql://..." -U`
2. Load them into your current shell before starting the API:
   - `source scripts/load-api-secrets-from-keychain.sh`
3. Start API:
   - `npm run api:dev`

Notes:

- The loader expects service names in the format `pf/ENV_VAR_NAME`.
- Override prefix/account if needed: `KEYCHAIN_PREFIX=myapp KEYCHAIN_ACCOUNT=myuser source scripts/load-api-secrets-from-keychain.sh`.
- Keep `apps/api/.env` sanitized (placeholders only). Exported shell values override `.env` values at runtime.

## Notes

- Current phase focuses on architecture + contracts + minimal API/UI flow.
- Existing Python app remains untouched for continuity during migration.
