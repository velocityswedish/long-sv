# YouTube API Setup Guide - Velocity Swedish

This guide will help you set up YouTube API credentials for automatic video uploads from GitHub Actions.

## 📋 Prerequisites

- Google Cloud Console account
- YouTube channel
- GitHub repository access

## 🔧 Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **New Project** (or select existing project)
3. Name it: `velocity-swedish-youtube`
4. Click **Create**

### 2. Enable YouTube Data API v3

1. In your project, go to **APIs & Services** > **Library**
2. Search for "YouTube Data API v3"
3. Click on it and press **Enable**

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Select **External** (unless you have Google Workspace)
3. Fill in required fields:
   - **App name**: Velocity Swedish YouTube Uploader
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **Save and Continue**
5. **Scopes**: Add these scopes:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube`
6. Click **Save and Continue**
7. **Test users**: Add your Google account email
8. Click **Save and Continue**

### 4. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `YouTube Uploader`
5. Click **Create**
6. **Save the Client ID and Client Secret** (you'll need these!)

### 5. Generate Refresh Token

Run this Python script locally to generate a refresh token:

```python
# save as: get_youtube_token.py
from google_auth_oauthlib.flow import InstalledAppFlow
import json

# Replace with your credentials
CLIENT_ID = 'YOUR_CLIENT_ID_HERE'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET_HERE'

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=[
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube'
    ]
)

# This will open a browser window for authentication
creds = flow.run_local_server(port=0)

# Save the refresh token
print("\n✅ Authentication successful!")
print(f"\n📋 Your credentials:")
print(f"Client ID: {CLIENT_ID}")
print(f"Client Secret: {CLIENT_SECRET}")
print(f"Refresh Token: {creds.refresh_token}")
print("\n💾 Save these to GitHub Secrets!")
```

Run the script:
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
python get_youtube_token.py
```

### 6. Add Credentials to GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add these three secrets:

| Secret Name | Value |
|------------|-------|
| `YT_CLIENT_ID` | Your OAuth Client ID |
| `YT_CLIENT_SECRET` | Your OAuth Client Secret |
| `YT_REFRESH_TOKEN` | Your Refresh Token from step 5 |

### 7. Verify Setup

The workflow will automatically:
- ✅ Generate a long-form video daily at 10 PM EST (3 AM UTC)
- ✅ Upload the video to YouTube
- ✅ Upload the custom thumbnail
- ✅ Add title, description, and tags
- ✅ Set video to **Private** (you can change to Public after review)

## 🎯 What Gets Uploaded

Every day, the workflow will:
1. Generate a 10-minute Swedish lesson video with 60 phrases
2. Create a custom thumbnail
3. Generate SEO-optimized title, description, and tags
4. Upload everything to YouTube automatically

## 📺 Video Visibility

- **Default**: Videos upload as **Private**
- **Recommended**: Review in YouTube Studio, then change to **Public**
- **Why**: Allows you to verify quality before public release

## 🔍 Troubleshooting

### Upload Fails

Check the GitHub Actions logs for error messages:
- **Invalid credentials**: Regenerate your refresh token
- **Quota exceeded**: YouTube API has daily limits (10,000 units/day)
- **Token expired**: Refresh tokens don't expire unless revoked

### Token Expired

If your refresh token stops working:
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Check if you revoked access
3. Re-run the token generation script (Step 5)

### Missing Credentials Error

Make sure all three secrets are added to GitHub:
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

## 📅 Schedule

- **Daily run time**: 10:00 PM EST (3:00 AM UTC)
- **Why this time**: Reaches American audience before they sleep
- **Change schedule**: Edit `.github/workflows/youtube_longform_generator.yml`

## 💡 Tips

1. **Check uploads daily**: Review new videos in YouTube Studio
2. **Change to Public**: After verifying quality, make videos public
3. **Monitor API quota**: YouTube has daily upload limits
4. **Keep credentials secure**: Never commit them to the repository

## 📞 Support

If you need help:
1. Check the GitHub Actions logs
2. Verify all secrets are set correctly
3. Test the workflow manually using **workflow_dispatch**

---

**Ready?** Once credentials are set, your YouTube channel will receive daily uploads automatically! 🚀
