import { NextResponse } from 'next/server'
import StartupManager from '@/lib/startup'
import pool from '@/lib/database'

export async function GET() {
  try {
    // Check database connectivity
    let dbStatus = 'disconnected'
    try {
      const client = await pool.connect()
      await client.query('SELECT 1')
      client.release()
      dbStatus = 'connected'
    } catch (error) {
      dbStatus = 'error'
    }

    // Get startup manager status
    const startupStatus = StartupManager.getStatus()

    return NextResponse.json({
      startup: {
        initialized: startupStatus.initialized,
        database: dbStatus,
        scheduler: {
          running: false,
          tasks: [],
          count: 0,
          note: 'Scheduler removed from frontend - using Python backend'
        }
      },
      server_time: new Date().toISOString(),
      environment: process.env.NODE_ENV
    })
  } catch (error) {
    return NextResponse.json(
      { 
        error: 'Failed to get startup status',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

export async function POST() {
  try {
    console.log('Manual startup initialization requested...')
    await StartupManager.initialize()
    
    const status = StartupManager.getStatus()
    
    return NextResponse.json({
      message: 'Startup initialization completed',
      status: {
        initialized: status.initialized,
        scheduler_running: false,
        scheduler_tasks: 0,
        note: 'Frontend scheduler removed - using Python backend'
      }
    })
  } catch (error) {
    return NextResponse.json(
      { 
        error: 'Startup initialization failed',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}