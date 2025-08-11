-- Migration: Test the automated migration system
-- This is a test migration to verify the scanner and runner work correctly

-- Add a simple test comment to migrations table
COMMENT ON TABLE migrations IS 'Migration tracking table - automated system test completed';

-- Create a temporary test table and immediately drop it to test transaction handling
CREATE TEMP TABLE migration_test_temp AS SELECT 1 as test_value;
DROP TABLE migration_test_temp;

-- Log successful test execution
DO $$
BEGIN
    RAISE NOTICE 'Migration system test completed successfully at %', NOW();
END
$$;