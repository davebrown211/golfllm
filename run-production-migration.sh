#!/bin/bash
set -e

echo "🚀 Golf Directory Production Migration"
echo "======================================"

# Check if DATABASE_URL is provided
if [ -z "$1" ]; then
    echo "❌ Usage: $0 <DATABASE_URL>"
    echo "   Example: $0 'postgresql://user:pass@host:port/db'"
    exit 1
fi

DATABASE_URL="$1"
echo "🔗 Database: ${DATABASE_URL:0:30}..."

echo ""
echo "Step 1/3: Running schema migration..."
psql "$DATABASE_URL" -f production-migration.sql

echo ""
echo "Step 2/3: Running data migration (dry run first)..."
python populate-whitelist-production.py "$DATABASE_URL" --dry-run

echo ""
read -p "🤔 Dry run looks good? Continue with actual migration? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""
echo "Step 3/3: Running actual data migration..."
python populate-whitelist-production.py "$DATABASE_URL"

echo ""
echo "✅ Production migration completed!"
echo ""
echo "🔍 Verification query results:"
psql "$DATABASE_URL" -c "
SELECT 
    channel_type,
    COUNT(*) as channel_count,
    COUNT(x_handle) as channels_with_x_handle
FROM whitelisted_channels 
WHERE active = true
GROUP BY channel_type
ORDER BY channel_type;"

echo ""
echo "🚀 Ready to deploy code changes!"