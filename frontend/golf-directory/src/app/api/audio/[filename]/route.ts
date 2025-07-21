import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    const { filename } = params
    
    // Validate filename to prevent directory traversal
    if (!filename || filename.includes('..') || filename.includes('/')) {
      return NextResponse.json({ error: 'Invalid filename' }, { status: 400 })
    }
    
    // Only allow .mp3 files
    if (!filename.endsWith('.mp3')) {
      return NextResponse.json({ error: 'Only MP3 files are supported' }, { status: 400 })
    }
    
    const audioDir = '/opt/golf-directory/audio'
    const filepath = path.join(audioDir, filename)
    
    if (!existsSync(filepath)) {
      return NextResponse.json({ error: 'Audio file not found' }, { status: 404 })
    }
    
    const audioBuffer = await readFile(filepath)
    
    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': audioBuffer.length.toString(),
        'Content-Disposition': `inline; filename="${filename}"`,
        'Cache-Control': 'public, max-age=86400', // Cache for 24 hours
      }
    })
    
  } catch (error) {
    console.error('Error serving audio file:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}