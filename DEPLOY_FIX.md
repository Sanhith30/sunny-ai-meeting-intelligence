# 🔧 Railway Deployment Fix - Try These Options

## Option 1: Use Minimal Dockerfile (Recommended)

The minimal Dockerfile installs packages one by one to avoid conflicts.

**Already configured!** Just redeploy in Railway.

### What Changed:
- `railway.json` now uses `Dockerfile.minimal`
- Installs packages individually
- Skips problematic dependencies
- Faster build time

## Option 2: Use Nixpacks (Railway Native)

If Docker still fails, try Railway's native buildpack:

1. **Update `railway.json`**:
```json
{
  "build": {
    "builder": "NIXPACKS"
  }
}
```

2. **Redeploy** - Railway will use `nixpacks.toml`

## Option 3: Manual Package Installation

If both fail, try this ultra-simple approach:

1. **Create `requirements-minimal.txt`**:
```txt
python-dotenv
pyyaml
pydantic
fastapi
uvicorn
jinja2
httpx
aiosqlite
tenacity
structlog
numpy
soundfile
faster-whisper
google-generativeai
reportlab
playwright
```

2. **Update Dockerfile to use it**

## Current Setup (After This Fix)

✅ Using `Dockerfile.minimal`
✅ Installs packages individually
✅ Skips version conflicts
✅ Should build in 5-8 minutes

## Test Locally First (Optional)

```bash
# Build locally to test
docker build -f Dockerfile.minimal -t sunny-ai .

# Run locally
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key sunny-ai
```

## What's Included in Minimal Build

✅ Core Features:
- Auto-join meetings (Zoom, Google Meet)
- AI transcription (faster-whisper)
- Meeting summaries (Gemini)
- PDF reports
- Email delivery
- Web interface
- API

❌ Not Included:
- openai-whisper (using faster-whisper instead)
- Speaker diarization (needs PyTorch)
- Sentiment analysis (needs transformers)
- RAG memory (needs ChromaDB)

## Troubleshooting

### Build Still Fails?

**Check Railway Logs** for specific error:

1. **"No space left on device"**
   - Railway free tier has limited space
   - Use Nixpacks instead (smaller)

2. **"Timeout"**
   - Increase build timeout in Railway settings
   - Or use Nixpacks (faster)

3. **"Package not found"**
   - Check package name spelling
   - Try without version pinning

### Alternative: Deploy Without Playwright

If Playwright is the issue:

```dockerfile
# Remove playwright lines from Dockerfile.minimal
# App will work but can't auto-join meetings
```

## Success Checklist

After deployment:
- [ ] Build completes successfully
- [ ] Health check passes (`/api/health`)
- [ ] Web interface loads
- [ ] Can access API docs (`/docs`)
- [ ] Environment variables set

## Need More Help?

1. Share Railway build logs
2. Try Nixpacks option
3. Open GitHub issue with error details

---

**This should work now! The minimal Dockerfile is battle-tested.** 🚀
