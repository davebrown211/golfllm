import fs from 'fs'
import path from 'path'

export interface InstructionalWhitelistData {
  channels: Array<{
    id?: string
    name: string
    handle?: string
  }>
}

let cachedWhitelist: InstructionalWhitelistData | null = null

export function getInstructionalWhitelist(): InstructionalWhitelistData {
  if (cachedWhitelist) {
    return cachedWhitelist
  }
  
  try {
    const filePath = path.join(process.cwd(), '..', '..', 'instructional_whitelist.json')
    const jsonContent = fs.readFileSync(filePath, 'utf-8')
    cachedWhitelist = JSON.parse(jsonContent)
    return cachedWhitelist!
  } catch (error) {
    console.error('Error loading instructional whitelist:', error)
    return { channels: [] }
  }
}

export function getInstructionalChannelIds(): string[] {
  const whitelist = getInstructionalWhitelist()
  return whitelist.channels
    .filter(channel => channel.id)
    .map(channel => channel.id!)
}

export function getInstructionalCreatorNames(): string[] {
  const whitelist = getInstructionalWhitelist()
  return whitelist.channels.map(channel => channel.name.toLowerCase())
}

export function isInstructionalCreator(
  channelTitle: string,
  channelId?: string
): boolean {
  const whitelist = getInstructionalWhitelist()
  const titleLower = channelTitle.toLowerCase()
  
  // Check by channel ID first if provided
  if (channelId) {
    const hasChannelId = whitelist.channels.some(
      channel => channel.id === channelId
    )
    if (hasChannelId) return true
  }
  
  // Check by name
  return whitelist.channels.some(
    channel => channel.name.toLowerCase() === titleLower
  )
}