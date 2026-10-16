# 🎬 YouTube Long-Form Video - GitHub Actions Setup Guide

## ⚡ Quick Answer: Is it GitHub Ready?

**YES!** The system is now fully GitHub Actions ready with:
- ✅ Automated video generation (60 phrases, ~5 minutes)
- ✅ Thumbnail generation (2 types: graphic + video frame)
- ✅ Title & description in one file (`youtube_upload_info.txt`)
- ✅ YouTube API upload with thumbnail
- ✅ Phrase history persistence (no repeats)

---

## ⏱️ Generation Time on GitHub Actions

| Step | Estimated Time |
|------|----------------|
| Checkout & Setup | 1-2 minutes |
| Install Dependencies | 2-3 minutes |
| Generate 60 Phrases (AI) | 2-3 minutes |
| Generate 60 Images | 2-3 minutes |
| Generate Audio (TTS) | 2-3 minutes |
| Create Video (FFmpeg) | 1-2 minutes |
| Upload Artifact | 1-2 minutes |
| **TOTAL** | **10-15 minutes** |

**Note:** GitHub Actions runners are typically faster than local machines for most steps.

---

## 📋 Required GitHub Secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions**

### Required Secrets:

```bash
# Pollinations AI (for content generation)
POLLINATIONS_API_KEY=sk_your_api_key_here

# AI Model selection
AI_MODEL=gemini-fast

# YouTube API (for automatic upload)
YT_CLIENT_ID=your_client_id
YT_CLIENT_SECRET=your_client_secret
YT_REFRESH_TOKEN=your_refresh_token
```

### Optional Secrets:
```bash
# If you want manual category selection
TIMEZONE_OFFSET_HOURS=-5
```

---

## 🔑 Getting YouTube API Credentials

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Velocity Swedish YouTube")
3. Enable **YouTube Data API v3**

### Step 2: Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Add authorized redirect URIs: `http://localhost`
5. Download the credentials JSON

### Step 3: Get Refresh Token
Run this locally once to get your refresh token:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
import json

flow = InstalledAppFlow.from_client_config({
    'web': {
        'client_id': 'YOUR_CLIENT_ID',
        'client_secret': 'YOUR_CLIENT_SECRET',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }
}, scopes=['https://www.googleapis.com/auth/youtube.upload'])

credentials = flow.run_local_server()
print('Refresh Token:', credentials.refresh_token)
"
```

### Step 4: Add to GitHub Secrets
Copy the refresh token and add it as `YT_REFRESH_TOKEN` secret.

---

## 🚀 Workflow Files

### 1. Daily Long-Form Generator
**File:** `.github/workflows/youtube_longform_generator.yml`

**Schedule:** Daily at 6:00 AM UTC (1:00 AM EST)

**What it does:**
- Generates 60 unique phrases (checks history)
- Creates 60 images with premium backgrounds
- Generates audio for all phrases
- Assembles 5-minute 16:9 video
- Generates thumbnail (graphic + video frame)
- Creates `youtube_upload_info.txt` with title, description, tags
- Uploads video artifact for download
- Commits phrase history (prevents repeats)

**Manual Trigger:**
```
Go to Actions → YouTube Long-Form Video Generator → Run workflow
Optional inputs:
  - Category: (leave empty for random)
  - Phrases: 60 (default)
```

### 2. Short-Form Reels (Existing)
**File:** `.github/workflows/daily_4x_upload.yml`

**Schedule:** 5x daily for Facebook/Instagram reels

---

## 📁 Generated Files Structure

After workflow runs, you get:

```
output/longform_videos/{Category}_{timestamp}/
├── final_video.mp4              # Main video (16:9, ~5 min)
├── thumbnail.jpg                # Generated graphic thumbnail
├── video_thumbnail_frame.jpg    # Frame extracted from video
├── youtube_upload_info.txt      # 📄 TITLE + DESCRIPTION + TAGS (all in one!)
├── video_metadata.json          # Structured metadata
└── [audio files and phrase images]
```

### `youtube_upload_info.txt` Contents:
```
================================================================================
YOUTUBE VIDEO UPLOAD INFORMATION
================================================================================

📌 RECOMMENDED TITLES (Choose one):
--------------------------------------------------------------------------------
1. Learn Swedish in 10 Minutes | Kindness Phrases...
2. 60 Chinese Phrases for Kindness...
3. Master Chinese Kindness...

================================================================================
📝 SELECTED TITLE (Recommended):
--------------------------------------------------------------------------------
Learn Swedish in 10 Minutes | Kindness Phrases Every Beginner NEEDS to Know! (善良)

================================================================================
📄 VIDEO DESCRIPTION:
--------------------------------------------------------------------------------
🇸🇪 Learn Swedish with Velocity Swedish! 🇸🇪

In this video, you'll learn 60 essential Swedish phrases...
[Full description with all 60 phrases, timestamps, tags, etc.]

================================================================================
🏷️ VIDEO TAGS (for YouTube):
--------------------------------------------------------------------------------
Learn Swedish, Chinese Phrases, Swedish, Kindness, ...
```

---

## 🎴 Thumbnail Upload

**YES, thumbnails are uploaded automatically!**

The workflow:
1. Generates `thumbnail.jpg` (graphic with "LEARN SWEDISH" title)
2. Extracts `video_thumbnail_frame.jpg` (actual frame from video at 5 seconds)
3. Uploads `thumbnail.jpg` to YouTube via API

**Thumbnail Features:**
- 1920x1080 resolution (YouTube recommended)
- "LEARN SWEDISH" main title
- Category name (English + Chinese)
- "60 Essential Phrases" subtitle
- Velocity Swedish branding

---

## 📥 Download & Manual Upload (Alternative)

If you prefer manual upload:

1. **Go to Actions tab** in your GitHub repository
2. **Click on the workflow run** (e.g., "YouTube Long-Form Video Generator")
3. **Scroll to Artifacts** section at bottom
4. **Download** `youtube-video-{run_number}`
5. **Extract** the ZIP file
6. **Open** `youtube_upload_info.txt`
7. **Upload to YouTube:**
   - Video: `final_video.mp4`
   - Thumbnail: `thumbnail.jpg`
   - Title: Copy from file
   - Description: Copy from file
   - Tags: Copy from file

---

## 🔧 Customization

### Change Upload Schedule
Edit `.github/workflows/youtube_longform_generator.yml`:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'  # Change this cron expression
```

**Cron examples:**
- `0 12 * * *` - Daily at 12:00 PM UTC
- `0 6 * * 1` - Every Monday at 6:00 AM UTC
- `0 6 1 * *` - First day of each month

### Change Number of Phrases
Edit `youtube_longform_automation.py`:
```python
TARGET_PHRASES = 60  # Change to 45, 90, 120, etc.
```

### Change Video Duration
Each phrase ≈ 5 seconds, so:
- 45 phrases ≈ 3.75 minutes
- 60 phrases ≈ 5 minutes
- 90 phrases ≈ 7.5 minutes
- 120 phrases ≈ 10 minutes

---

## ⚠️ Important Notes

### 1. YouTube API Quota Limits
- **Daily upload limit:** Varies by channel (new channels: ~6 videos/day)
- **API quota:** 10,000 units/day (uploads use ~1,600 units each)
- **Solution:** If quota exceeded, use manual upload method

### 2. Video Processing Time
- Videos upload as **PRIVATE** initially
- YouTube processes for ~5-10 minutes
- Review in YouTube Studio, then change to **PUBLIC**

### 3. Storage Management
- Artifacts retained for 7 days
- Phrase history retained for 90 days
- Consider cleaning old artifacts monthly

### 4. Cost Considerations
- **GitHub Actions:** Free for public repos, 2,000 minutes/month for private
- **Pollinations API:** Check your plan limits
- **YouTube API:** Free up to quota limits

---

## 🐛 Troubleshooting

### Video Generation Fails
```bash
# Check logs in Actions tab
# Look for "Generate Long-Form YouTube Video" step
# Common issues:
# - API key invalid
# - Insufficient quota
# - Font installation failed
```

### Thumbnail Not Uploading
```bash
# Check file size (must be <2MB)
# Check resolution (must be 1280x720 minimum)
# Manual upload: Use thumbnail.jpg from artifact
```

### Phrase History Lost
```bash
# Check if phrase-history artifact uploaded
# Verify commit was made to repository
# Check output/history/all_generated_phrases.json
```

### YouTube Upload Fails
```bash
# Check credentials in secrets
# Verify refresh token is valid (re-generate if expired)
# Check quota status in Google Cloud Console
```

---

## ✅ Pre-Flight Checklist

Before running on GitHub Actions:

- [ ] All secrets added to repository
- [ ] YouTube API credentials tested locally
- [ ] Pollinations API key valid
- [ ] Requirements.txt updated
- [ ] Workflow file committed
- [ ] Branch protection rules allow workflow

---

## 📞 Support

For issues:
1. Check Actions logs for error messages
2. Verify all secrets are set correctly
3. Test locally first with `python youtube_longform_automation.py`
4. Check phrase history for duplicates

---

**Made with ❤️ for Swedish learners worldwide**

🇸🇪 Velocity Swedish - Automated YouTube Content! 🇸🇪
