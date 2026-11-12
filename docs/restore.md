# Database restore procedure

The production database (`psql-prod-rec`, Azure Database for PostgreSQL
Flexible Server, defined in `infra/terraform/postgres.tf`) has:

- Automated backups with 30-day retention (`backup_retention_days = 30`)
- Geo-redundant backup storage in the Azure paired region
  (`geo_redundant_backup_enabled = true`)
- Point-in-time recovery to any second within the retention window

The full step-by-step restore procedure (point-in-time restore, geo-restore,
verification) and the restore test log are in
[`docs/runbooks/db-restore.md`](runbooks/db-restore.md).

A test restore must be performed and recorded in that runbook's
"Restore test log" before go-live.
