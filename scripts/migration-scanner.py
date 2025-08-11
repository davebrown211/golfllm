#!/usr/bin/env python3
"""
Migration Scanner - Scans for new migration files and adds them to the migrations table
Used during GitHub Actions deployment to detect new migrations
"""

import os
import sys
import re
import psycopg2
from pathlib import Path
import logging
from typing import List, Tuple
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables - check multiple locations
load_dotenv()  # Try project root first
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")  # Try backend .env for local development
load_dotenv(Path(__file__).parent.parent / "frontend" / "golf-directory" / ".env.local")  # Try frontend .env.local

def extract_migration_number(filename: str) -> int:
    """Extract migration number from filename (e.g., '007_name.sql' -> 7)"""
    match = re.match(r'^(\d+)_.*\.sql$', filename)
    if not match:
        raise ValueError(f"Invalid migration filename format: {filename}")
    return int(match.group(1))

def scan_migrations_directory(migrations_path: str) -> List[Tuple[str, int]]:
    """Scan migrations directory and return list of (filename, migration_number)"""
    migrations_dir = Path(migrations_path)
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_path}")
    
    migrations = []
    for file_path in migrations_dir.glob("*.sql"):
        filename = file_path.name
        try:
            migration_number = extract_migration_number(filename)
            migrations.append((filename, migration_number))
        except ValueError as e:
            logger.warning(f"Skipping invalid migration file: {e}")
            continue
    
    # Sort by migration number
    migrations.sort(key=lambda x: x[1])
    logger.info(f"Found {len(migrations)} migration files")
    return migrations

def get_existing_migrations(database_url: str) -> set:
    """Get set of existing migration filenames from database"""
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT filename FROM migrations")
                existing = {row[0] for row in cur.fetchall()}
                logger.info(f"Found {len(existing)} existing migrations in database")
                return existing
    except psycopg2.Error as e:
        logger.error(f"Database error getting existing migrations: {e}")
        raise

def insert_new_migrations(database_url: str, new_migrations: List[Tuple[str, int]]) -> int:
    """Insert new migrations into database with pending status"""
    if not new_migrations:
        logger.info("No new migrations to insert")
        return 0
    
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                inserted_count = 0
                for filename, migration_number in new_migrations:
                    try:
                        cur.execute("""
                            INSERT INTO migrations (filename, migration_number, status)
                            VALUES (%s, %s, 'pending')
                        """, (filename, migration_number))
                        logger.info(f"Added pending migration: {filename} (#{migration_number})")
                        inserted_count += 1
                    except psycopg2.IntegrityError:
                        # Migration already exists (duplicate filename)
                        logger.warning(f"Migration already exists: {filename}")
                        continue
                
                conn.commit()
                logger.info(f"Successfully inserted {inserted_count} new migrations")
                return inserted_count
                
    except psycopg2.Error as e:
        logger.error(f"Database error inserting migrations: {e}")
        raise

def main():
    """Main scanner function"""
    try:
        # Get paths
        script_dir = Path(__file__).parent
        migrations_path = script_dir.parent / "frontend" / "golf-directory" / "src" / "lib" / "migrations"
        
        # Get database URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
        
        logger.info("Starting migration scanner...")
        logger.info(f"Scanning directory: {migrations_path}")
        
        # Scan for migration files
        all_migrations = scan_migrations_directory(str(migrations_path))
        
        # Get existing migrations from database
        existing_migrations = get_existing_migrations(database_url)
        
        # Filter for new migrations
        new_migrations = [
            (filename, number) for filename, number in all_migrations
            if filename not in existing_migrations
        ]
        
        if new_migrations:
            logger.info(f"Found {len(new_migrations)} new migrations:")
            for filename, number in new_migrations:
                logger.info(f"  - {filename} (#{number})")
        else:
            logger.info("No new migrations found")
        
        # Insert new migrations
        inserted_count = insert_new_migrations(database_url, new_migrations)
        
        logger.info(f"Migration scanner completed successfully. Inserted {inserted_count} new migrations.")
        
    except Exception as e:
        logger.error(f"Migration scanner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()