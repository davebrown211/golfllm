// Startup checks and initialization
import { channelMonitor } from './channel-monitor'
import pool from './database'

export class StartupManager {
  private static initialized = false

  static async initialize(): Promise<void> {
    if (this.initialized) return

    console.log('🚀 Starting StreamingRange initialization...')

    try {
      // 1. Check database connection
      await this.checkDatabase()
      
      // 2. Initialize channel monitoring
      await this.initializeChannelMonitoring()
      
      this.initialized = true
      console.log('✅ StreamingRange initialization complete!')
      
    } catch (error) {
      console.error('❌ Startup initialization failed:', error)
      throw error
    }
  }

  private static async checkDatabase(): Promise<void> {
    let retries = 3
    while (retries > 0) {
      try {
        const client = await pool.connect()
        await client.query('SELECT 1')
        client.release()
        console.log('✅ Database connection verified')
        return
      } catch (error) {
        retries--
        console.error(`❌ Database connection failed (${3-retries}/3):`, error)
        if (retries === 0) {
          throw error
        }
        // Wait 2 seconds before retry
        await new Promise(resolve => setTimeout(resolve, 2000))
      }
    }
  }

  private static async initializeChannelMonitoring(): Promise<void> {
    try {
      await channelMonitor.initializeChannels()
      console.log('✅ Channel monitoring initialized')
    } catch (error) {
      console.error('❌ Channel monitoring initialization failed:', error)
      // Don't throw - channel monitoring is not critical for startup
    }
  }


  static getStatus(): { initialized: boolean } {
    return { initialized: this.initialized }
  }
}

// Auto-initialize in server-side environments (but not during build)
if (typeof window === 'undefined' && process.env.NODE_ENV !== 'production') {
  // Small delay to let imports settle
  setTimeout(() => {
    StartupManager.initialize().catch(console.error)
  }, 1000)
}

export default StartupManager