/**
 * Unified Whitelist Loader - Reads from shared JSON file
 */

import fs from 'fs'
import path from 'path'

export interface WhitelistChannel {
  id: string
  name: string
  handle?: string
}

export interface WhitelistData {
  channels: WhitelistChannel[]
}

let cachedWhitelist: WhitelistData | null = null

export function loadWhitelist(): WhitelistData {
  if (cachedWhitelist) {
    return cachedWhitelist
  }

  try {
    // Path to the JSON file (3 levels up from this file)
    const jsonPath = path.join(process.cwd(), '..', '..', 'whitelist.json')
    const jsonContent = fs.readFileSync(jsonPath, 'utf-8')
    cachedWhitelist = JSON.parse(jsonContent)
    return cachedWhitelist!
  } catch (error) {
    console.error('Error loading whitelist from JSON:', error)
    // Return empty whitelist as fallback
    return { channels: [] }
  }
}

export function getWhitelistedChannelIds(): string[] {
  const whitelist = loadWhitelist()
  return whitelist.channels.map(channel => channel.id)
}

export function getWhitelistedCreatorNames(): string[] {
  const whitelist = loadWhitelist()
  return whitelist.channels.map(channel => channel.name.toLowerCase())
}

export function isWhitelistedCreator(channelTitle: string, channelId?: string): boolean {
  const whitelist = loadWhitelist()
  
  // Check by channel ID first (most reliable)
  if (channelId && whitelist.channels.some(channel => channel.id === channelId)) {
    return true
  }

  // Check by channel name (case insensitive, partial match)
  const channelTitleLower = channelTitle.toLowerCase()
  return whitelist.channels.some(channel => 
    channelTitleLower.includes(channel.name.toLowerCase())
  )
}