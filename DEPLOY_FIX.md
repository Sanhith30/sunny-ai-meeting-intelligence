# Fix Browser Automation Error on EC2

## Problem
When clicking "Let Sunny Attend", you get "An error occurred during processing" because:
1. Playwright browser needs to run in headless mode in Docker
2. Missing system dependencies for Chromium browser
3. Container crashed and needs to be rebuilt

## Solution - Quick Fix (5 minutes)

### Step 1: Connect to EC2
```bash
ssh -i your-key.pem ubuntu@13.126.247.12
cd ~/sunny-ai-meeting-intelligence
```

### Step 2: Update Config for Headless Mode
```bash
nano config.yaml
```

Find this line:
```yaml
browser:
  headless: false
```

Change it to:
```yaml
browser:
  headless: true
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 3: Update Dockerfile for Browser Dependencies
```bash
nano Dockerfile.minimal
```

Replace the entire file with this:

```dockerfile
# Sunny AI - Minimal Deployment with Browser Support
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system packages including browser dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    portaudio19-dev \
    libsndfile1 \
    build-essential \
    python3-dev \
    pkg-config \
    # Browser dependencies for Playwright
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libglib2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application
COPY . .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir python-dotenv pyyaml && \
    pip install --no-cache-dir pydantic[email] fastapi uvicorn && \
    pip install --no-cache-dir jinja2 httpx aiosqlite && \
    pip install --no-cache-dir tenacity structlog && \
    pip install --no-cache-dir numpy soundfile sounddevice && \
    pip install --no-cache-dir faster-whisper && \
    pip install --no-cache-dir google-generativeai && \
    pip install --no-cache-dir reportlab && \
    pip install --no-cache-dir playwright && \
    playwright install chromium --with-deps

# Create directories
RUN mkdir -p outputs temp data logs

ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 4: Rebuild and Restart Container
```bash
# Stop and remove old container
sudo docker stop sunny-ai
sudo docker rm sunny-ai

# Rebuild image
sudo docker build -f Dockerfile.minimal -t sunny-ai-meeting-intelligence-sunny-ai .

# Start new container with proper environment variables
sudo docker run -d \
  --name sunny-ai \
  --restart unless-stopped \
  -p 8000:8000 \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  -e ALLOWED_HOSTS=* \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  sunny-ai-meeting-intelligence-sunny-ai
```

### Step 5: Verify Container is Running
```bash
sudo docker ps
```

You should see `sunny-ai` with status "Up"

### Step 6: Check Logs
```bash
sudo docker logs sunny-ai --tail 30
```

Look for:
- ✅ "Sunny AI Web Server started"
- ✅ "Uvicorn running on http://0.0.0.0:8000"

### Step 7: Test in Browser
1. Go to: `http://13.126.247.12`
2. Enter your Gemini API key
3. Paste a Google Meet URL
4. Click "Let Sunny Attend"
5. Should see "Joining meeting..." instead of error

## What Changed?

1. **config.yaml**: `headless: false` → `headless: true`
   - Allows browser to run without display in Docker

2. **Dockerfile.minimal**: Added browser system libraries
   - `libnss3`, `libnspr4`, `libatk1.0-0`, etc.
   - These are required for Chromium to run

3. **Playwright install**: Added `--with-deps` flag
   - Ensures all browser dependencies are installed

## Troubleshooting

### If container won't start:
```bash
sudo docker logs sunny-ai
```

### If still getting errors:
```bash
# Check if Playwright is installed
sudo docker exec sunny-ai playwright --version

# Check if Chromium is installed
sudo docker exec sunny-ai ls -la /root/.cache/ms-playwright/
```

### If "Invalid host header" error:
Make sure you used the environment variables:
```bash
-e HOST=0.0.0.0 -e PORT=8000 -e ALLOWED_HOSTS=*
```

## Alternative: Use Docker Compose

If you prefer docker-compose:

```bash
# Stop current container
sudo docker stop sunny-ai
sudo docker rm sunny-ai

# Use docker-compose
sudo docker-compose -f docker-compose.ec2.yml down
sudo docker-compose -f docker-compose.ec2.yml build
sudo docker-compose -f docker-compose.ec2.yml up -d

# Check status
sudo docker-compose -f docker-compose.ec2.yml ps
sudo docker-compose -f docker-compose.ec2.yml logs -f
```

## Expected Result

After these changes:
- ✅ Container runs successfully
- ✅ Browser automation works in headless mode
- ✅ "Let Sunny Attend" joins meetings without errors
- ✅ Audio recording and transcription work
- ✅ Meeting summaries are generated

## Time Required
- Config change: 1 minute
- Dockerfile update: 2 minutes
- Rebuild: 5-10 minutes (depending on internet speed)
- Testing: 2 minutes

**Total: ~15 minutes**
