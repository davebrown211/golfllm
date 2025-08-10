#!/usr/bin/env node

/**
 * Migration script to populate whitelisted_channels table from whitelist.json
 */

const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');
require('dotenv').config();

async function migrateWhitelist() {
    const pool = new Pool({
        connectionString: process.env.DATABASE_URL
    });

    try {
        // Read whitelist.json
        const whitelistPath = path.join(__dirname, '..', 'whitelist.json');
        const whitelistData = JSON.parse(fs.readFileSync(whitelistPath, 'utf-8'));
        
        console.log(`Found ${whitelistData.channels.length} channels in whitelist.json`);
        
        // Run the table creation migration first
        const migrationPath = path.join(__dirname, '..', 'frontend', 'golf-directory', 'src', 'lib', 'migrations', '007_add_whitelisted_channels_table.sql');
        const migrationSQL = fs.readFileSync(migrationPath, 'utf-8');
        
        await pool.query(migrationSQL);
        console.log('Created whitelisted_channels table');
        
        // Insert channels
        for (const channel of whitelistData.channels) {
            if (channel.id) {
                await pool.query(
                    'INSERT INTO whitelisted_channels (channel_id, name, active) VALUES ($1, $2, $3) ON CONFLICT (channel_id) DO UPDATE SET name = $2, active = $3',
                    [channel.id, channel.name || 'Unknown', true]
                );
            }
        }
        
        console.log(`Inserted ${whitelistData.channels.length} channels into database`);
        
        // Verify the data
        const result = await pool.query('SELECT COUNT(*) FROM whitelisted_channels WHERE active = true');
        console.log(`Active channels in database: ${result.rows[0].count}`);
        
    } catch (error) {
        console.error('Migration failed:', error);
        throw error;
    } finally {
        await pool.end();
    }
}

if (require.main === module) {
    migrateWhitelist().catch(console.error);
}

module.exports = { migrateWhitelist };