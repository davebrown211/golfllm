#!/usr/bin/env python3
"""
Production Whitelist Migration Script
Populates the whitelisted_channels table from JSON files
Run this script against production database after running the schema migration
"""

import os
import json
import psycopg2
from typing import List, Dict, Any

def load_json_whitelist(file_path: str) -> List[Dict[str, Any]]:
    """Load whitelist from JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data.get('channels', [])
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def populate_whitelist_table(database_url: str, dry_run: bool = True):
    """Populate whitelisted_channels table from JSON files"""
    
    # Load both whitelists
    regular_channels = load_json_whitelist('/Users/dbrown/golfllm/whitelist.json')
    instructional_channels = load_json_whitelist('/Users/dbrown/golfllm/instructional_whitelist.json')
    
    print(f"Found {len(regular_channels)} regular channels")
    print(f"Found {len(instructional_channels)} instructional channels")
    
    if dry_run:
        print("\n=== DRY RUN MODE - No changes will be made ===")
        print("\nRegular channels to insert:")
        for channel in regular_channels[:5]:  # Show first 5
            print(f"  - {channel.get('name', 'Unknown')} ({channel.get('id', 'No ID')}) - X: {channel.get('x_handle', 'None')}")
        
        print(f"\nInstructional channels to insert:")
        for channel in instructional_channels[:5]:  # Show first 5
            print(f"  - {channel.get('name', 'Unknown')} ({channel.get('id', 'No ID')}) - X: {channel.get('x_handle', 'None')}")
        
        print(f"\nTotal: {len(regular_channels) + len(instructional_channels)} channels would be inserted")
        return
    
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                inserted_count = 0
                
                # Insert regular channels
                for channel in regular_channels:
                    if not channel.get('id'):
                        continue
                        
                    cur.execute("""
                        INSERT INTO whitelisted_channels 
                        (channel_id, name, channel_type, x_handle, active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (channel_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            x_handle = EXCLUDED.x_handle,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        channel['id'],
                        channel.get('name', 'Unknown Channel'),
                        'regular',
                        channel.get('x_handle'),
                        channel.get('active', True)
                    ))
                    inserted_count += 1
                
                # Insert instructional channels
                for channel in instructional_channels:
                    if not channel.get('id'):
                        continue
                        
                    cur.execute("""
                        INSERT INTO whitelisted_channels 
                        (channel_id, name, channel_type, x_handle, active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (channel_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            x_handle = EXCLUDED.x_handle,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        channel['id'],
                        channel.get('name', 'Unknown Channel'),
                        'instructional',
                        channel.get('x_handle'),
                        channel.get('active', True)
                    ))
                    inserted_count += 1
                
                conn.commit()
                print(f"✅ Successfully inserted/updated {inserted_count} channels")
                
                # Verify results
                cur.execute("""
                    SELECT 
                        channel_type,
                        COUNT(*) as channel_count,
                        COUNT(x_handle) as channels_with_x_handle
                    FROM whitelisted_channels 
                    WHERE active = true
                    GROUP BY channel_type
                    ORDER BY channel_type
                """)
                
                print("\n📊 Migration Results:")
                for row in cur.fetchall():
                    channel_type, count, with_x_handle = row
                    print(f"  {channel_type}: {count} channels ({with_x_handle} with X handles)")
    
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    # Get database URL from environment or command line
    database_url = os.getenv('DATABASE_URL')
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    
    if not database_url:
        print("❌ DATABASE_URL required")
        print("Usage: python populate-whitelist-production.py [DATABASE_URL]")
        print("Or set DATABASE_URL environment variable")
        sys.exit(1)
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    print("🚀 Production Whitelist Migration")
    print(f"Database: {database_url[:50]}...")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    
    if not dry_run:
        response = input("\n⚠️  This will modify the production database. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled")
            sys.exit(0)
    
    populate_whitelist_table(database_url, dry_run=dry_run)
    
    if dry_run:
        print("\n🔍 To run the actual migration:")
        print("python populate-whitelist-production.py [DATABASE_URL]")