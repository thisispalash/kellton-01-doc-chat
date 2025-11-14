"""Migrations directory for database and ChromaDB schema changes."""

from .001_consolidate_collections import consolidate_collections_migration

# List of all migrations in order
ALL_MIGRATIONS = [
    consolidate_collections_migration,
]

__all__ = ['ALL_MIGRATIONS', 'consolidate_collections_migration']

