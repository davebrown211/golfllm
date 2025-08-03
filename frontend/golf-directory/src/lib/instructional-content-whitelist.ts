// YouTube Golf Instructional Creator Whitelist
import { 
  getInstructionalChannelIds, 
  getInstructionalCreatorNames, 
  isInstructionalCreator as isInstructionalFromJson 
} from './instructional-whitelist-loader'

// Export arrays for backward compatibility
export const INSTRUCTIONAL_CHANNEL_IDS = getInstructionalChannelIds()
export const INSTRUCTIONAL_GOLF_CREATORS = getInstructionalCreatorNames()

// Function to check if a channel is an instructional creator
export function isInstructionalCreator(
  channelTitle: string,
  channelId?: string
): boolean {
  return isInstructionalFromJson(channelTitle, channelId)
}