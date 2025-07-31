// YouTube Golf Creator Whitelist - Now loaded from shared JSON file
import { 
  getWhitelistedChannelIds, 
  getWhitelistedCreatorNames, 
  isWhitelistedCreator as isWhitelistedFromJson 
} from './whitelist-loader'

// Export arrays for backward compatibility
export const WHITELISTED_CHANNEL_IDS = getWhitelistedChannelIds()
export const WHITELISTED_GOLF_CREATORS = getWhitelistedCreatorNames()

// Function to check if a channel is whitelisted
export function isWhitelistedCreator(
  channelTitle: string,
  channelId?: string
): boolean {
  return isWhitelistedFromJson(channelTitle, channelId)
}

// Professional tournament patterns to exclude
export const EXCLUDED_TOURNAMENT_PATTERNS = [
  /round \d+/i,
  /r\d+/i,
  /mpo \|/i,
  /fpo \|/i,
  /klpga/i,
  /kpga/i,
  /lpga tour/i,
  /pga tour/i,
  /dp world tour/i,
  /european tour/i,
  /asian tour/i,
  /kornferry/i,
  /fedex cup/i,
  /\d{4} open/i,
  /championship \d{4}/i,
  /tournament highlights/i,
  /final round/i,
  /course maintenance/i,
  /golf course setup/i,
  /superintendentlife/i,
];

// Function to check if content should be excluded (tournaments, maintenance, etc.)
export function isExcludedContent(title: string, description: string): boolean {
  const content = `${title} ${description}`.toLowerCase();

  return EXCLUDED_TOURNAMENT_PATTERNS.some((pattern) => pattern.test(content));
}
