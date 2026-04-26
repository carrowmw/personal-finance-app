# TypeScript Rewrite Plan (Finance-Only MVP)

## Implemented in this phase

- Monorepo workspace setup (`apps/api`, `apps/web`, `packages/contracts`)
- NestJS API scaffold with modules:
  - `auth`
  - `finance`
  - `plaid`
  - `sync`
- React app scaffold with dashboard summary fetch from API
- Shared contract package for API/web typing
- Build and typecheck scripts verified
- Prisma schema + generated client
- JWT auth (`register`, `login`, `me`)
- Plaid Node SDK integration for link token, public token exchange, and cursor sync
- DB-backed finance dashboard/transactions endpoints
- Legacy Flask code archived under `archive/legacy-python`

## Current API routes

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me` (auth required)
- `GET /api/finance/dashboard` (auth required)
- `GET /api/finance/transactions` (auth required)
- `POST /api/plaid/create-link-token`
- `POST /api/plaid/exchange-token`
- `POST /api/sync/manual` (auth required)

## Next implementation tasks

1. Run first database migration against local PostgreSQL
   - `cd apps/api`
   - `npx prisma migrate dev --name init`
2. Build frontend screens
   - Login
   - Plaid link
   - Transactions table
   - Dashboard cards/charts
3. Add tests
   - Unit tests for sync logic
   - API integration tests for finance endpoints

## Local development

From repository root:

- Install: `npm install`
- Typecheck: `npm run typecheck`
- Build: `npm run build`
- Run API + web: `npm run dev`
- Shortcut start: `npm start`
- API only with automatic port cleanup: `npm run api:dev`

## Environment checklist

- API env file: `apps/api/.env` (template in `apps/api/.env.example`)
- Required keys:
  - `DATABASE_URL` (pooled URL, usually port `6543`)
  - `JWT_SECRET` (32+ chars)
- Optional but recommended:
  - `DIRECT_URL` (direct Postgres URL, usually port `5432`, used by Prisma for migrations)
- If DB password contains special characters (`@`, `&`, `%`, `/`, `:`), URL-encode it in both URLs.

## Prisma + Supabase workflow

- Apply schema quickly (no migration files):
  - `cd apps/api`
  - `npx prisma db push`
- Create migration history (recommended once schema stabilizes):
  - `cd apps/api`
  - `npx prisma migrate dev --name baseline`
  - If prompted for reset and you do not want it, cancel and keep using `db push` for now.

## Notes

- Legacy Flask app is archived in `archive/legacy-python`.
- You must set `apps/api/.env` values (especially `DATABASE_URL`, `JWT_SECRET`, and Plaid credentials) before using protected/Plaid routes.
- API now validates env at startup and fails fast with explicit config errors.
- Web app now includes login/register, Plaid Link token creation + open flow, manual sync trigger, and a recent transactions table.
