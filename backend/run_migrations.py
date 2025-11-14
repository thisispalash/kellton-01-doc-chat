#!/usr/bin/env python3
"""CLI tool for running database and ChromaDB migrations.

Usage:
    python run_migrations.py                    # Run all pending migrations
    python run_migrations.py --dry-run          # Preview migrations without executing
    python run_migrations.py --rollback         # Rollback the last migration
    python run_migrations.py --status           # Show migration status
    python run_migrations.py --help             # Show this help message
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from backend.db.migrations import MigrationRunner
from migrations import ALL_MIGRATIONS


def main():
    """Main entry point for migration CLI."""
    parser = argparse.ArgumentParser(
        description='Run database and ChromaDB migrations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview migrations without executing them'
    )
    
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback the last completed migration'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show status of all migrations'
    )
    
    parser.add_argument(
        '--migrations-dir',
        type=str,
        default=str(Path(__file__).parent / 'migrations'),
        help='Directory containing migration files (default: ./migrations)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    
    args = parser.parse_args()
    
    # Initialize migration runner
    verbose = not args.quiet
    runner = MigrationRunner(
        migrations_dir=args.migrations_dir,
        verbose=verbose
    )
    
    # Handle status command
    if args.status:
        status = runner.get_status(ALL_MIGRATIONS)
        
        print("\n" + "="*60)
        print("Migration Status")
        print("="*60)
        print(f"Total migrations: {status['total']}")
        print(f"Completed: {status['completed']}")
        print(f"Pending: {status['pending']}")
        print("\nDetails:")
        
        for migration in status['migrations']:
            status_icon = "✓" if migration['status'] == 'completed' else "○"
            print(f"  {status_icon} [{migration['version']:03d}] {migration['name']}")
            
            if migration['status'] == 'completed':
                print(f"      Completed at: {migration.get('completed_at', 'Unknown')}")
        
        print("="*60 + "\n")
        return 0
    
    # Handle rollback command
    if args.rollback:
        # Find the last completed migration
        completed_versions = sorted(
            [int(v) for v in runner.completed_migrations.keys()],
            reverse=True
        )
        
        if not completed_versions:
            print("No migrations to rollback.")
            return 0
        
        last_version = completed_versions[0]
        last_migration = next(
            (m for m in ALL_MIGRATIONS if m.version == last_version),
            None
        )
        
        if not last_migration:
            print(f"ERROR: Migration {last_version} not found in migration list")
            return 1
        
        print(f"\nRolling back migration {last_version}: {last_migration.name}")
        
        confirm = input("Are you sure? This will undo the migration. (yes/no): ")
        if confirm.lower() != 'yes':
            print("Rollback cancelled.")
            return 0
        
        success = runner.rollback_migration(last_migration)
        return 0 if success else 1
    
    # Handle dry-run or normal execution
    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN MODE - No changes will be made")
        print("="*60 + "\n")
    
    # Run all pending migrations
    success = runner.run_all(ALL_MIGRATIONS, dry_run=args.dry_run)
    
    if success:
        if args.dry_run:
            print("\nDry run completed successfully")
        else:
            print("\nAll migrations completed successfully!")
        return 0
    else:
        print("\nMigrations failed!")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

