# Enable YouTube Data API v3

## Quick Fix Steps:

1. **Click this link** (from your error message):
   ```
   https://console.developers.google.com/apis/api/youtube.googleapis.com/overview?project=423974720166
   ```

2. **Click "ENABLE" button** on the page

3. **Wait 2-5 minutes** for the API to activate

4. **Test it works**:
   ```bash
   python test_postgres_collection.py
   ```

## Alternative: Create New API Key

If the above doesn't work, you can create a new project:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project
3. Enable YouTube Data API v3
4. Create new API key
5. Update your `.env` file:
   ```
   GOOGLE_API_KEY=your_new_key_here
   ```

## Verify API is Enabled

Once enabled, you should see:
- Status: "Enabled" ✓
- Quota: 10,000 units per day

## Common Issues

**"API not enabled" persists after enabling:**
- Clear any cache: `rm -rf __pycache__`
- Restart your terminal
- Wait full 5 minutes

**"Quota exceeded":**
- Wait until midnight Pacific Time
- Or create new project for fresh quota

## Test Collection After Enabling

```bash
# Quick test
python test_postgres_collection.py

# Full collection
python -m youtube_analyzer.app.data_collector
```

The error will disappear once the API is enabled!