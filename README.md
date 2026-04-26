# About

## TypeScript rewrite (active)

This repository now includes an in-progress TypeScript rewrite focused on a finance-only MVP.

- API: `apps/api` (NestJS)
- Web: `apps/web` (React + Vite)
- Shared contracts: `packages/contracts`

Quick start:

1. `npm install`
2. `npm run typecheck`
3. `npm run build`
4. `npm run dev`

Migration notes: `docs/typescript-migration.md`

Legacy Python implementation archive: `archive/legacy-python`

Balance fields: ['account_id', 'balances', 'mask', 'name', 'official_name', 'type', 'subtype', 'persistent_account_id']

Transaction field: ['account_id', 'account_owner', 'amount', 'authorised_date', 'authorised_datetime', 'category', 'category_id', 'check_number', 'counterparties', 'date', 'datetime', 'iso_currency_code', 'location', 'logo_url', 'merchant_entity_id', 'merchant_name', 'name', 'payment_channel', 'payment_meta', 'pending', 'pending_transaction_id', 'personal_finance_category', 'personal_finance_category_icon_url', 'transaction_code', 'transaction_id', 'transaction_type', 'unofficial_currency_code', 'website']
