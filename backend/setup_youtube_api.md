# Fix YouTube API Access

## Quick Solution: Create New API Key

### Step 1: Go to Google Cloud Console
```
https://console.cloud.google.com
```

### Step 2: Create New Project (Optional but Recommended)
1. Click project dropdown (top left)
2. Click "New Project"
3. Name it "Golf YouTube Directory"
4. Click "Create"

### Step 3: Enable YouTube Data API v3
1. Go to: https://console.cloud.google.com/apis/library
2. Search for "YouTube Data API v3"
3. Click on it
4. Click "ENABLE"

### Step 4: Create New API Key
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "+ CREATE CREDENTIALS"
3. Choose "API key"
4. Copy the new key

### Step 5: (IMPORTANT) Check API Key Restrictions
1. Click on your new API key
2. Under "API restrictions":
   - Choose "Restrict key"
   - Select "YouTube Data API v3"
3. Under "Application restrictions":
   - Choose "None" (for testing)
4. Click "SAVE"

### Step 6: Update Your .env File
```bash
# Replace the old key with your new one
GOOGLE_API_KEY=your_new_api_key_here
```

### Step 7: Test It Works
```bash
python test_youtube_api_key.py
```

## If Still Blocked: Check Billing

YouTube API requires billing to be enabled (though it's free up to quota):

1. Go to: https://console.cloud.google.com/billing
2. Link a billing account to your project
3. Don't worry - YouTube API has free quota of 10,000 units/day

## Alternative: Use Existing Working API Key

If you have another Google API key that works with YouTube (from another project), you can:

1. Add it as a new environment variable:
   ```bash
   YOUTUBE_API_KEY=working_key_here
   ```

2. The code already checks for both `YOUTUBE_API_KEY` and `GOOGLE_API_KEY`

## Common Issues

**"Requests are blocked" for all methods:**
- API key has wrong restrictions
- Project doesn't have billing enabled
- Using wrong project's API key

**"API not enabled":**
- YouTube Data API v3 not enabled for the project
- Wait 5 minutes after enabling

**"Quota exceeded":**
- Wait until midnight Pacific Time
- Or use different project/API key