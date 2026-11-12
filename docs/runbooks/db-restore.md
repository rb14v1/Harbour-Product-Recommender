# Runbook: Restoring the prod_rec database

## Backup configuration

The production database is the Azure Database for PostgreSQL Flexible Server
`psql-prod-rec`, defined in `infra/terraform/postgres.tf`.

| Setting | Value |
|---|---|
| Automated backups | Enabled (managed by Azure, daily full + continuous WAL) |
| Retention | 30 days (`backup_retention_days = 30`) |
| Off-region copy | Geo-redundant backups to the Azure paired region (`geo_redundant_backup_enabled = true`) |
| Point-in-time recovery | Any point within the 30-day retention window |

The local Docker Compose Postgres (`docker-compose.yml`) is for development
only and is not backed up.

## Point-in-time restore (same region)

A restore always creates a **new** server; the original is not overwritten.

1. Pick the restore point (UTC), e.g. just before the incident.
2. Restore to a new server:

   ```bash
   az postgres flexible-server restore \
     --resource-group <resource-group> \
     --name psql-prod-rec-restore-<yyyymmddhhmm> \
     --source-server psql-prod-rec \
     --restore-time "<YYYY-MM-DDTHH:MM:SSZ>"
   ```

3. Re-enable the pgvector extension on the new server if needed:

   ```bash
   az postgres flexible-server parameter set \
     --resource-group <resource-group> \
     --server-name psql-prod-rec-restore-<yyyymmddhhmm> \
     --name azure.extensions --value VECTOR
   ```

4. Verify the data (see "Verification" below).
5. Point the backend at the restored server by updating `POSTGRES_HOST`
   (and credentials, if they changed) in the deployment environment, then
   restart the backend.
6. Once confirmed, retire or rename the old server, and bring the restored
   server under Terraform management (`terraform import`) so it keeps the
   same backup settings.

## Geo-restore (primary region outage)

```bash
az postgres flexible-server geo-restore \
  --resource-group <resource-group> \
  --name psql-prod-rec-geo-<yyyymmddhhmm> \
  --source-server <psql-prod-rec resource ID> \
  --location <paired-region>
```

Then follow steps 3–6 above.

## Verification

- `python manage.py showmigrations` against the restored server shows all
  migrations applied.
- Row counts for `products_product` and the users table match expectations
  for the restore point.
- `GET /api/products/{id}/similar/` returns results (confirms pgvector
  data and extension are intact).

## Restore test log

A test restore must be completed and recorded here before go-live, and
repeated at least annually.

| Date (UTC) | Performed by | Type (PITR / geo) | Restore point | Time to restore | Verification result |
|---|---|---|---|---|---|
| _pending — required before go-live_ | | | | | |
