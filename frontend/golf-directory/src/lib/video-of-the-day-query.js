/**
 * Video of the Day Query
 * Shared between frontend and backend to ensure consistent selection logic
 */

const fs = require('fs');
const path = require('path');

// Read the SQL query from shared file (single source of truth)
const getVideoOfTheDayQuery = () => {
  // Use the shared query file that both frontend and backend use
  const queryPath = path.join(process.cwd(), '..', '..', 'shared', 'video-of-the-day-query.sql');
  return fs.readFileSync(queryPath, 'utf8');
};

module.exports = {
  getVideoOfTheDayQuery
};