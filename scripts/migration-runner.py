#!/usr/bin/env python3
"""
Migration Runner - Executes pending migrations in order
Used during GitHub Actions deployment to apply database changes
"""

import os
import sys
import psycopg2
from pathlib import Path
import logging
from typing import List, Tuple, Optional
from dotenv import load_dotenv
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables - check multiple locations
load_dotenv()  # Try project root first
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")  # Try backend .env for local development
load_dotenv(Path(__file__).parent.parent / "frontend" / "golf-directory" / ".env.local")  # Try frontend .env.local

def get_pending_migrations(database_url: str) -> List[Tuple[int, str, str]]:
    """Get pending migrations ordered by created_date"""
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, filename, migration_number
                    FROM migrations 
                    WHERE status = 'pending'
                    ORDER BY created_at ASC, migration_number ASC
                """)
                migrations = cur.fetchall()
                logger.info(f"Found {len(migrations)} pending migrations")
                return migrations
    except psycopg2.Error as e:
        logger.error(f"Database error getting pending migrations: {e}")
        raise

def read_migration_file(migrations_path: str, filename: str) -> str:
    """Read migration SQL file content"""
    file_path = Path(migrations_path) / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Migration file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_migration(database_url: str, migration_id: int, filename: str, sql_content: str) -> bool:
    """Execute a single migration and update its status"""
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                logger.info(f"Executing migration: {filename}")
                
                # Execute the migration SQL
                cur.execute(sql_content)
                
                # Update migration status to completed
                cur.execute("""
                    UPDATE migrations 
                    SET status = 'completed', applied_at = %s
                    WHERE id = %s
                """, (datetime.now(), migration_id))
                
                conn.commit()
                logger.info(f"✓ Migration completed successfully: {filename}")
                return True
                
    except psycopg2.Error as e:
        # Update migration status to failed with error message
        try:
            with psycopg2.connect(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE migrations 
                        SET status = 'failed', error_message = %s, applied_at = %s
                        WHERE id = %s
                    """, (str(e), datetime.now(), migration_id))
                    conn.commit()
        except Exception as update_error:
            logger.error(f"Failed to update migration status: {update_error}")
        
        logger.error(f"✗ Migration failed: {filename} - {e}")
        return False

def main():
    """Main migration runner function"""
    try:
        # Get paths
        script_dir = Path(__file__).parent
        migrations_path = script_dir.parent / "frontend" / "golf-directory" / "src" / "lib" / "migrations"
        
        # Get database URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
        
        logger.info("Starting migration runner...")
        logger.info(f"Migrations directory: {migrations_path}")
        
        # Get pending migrations
        pending_migrations = get_pending_migrations(database_url)
        
        if not pending_migrations:
            logger.info("No pending migrations to execute")
            return
        
        logger.info(f"Executing {len(pending_migrations)} pending migrations:")
        for migration_id, filename, migration_number in pending_migrations:
            logger.info(f"  - {filename} (#{migration_number})")
        
        # Execute each migration
        failed_migrations = []
        successful_count = 0
        
        for migration_id, filename, migration_number in pending_migrations:
            try:
                # Read migration file
                sql_content = read_migration_file(str(migrations_path), filename)
                
                # Execute migration
                if execute_migration(database_url, migration_id, filename, sql_content):
                    successful_count += 1
                else:
                    failed_migrations.append(filename)
                    # Stop on first failure to maintain order
                    break
                    
            except FileNotFoundError as e:
                logger.error(f"Migration file not found: {e}")
                failed_migrations.append(filename)
                break
            except Exception as e:
                logger.error(f"Unexpected error processing {filename}: {e}")
                failed_migrations.append(filename)
                break
        
        # Report results
        if failed_migrations:
            logger.error(f"Migration runner completed with failures:")
            logger.error(f"  - Successful: {successful_count}")
            logger.error(f"  - Failed: {len(failed_migrations)}")
            for failed in failed_migrations:
                logger.error(f"    • {failed}")
            sys.exit(1)
        else:
            logger.info(f"Migration runner completed successfully. Applied {successful_count} migrations.")
        
    except Exception as e:
        logger.error(f"Migration runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()