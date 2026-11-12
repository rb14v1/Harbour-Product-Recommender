# Production database for prod_rec: Azure Database for PostgreSQL Flexible Server.
# Backups: automated daily backups with 30-day retention, geo-redundant
# (copied to the Azure paired region, separate from the primary), and
# point-in-time restore (PITR) to any second within the retention window.
# Restore procedure: docs/runbooks/db-restore.md

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "resource_group_name" {
  description = "Resource group that hosts the production database."
  type        = string
}

variable "location" {
  description = "Primary Azure region for the database (must have a paired region for geo-redundant backups)."
  type        = string
}

variable "postgres_admin_login" {
  description = "Administrator login for the PostgreSQL server."
  type        = string
}

variable "postgres_admin_password" {
  description = "Administrator password, sourced from Key Vault kv-prod-rec. Never commit."
  type        = string
  sensitive   = true
}

resource "azurerm_postgresql_flexible_server" "prod_rec" {
  name                = "psql-prod-rec"
  resource_group_name = var.resource_group_name
  location            = var.location

  version    = "16"
  sku_name   = "GP_Standard_D2s_v3"
  storage_mb = 32768

  administrator_login    = var.postgres_admin_login
  administrator_password = var.postgres_admin_password

  # Automated backups + PITR, retained for 30 days.
  backup_retention_days = 30
  # Store backups in the paired region, separate from the primary.
  geo_redundant_backup_enabled = true

  lifecycle {
    prevent_destroy = true
  }
}

# pgvector is required by the app (apps/products/migrations/0001_initial.py).
resource "azurerm_postgresql_flexible_server_configuration" "extensions" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.prod_rec.id
  value     = "VECTOR"
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.prod_rec.fqdn
}
