/**
 * Video of the Day Query
 * Shared between frontend and backend to ensure consistent selection logic
 */

const fs = require('fs');
const path = require('path');

// Read the SQL query from file
const getVideoOfTheDayQuery = () => {
  // In Next.js, we need to resolve the path relative to the project root
  const queryPath = path.join(process.cwd(), 'src/lib/video-of-the-day-query.sql');
  return fs.readFileSync(queryPath, 'utf8');
};

module.exports = {
  getVideoOfTheDayQuery
};