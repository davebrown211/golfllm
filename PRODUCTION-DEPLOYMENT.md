# Production Deployment Checklist

## ⚠️ CRITICAL: Run database migrations BEFORE deploying code

### Step 1: Database Schema Migration
```bash
# Connect to production database and run:
psql $PRODUCTION_DATABASE_URL -f production-migration.sql
```

### Step 2: Data Migration
```bash
# First do a dry run to verify data:
python populate-whitelist-production.py $PRODUCTION_DATABASE_URL --dry-run

# If dry run looks good, run the actual migration:
python populate-whitelist-production.py $PRODUCTION_DATABASE_URL
```

### Step 3: Verify Migration
```sql
-- Connect to production database and verify:
SELECT 
    channel_type,
    COUNT(*) as channel_count,
    COUNT(x_handle) as channels_with_x_handle
FROM whitelisted_channels 
WHERE active = true
GROUP BY channel_type
ORDER BY channel_type;

-- Should show something like:
--  instructional | 15 | 8
--  regular       | 45 | 25
```

### Step 4: Deploy Code Changes
Only after the database migrations are complete:

1. **Backend**: Deploy the updated Python scripts
   - `ai_video_of_day_runner.py` - Now uses shared query without cursor
   - `ai_summary_runner.py` - Now only processes VOD
   - `golf_scheduler.py` - Uses database JOINs
   - `x_post_templates.py` - Uses database for X handles

2. **Frontend**: Deploy the updated Next.js app
   - All queries now use database JOINs instead of parameter arrays
   - No more whitelist JSON file dependencies

### Step 5: Post-Deployment Verification
```bash
# Test that the VOD runner works:
python ai_video_of_day_runner.py

# Test that AI summary runner only processes VOD:
python ai_summary_runner.py --once 1

# Verify frontend shows correct videos (should match production)
curl https://your-frontend-url.com/api/video-of-the-day
```

## What Changed
- ✅ Moved from JSON file whitelists to database table
- ✅ Added channel categorization (regular vs instructional)  
- ✅ Added X handle storage for social media integration
- ✅ Fixed parameter passing issues between psycopg2 and node-postgres
- ✅ AI summary runner now only processes current Video of the Day
- ✅ All systems use unified database-driven whitelist

## Rollback Plan
If issues occur, you can temporarily revert to the previous commit, but the database changes are safe to keep (they're additive only).

## Files Created/Modified
### New Files:
- `production-migration.sql` - Database schema changes
- `populate-whitelist-production.py` - Data migration script
- `009_add_x_handle_to_whitelisted_channels.sql` - Additional migration

### Modified Files:
- `backend/ai_video_of_day_runner.py` - Removed cursor, uses shared query
- `backend/ai_summary_runner.py` - Only processes VOD, uses database
- `backend/golf_scheduler.py` - Uses database JOINs  
- `backend/x_post_templates.py` - Database X handle lookup
- `frontend/src/app/page.tsx` - Database JOINs instead of parameters

### Removed Files:
- `backend/golf_whitelist.py` - No longer needed