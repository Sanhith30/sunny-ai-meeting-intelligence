# 🚂 Railway Deployment Guide

## Quick Deploy (Recommended)

### Option 1: Lightweight Deployment (Fastest)

This uses `Dockerfile.railway` which skips heavy ML features for faster deployment.

1. **Push to GitHub**:
```bash
git add .
git commit -m "Railway deployment setup"
git push origin main
```

2. **Deploy on Railway**:
   - Go to [Railway](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will automatically detect `railway.json`

3. **Set Environment Variables**:
   ```
   GEMINI_API_KEY=your-gemini-api-key
   GMAIL_ADDRESS=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-app-password
   PORT=8000
   ```

4. **Deploy!**
   - Railway will build and deploy automatically
   - Build time: ~5-10 minutes

### Option 2: Full Features Deployment

If you want all advanced features (speaker diarization, sentiment analysis, etc.):

1. **Update railway.json**:
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  }
}
```

2. **Add HuggingFace Token** (for speaker diarization):
   ```
   HF_TOKEN=your-huggingface-token
   ```

3. **Deploy**:
   - Build time: ~15-20 minutes (larger image)
   - More memory required

## Troubleshooting

### Build Fails with "exit code: 1"

**Solution 1: Use Lightweight Dockerfile**
```bash
# Update railway.json to use Dockerfile.railway
# This skips heavy ML packages
```

**Solution 2: Increase Build Timeout**
- Go to Railway project settings
- Increase build timeout to 30 minutes

**Solution 3: Use Railway's Build Cache**
- Railway caches Docker layers
- Subsequent builds will be faster

### Out of Memory During Build

**Solution**: Use the lightweight Dockerfile
```bash
# Dockerfile.railway uses less memory
# Skips PyTorch, pyannote.audio, etc.
```

### Playwright Browser Installation Fails

**Solution**: Already handled in Dockerfile
```dockerfile
RUN playwright install chromium --with-deps
```

If still fails, try:
```dockerfile
RUN playwright install chromium
```

### Application Crashes on Startup

**Check Logs**:
```bash
# In Railway dashboard, check deployment logs
```

**Common Issues**:
1. Missing environment variables
2. Port not set correctly (should be $PORT)
3. Database directory not writable

**Fix**:
```bash
# Ensure these are set:
PORT=8000
GEMINI_API_KEY=your-key
```

## Environment Variables

### Required
```env
GEMINI_API_KEY=your-gemini-api-key-here
```

### Optional (for email)
```env
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

### Optional (for advanced features)
```env
HF_TOKEN=your-huggingface-token
```

### System (auto-set by Railway)
```env
PORT=$PORT  # Railway sets this automatically
RAILWAY_ENVIRONMENT=production
```

## Features by Deployment Type

### Lightweight (Dockerfile.railway)
✅ Auto-join meetings (Zoom, Google Meet)
✅ AI transcription (Whisper)
✅ Meeting summaries (Gemini)
✅ PDF reports
✅ Email delivery
✅ Web interface
✅ API endpoints
❌ Speaker diarization (requires PyTorch)
❌ Sentiment analysis (requires transformers)
❌ RAG memory (requires ChromaDB)

### Full (Dockerfile)
✅ All lightweight features
✅ Speaker diarization
✅ Sentiment analysis
✅ Topic segmentation
✅ RAG memory system
✅ Meeting analytics

## Performance

### Lightweight Deployment
- **Build Time**: 5-10 minutes
- **Image Size**: ~2 GB
- **Memory Usage**: 512 MB - 1 GB
- **Startup Time**: 10-20 seconds

### Full Deployment
- **Build Time**: 15-20 minutes
- **Image Size**: ~5 GB
- **Memory Usage**: 1-2 GB
- **Startup Time**: 30-60 seconds

## Cost Estimation

Railway offers:
- **Free Tier**: $5 credit/month
- **Hobby Plan**: $5/month for more resources

### Estimated Usage
- **Lightweight**: ~$3-5/month (fits free tier)
- **Full**: ~$8-12/month (needs hobby plan)

## Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] Environment variables set in Railway
- [ ] Dockerfile selected (railway or full)
- [ ] Build completed successfully
- [ ] Health check passing
- [ ] Web interface accessible
- [ ] API endpoints working
- [ ] Meeting join tested

## Post-Deployment

### Test Your Deployment

1. **Health Check**:
```bash
curl https://your-app.railway.app/api/health
```

2. **Web Interface**:
```
https://your-app.railway.app
```

3. **API Test**:
```bash
curl -X POST https://your-app.railway.app/api/meetings/join \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_url": "https://meet.google.com/test",
    "recipient_email": "test@example.com"
  }'
```

### Monitor Your App

- **Logs**: Railway dashboard → Deployments → Logs
- **Metrics**: Railway dashboard → Metrics
- **Health**: Check `/api/health` endpoint

## Updating Your Deployment

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Railway auto-deploys on push
```

## Alternative: Deploy Without Docker

If Docker builds are too slow, use Python buildpack:

1. **Create `nixpacks.toml`**:
```toml
[phases.setup]
nixPkgs = ["python311", "ffmpeg"]

[phases.install]
cmds = ["pip install -r requirements-railway.txt"]

[start]
cmd = "uvicorn web.app:app --host 0.0.0.0 --port $PORT"
```

2. **Update railway.json**:
```json
{
  "build": {
    "builder": "NIXPACKS"
  }
}
```

## Support

If you encounter issues:

1. Check Railway logs
2. Review this guide
3. Open an issue on GitHub
4. Join Railway Discord for help

## Success! 🎉

Your Sunny AI is now deployed on Railway!

Access it at: `https://your-app.railway.app`

---

**Pro Tip**: Start with lightweight deployment, then upgrade to full features if needed.
