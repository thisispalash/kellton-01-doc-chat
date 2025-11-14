"""Migration framework for database and ChromaDB schema changes."""

import os
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class Migration(ABC):
    """Base class for migrations.
    
    Each migration should:
    1. Inherit from this class
    2. Set a unique version number
    3. Set a descriptive name
    4. Implement up(), down(), and dry_run() methods
    """
    
    version: int = 0
    name: str = "Base Migration"
    
    def __init__(self, verbose: bool = True):
        """Initialize migration.
        
        Args:
            verbose: Whether to print detailed progress logs
        """
        self.verbose = verbose
        self.log_messages: List[str] = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp.
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] [{level}] {message}"
        self.log_messages.append(formatted_msg)
        
        if self.verbose:
            print(formatted_msg)
    
    @abstractmethod
    def up(self) -> bool:
        """Execute the migration (forward).
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def down(self) -> bool:
        """Rollback the migration (backward).
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def dry_run(self) -> dict:
        """Preview what the migration would do without executing it.
        
        Returns:
            Dictionary with preview information
        """
        pass
    
    def get_logs(self) -> List[str]:
        """Get all log messages from this migration.
        
        Returns:
            List of log messages
        """
        return self.log_messages


class MigrationRunner:
    """Runner for managing and executing migrations."""
    
    def __init__(self, migrations_dir: str, state_file: Optional[str] = None, verbose: bool = True):
        """Initialize migration runner.
        
        Args:
            migrations_dir: Directory containing migration files
            state_file: Path to file tracking completed migrations (default: migrations/.migration_state.json)
            verbose: Whether to print detailed progress logs
        """
        self.migrations_dir = Path(migrations_dir)
        self.state_file = Path(state_file) if state_file else self.migrations_dir / '.migration_state.json'
        self.verbose = verbose
        self.completed_migrations = self._load_state()
    
    def _load_state(self) -> dict:
        """Load migration state from file.
        
        Returns:
            Dictionary mapping version numbers to execution info
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load migration state: {e}")
                return {}
        return {}
    
    def _save_state(self):
        """Save migration state to file."""
        try:
            # Create directory if it doesn't exist
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w') as f:
                json.dump(self.completed_migrations, f, indent=2)
        except Exception as e:
            print(f"Error saving migration state: {e}")
    
    def mark_completed(self, migration: Migration):
        """Mark a migration as completed.
        
        Args:
            migration: Migration instance
        """
        self.completed_migrations[str(migration.version)] = {
            'name': migration.name,
            'version': migration.version,
            'completed_at': datetime.now().isoformat(),
            'logs': migration.get_logs()
        }
        self._save_state()
    
    def mark_rolled_back(self, migration: Migration):
        """Mark a migration as rolled back (remove from completed).
        
        Args:
            migration: Migration instance
        """
        version_key = str(migration.version)
        if version_key in self.completed_migrations:
            del self.completed_migrations[version_key]
            self._save_state()
    
    def is_completed(self, migration: Migration) -> bool:
        """Check if a migration has been completed.
        
        Args:
            migration: Migration instance
            
        Returns:
            True if migration is completed
        """
        return str(migration.version) in self.completed_migrations
    
    def run_migration(self, migration: Migration, dry_run: bool = False) -> bool:
        """Run a single migration.
        
        Args:
            migration: Migration instance to run
            dry_run: If True, only preview without executing
            
        Returns:
            True if successful, False otherwise
        """
        if dry_run:
            print(f"\n{'='*60}")
            print(f"DRY RUN: Migration {migration.version} - {migration.name}")
            print(f"{'='*60}")
            
            preview = migration.dry_run()
            print("\nPreview:")
            for key, value in preview.items():
                print(f"  {key}: {value}")
            
            return True
        
        if self.is_completed(migration):
            print(f"Migration {migration.version} ({migration.name}) already completed. Skipping.")
            return True
        
        print(f"\n{'='*60}")
        print(f"Running Migration {migration.version}: {migration.name}")
        print(f"{'='*60}\n")
        
        try:
            success = migration.up()
            
            if success:
                self.mark_completed(migration)
                print(f"\n✓ Migration {migration.version} completed successfully")
                return True
            else:
                print(f"\n✗ Migration {migration.version} failed")
                return False
        
        except Exception as e:
            print(f"\n✗ Migration {migration.version} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a single migration.
        
        Args:
            migration: Migration instance to rollback
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_completed(migration):
            print(f"Migration {migration.version} ({migration.name}) not completed. Nothing to rollback.")
            return True
        
        print(f"\n{'='*60}")
        print(f"Rolling back Migration {migration.version}: {migration.name}")
        print(f"{'='*60}\n")
        
        try:
            success = migration.down()
            
            if success:
                self.mark_rolled_back(migration)
                print(f"\n✓ Migration {migration.version} rolled back successfully")
                return True
            else:
                print(f"\n✗ Migration {migration.version} rollback failed")
                return False
        
        except Exception as e:
            print(f"\n✗ Migration {migration.version} rollback failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all(self, migrations: List[Migration], dry_run: bool = False) -> bool:
        """Run all pending migrations.
        
        Args:
            migrations: List of migration instances
            dry_run: If True, only preview without executing
            
        Returns:
            True if all successful, False if any failed
        """
        # Sort by version
        sorted_migrations = sorted(migrations, key=lambda m: m.version)
        
        pending = [m for m in sorted_migrations if not self.is_completed(m) or dry_run]
        
        if not pending:
            print("No pending migrations.")
            return True
        
        print(f"\nFound {len(pending)} pending migration(s)")
        
        for migration in pending:
            success = self.run_migration(migration, dry_run=dry_run)
            if not success and not dry_run:
                print(f"\nStopping due to failed migration {migration.version}")
                return False
        
        return True
    
    def get_status(self, migrations: List[Migration]) -> dict:
        """Get status of all migrations.
        
        Args:
            migrations: List of migration instances
            
        Returns:
            Dictionary with status information
        """
        sorted_migrations = sorted(migrations, key=lambda m: m.version)
        
        status = {
            'total': len(sorted_migrations),
            'completed': 0,
            'pending': 0,
            'migrations': []
        }
        
        for migration in sorted_migrations:
            completed = self.is_completed(migration)
            
            migration_info = {
                'version': migration.version,
                'name': migration.name,
                'status': 'completed' if completed else 'pending'
            }
            
            if completed:
                status['completed'] += 1
                migration_info['completed_at'] = self.completed_migrations[str(migration.version)].get('completed_at')
            else:
                status['pending'] += 1
            
            status['migrations'].append(migration_info)
        
        return status

