"""
Database migration utilities for schema updates
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class MigrationManager:
    """Handles database schema migrations"""
    
    def __init__(self, db_path: str = "data/mt5_dashboard.db"):
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        checksum TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT version FROM schema_migrations ORDER BY version")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        pending = []
        
        # Scan migration files
        for migration_file in sorted(self.migrations_dir.glob("*.sql")):
            version = migration_file.stem
            if version not in applied:
                pending.append({
                    'version': version,
                    'name': version.replace('_', ' ').title(),
                    'file_path': migration_file
                })
        
        return pending
    
    def apply_migration(self, migration_file: Path) -> bool:
        """Apply a single migration"""
        try:
            version = migration_file.stem
            
            # Read migration SQL
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Calculate checksum
            import hashlib
            checksum = hashlib.md5(migration_sql.encode()).hexdigest()
            
            # Apply migration
            with sqlite3.connect(self.db_path) as conn:
                # Execute migration SQL
                conn.executescript(migration_sql)
                
                # Record migration
                conn.execute("""
                    INSERT INTO schema_migrations (version, name, checksum)
                    VALUES (?, ?, ?)
                """, (version, version.replace('_', ' ').title(), checksum))
                
                conn.commit()
            
            logger.info(f"Applied migration: {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration_file}: {e}")
            return False
    
    def migrate(self) -> bool:
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        success_count = 0
        for migration in pending:
            if self.apply_migration(migration['file_path']):
                success_count += 1
            else:
                logger.error(f"Migration failed, stopping at: {migration['version']}")
                break
        
        logger.info(f"Applied {success_count}/{len(pending)} migrations")
        return success_count == len(pending)
    
    def create_migration(self, name: str, sql_content: str = None) -> Path:
        """Create a new migration file"""
        # Generate version timestamp
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{version}_{name.lower().replace(' ', '_')}.sql"
        migration_file = self.migrations_dir / filename
        
        # Default SQL content
        if sql_content is None:
            sql_content = f"""-- Migration: {name}
-- Created: {datetime.now().isoformat()}

-- Add your SQL statements here
-- Example:
-- ALTER TABLE eas ADD COLUMN new_field TEXT;

-- Remember to test your migration before applying!
"""
        
        # Write migration file
        with open(migration_file, 'w') as f:
            f.write(sql_content)
        
        logger.info(f"Created migration: {migration_file}")
        return migration_file
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration (if rollback SQL exists)"""
        try:
            rollback_file = self.migrations_dir / f"{version}_rollback.sql"
            
            if not rollback_file.exists():
                logger.error(f"No rollback file found for migration: {version}")
                return False
            
            # Read rollback SQL
            with open(rollback_file, 'r') as f:
                rollback_sql = f.read()
            
            # Apply rollback
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(rollback_sql)
                
                # Remove migration record
                conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
                conn.commit()
            
            logger.info(f"Rolled back migration: {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {version}: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied_migrations': applied,
            'pending_migrations': [m['version'] for m in pending],
            'last_applied': applied[-1] if applied else None
        }

# Convenience functions
def create_migration_manager(db_path: str = None) -> MigrationManager:
    """Create migration manager instance"""
    if db_path is None:
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
    return MigrationManager(db_path)

def apply_migrations(db_path: str = None) -> bool:
    """Apply all pending migrations"""
    manager = create_migration_manager(db_path)
    return manager.migrate()

def create_migration(name: str, sql_content: str = None, db_path: str = None) -> Path:
    """Create a new migration file"""
    manager = create_migration_manager(db_path)
    return manager.create_migration(name, sql_content)