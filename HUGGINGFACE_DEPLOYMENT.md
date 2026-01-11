# 🤗 Hugging Face Spaces Deployment Guide - Sunny AI

Deploy Sunny AI on Hugging Face Spaces with all features enabled!

---

## 🔑 Important: User API Keys Required

**Sunny AI is free and open-source.** Each user who accesses your Space will need their own **free** Gemini API key:

- ✅ **No cost to you** - Users provide their own keys
- ✅ **Better privacy** - Each user's data goes directly to Google
- ✅ **No rate limits** - Each user has their own quota
- ✅ **Fair usage** - Sustainable for everyone

**How it works:**
1. You deploy Sunny AI on HF Spaces
2. Users visit your Space
3. They enter their own API key (takes 1 minute to get)
4. They can use all features for free

📖 **Share this with your users**: [API_KEY_GUIDE.md](API_KEY_GUIDE.md)

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Create Hugging Face Space](#create-hugging-face-space)
3. [Configure Files](#configure-files)
4. [Deploy Application](#deploy-application)
5. [Enable All Features](#enable-all-features)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You'll Need:

- ✅ Hugging Face account ([Sign up here](https://huggingface.co/join))
- ✅ HuggingFace token ([Get here](https://huggingface.co/settings/tokens)) - for speaker diarization

### 🔑 About API Keys:

**You DON'T need to configure Gemini API keys in HF Spaces secrets!**

- ❌ No need to set `GEMINI_API_KEY` in repository secrets
- ❌ No need to configure Gmail credentials
- ✅ Users will provide their own API keys when they use the app
- ✅ This keeps your Space free and sustainable

**Optional**: 
- `HF_TOKEN` - Only needed for speaker diarization feature
- `GMAIL_*` - Only if you want to provide shared email service

### Cost:

- **Free Tier**: 2 vCPU, 16GB RAM, 50GB storage
- **Upgraded**: $0.60/hour for better performance
- **Persistent Storage**: $5/month for 50GB

---

## Create Hugging Face Space

### Step 1: Create New Space

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Configure:
   - **Space name**: `sunny-ai-meeting-assistant`
   - **License**: `MIT`
   - **Select SDK**: `Docker`
   - **Space hardware**: `CPU basic` (free) or `CPU upgrade` (better)
   - **Visibility**: `Public` or `Private`
4. Click **"Create Space"**

### Step 2: Clone Your Space

```bash
# Install git-lfs (if not already installed)
git lfs install

# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/sunny-ai-meeting-assistant
cd sunny-ai-meeting-assistant
```

---

## Configure Files

### Step 1: Create Dockerfile for Hugging Face

Create `Dockerfile`:

```dockerfile
# Sunny AI - Hugging Face Spaces Deployment
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    pkg-config \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    curl \
    wget \
    ca-certificates \
    git \
    # Playwright browser dependencies
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

# Copy application files
COPY . .

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch CPU version first
RUN pip install --no-cache-dir \
    torch==2.1.0 \
    torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Install core dependencies
RUN pip install --no-cache-dir \
    python-dotenv==1.0.0 \
    pyyaml==6.0.1 \
    pydantic[email]==2.5.0 \
    fastapi==0.108.0 \
    uvicorn==0.25.0 \
    jinja2==3.1.2 \
    httpx==0.26.0 \
    aiosqlite==0.19.0 \
    tenacity==8.2.3 \
    structlog==23.2.0

# Install audio/ML dependencies
RUN pip install --no-cache-dir \
    numpy==1.26.2 \
    soundfile==0.12.1 \
    sounddevice==0.4.6 \
    scipy==1.11.4

# Install Whisper
RUN pip install --no-cache-dir \
    faster-whisper==0.10.0

# Install AI/LLM
RUN pip install --no-cache-dir \
    google-generativeai==0.8.0

# Install PDF generation
RUN pip install --no-cache-dir \
    reportlab==4.0.7

# Install Playwright
RUN pip install --no-cache-dir \
    playwright==1.40.0 && \
    playwright install chromium

# Install advanced features
RUN pip install --no-cache-dir \
    pyannote.audio==3.1.1 \
    transformers>=4.35.0 \
    sentence-transformers>=2.2.0 \
    chromadb>=0.4.0 \
    scikit-learn>=1.3.0

# Create necessary directories
RUN mkdir -p outputs temp data logs

# Set environment variables
ENV PORT=7860
ENV HOST=0.0.0.0
ENV ENVIRONMENT=production

EXPOSE 7860

# Run the application
CMD ["python", "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "7860"]
```

### Step 2: Create README.md

Create `README.md`:

```markdown
---
title: Sunny AI Meeting Assistant
emoji: ☀️
colorFrom: yellow
colorTo: orange
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# ☀️ Sunny AI - Meeting Assistant

Your AI-powered meeting assistant that joins meetings, transcribes, and generates intelligent summaries.

## Features

- 🎥 Auto-join Zoom & Google Meet
- 🎤 AI Transcription (Whisper)
- 🧠 Smart Summaries (Gemini AI)
- 👥 Speaker Diarization
- 😊 Sentiment Analysis
- ✅ Action Item Extraction
- 📊 Meeting Analytics
- 📄 PDF Reports
- 📧 Email Delivery
- 🔍 RAG Memory System

## Setup

1. Add your API keys in Settings → Repository secrets:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `GMAIL_ADDRESS`: Your Gmail address (optional)
   - `GMAIL_APP_PASSWORD`: Gmail app password (optional)
   - `HF_TOKEN`: Your HuggingFace token

2. The app will start automatically!

## Usage

Access the web interface and:
1. Enter a meeting URL (Zoom or Google Meet)
2. Enter your email address
3. Click "Join Meeting"
4. Sunny AI will join, record, transcribe, and send you a summary!

## Documentation

- [User Guide](USER_GUIDE.md)
- [GitHub Repository](https://github.com/Sanhith30/sunny-ai-meeting-intelligence)

## License

MIT License - See [LICENSE](LICENSE) file
```

### Step 3: Create .env.example

Create `.env.example`:

```env
# Sunny AI Configuration for Hugging Face Spaces

# Required - Get from https://aistudio.google.com/apikey
GEMINI_API_KEY=your-gemini-api-key-here

# Optional - For email notifications
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password-here

# Required - For speaker diarization
HF_TOKEN=your-huggingface-token-here

# Server Configuration (auto-set by HF Spaces)
HOST=0.0.0.0
PORT=7860
ENVIRONMENT=production
```

### Step 4: Update config.yaml for HF Spaces

Create `config.hf.yaml`:

```yaml
# Sunny AI Configuration for Hugging Face Spaces
# ================================================

# General Settings
general:
  bot_name: "Sunny AI – Assistant"
  log_level: "INFO"
  output_dir: "./outputs"
  temp_dir: "./temp"

# Meeting Settings
meeting:
  max_duration_minutes: 180
  waiting_room_timeout_seconds: 300
  end_detection_interval_seconds: 10
  auto_leave_on_end: true

# Audio Settings
audio:
  sample_rate: 16000
  channels: 1
  format: "wav"
  chunk_duration_seconds: 30

# Transcription Settings (Whisper)
transcription:
  model_size: "base"  # Use base for faster processing on HF
  language: "en"
  device: "cpu"
  compute_type: "int8"

# Summarization Settings (Google Gemini)
summarization:
  provider: "gemini"
  gemini_api_key: "${GEMINI_API_KEY}"
  gemini_model: "gemini-1.5-flash"
  max_tokens: 2048
  temperature: 0.3
  chunk_size_tokens: 4000
  overlap_tokens: 200

# PDF Settings
pdf:
  font_family: "Helvetica"
  title_font_size: 18
  heading_font_size: 14
  body_font_size: 11
  margin: 50

# Email Settings
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "${GMAIL_ADDRESS}"
  sender_password: "${GMAIL_APP_PASSWORD}"
  subject_template: "Meeting Summary - {date} - {platform}"

# Browser Settings
browser:
  headless: true  # Must be true on HF Spaces
  timeout_ms: 30000
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Advanced Features Settings
advanced_features:
  # Speaker Diarization
  diarization_enabled: true
  huggingface_token: "${HF_TOKEN}"
  min_speakers: 1
  max_speakers: 10
  
  # Topic Segmentation
  topic_segmentation_enabled: true
  min_topic_duration_seconds: 60
  max_topics: 10
  
  # Sentiment Analysis
  sentiment_enabled: true
  sentiment_use_llm: true
  
  # Action Item Extraction
  action_items_enabled: true
  action_items_use_llm: true
  
  # Meeting Analytics
  analytics_enabled: true
  
  # Follow-up Email Generator
  followup_email_enabled: true
  company_name: ""
  sender_name: "Sunny AI"
  
  # RAG Memory System
  rag_memory_enabled: true
  memory_persist_dir: "./data/memory"
  memory_collection: "meeting_memory"
```

---

## Deploy Application

### Step 1: Copy Your Code

```bash
# Copy all files from your GitHub repo
git clone https://github.com/Sanhith30/sunny-ai-meeting-intelligence.git temp
cp -r temp/* .
rm -rf temp

# Or manually copy these folders:
# - web/
# - meeting_bot/
# - transcription/
# - summarization/
# - advanced_features/
# - pdf/
# - email_sender/
# - database/
# - utils/
# - config.yaml
# - requirements.txt
```

### Step 2: Add Secrets in Hugging Face (Optional)

**Note**: These secrets are now OPTIONAL. Users will provide their own API keys.

1. Go to your Space settings
2. Click **"Repository secrets"**
3. Add these secrets (only if you want to provide shared services):
   - `HF_TOKEN`: Your HuggingFace token (for speaker diarization)
   - `GMAIL_ADDRESS`: Your Gmail (optional, for shared email service)
   - `GMAIL_APP_PASSWORD`: Gmail app password (optional)

**You do NOT need to add `GEMINI_API_KEY`** - users will provide their own!

### Step 3: Push to Hugging Face

```bash
# Add all files
git add .

# Commit
git commit -m "Initial deployment of Sunny AI with all features"

# Push to Hugging Face
git push
```

### Step 4: Wait for Build

- Go to your Space URL: `https://huggingface.co/spaces/YOUR_USERNAME/sunny-ai-meeting-assistant`
- Wait 10-15 minutes for the build to complete
- You'll see "Running" when it's ready!

---

## Enable All Features

### Features Included:

✅ **Core Features:**
- Auto-join meetings (Zoom, Google Meet)
- AI transcription (Whisper)
- Meeting summaries (Gemini AI)
- PDF reports
- Email delivery
- Web interface
- Full REST API

✅ **Advanced Features:**
- Speaker diarization (pyannote.audio)
- Sentiment analysis (transformers)
- Topic segmentation
- Action item extraction
- Meeting analytics
- Follow-up email generation
- RAG memory system (ChromaDB)

### Hardware Requirements:

For all features to work smoothly:

1. **Upgrade Space Hardware:**
   - Go to Space Settings
   - Select **"CPU upgrade"** or **"GPU"**
   - Cost: ~$0.60/hour

2. **Enable Persistent Storage:**
   - Go to Space Settings
   - Enable **"Persistent storage"**
   - Select 50GB
   - Cost: $5/month

---

## Testing

### Step 1: Access Your Space

Open: `https://huggingface.co/spaces/YOUR_USERNAME/sunny-ai-meeting-assistant`

### Step 2: Test Health Check

```bash
curl https://YOUR_USERNAME-sunny-ai-meeting-assistant.hf.space/api/health
```

### Step 3: Test Meeting Join

1. Enter a test meeting URL
2. Enter your email
3. Click "Join Meeting"
4. Check logs in HF Space

---

## Troubleshooting

### Build Fails

**Issue**: Docker build times out

**Solution**: 
- Use smaller Whisper model (`base` instead of `medium`)
- Disable some advanced features temporarily
- Upgrade to GPU space

### Out of Memory

**Issue**: App crashes with OOM error

**Solution**:
- Upgrade space hardware
- Reduce `max_duration_minutes` in config
- Use smaller models

### Playwright Fails

**Issue**: Browser automation doesn't work

**Solution**:
- Ensure `headless: true` in config
- Check if all browser dependencies are installed
- Try upgrading space hardware

### Features Not Working

**Issue**: Advanced features disabled

**Solution**:
- Check if secrets are set correctly
- Verify HF_TOKEN is valid
- Check space logs for errors

---

## Comparison: HF Spaces vs EC2

| Feature | HF Spaces | AWS EC2 |
|---------|-----------|---------|
| **Setup Time** | 5 minutes | 30 minutes |
| **Cost (Free)** | 2 vCPU, 16GB RAM | t2.micro (1 vCPU, 1GB) |
| **Cost (Paid)** | $0.60/hour | $15-30/month |
| **Maintenance** | Zero | Manual updates |
| **Scaling** | Automatic | Manual |
| **SSL/HTTPS** | Automatic | Manual setup |
| **Custom Domain** | Limited | Full control |
| **Persistent Storage** | $5/month | Included |
| **Best For** | Quick deploy, demos | Production, custom needs |

---

## Advanced Configuration

### Enable GPU (Faster Processing)

Update Dockerfile:

```dockerfile
# Change device to cuda
ENV TRANSCRIPTION_DEVICE=cuda
ENV DIARIZATION_DEVICE=cuda
```

Update Space settings:
- Hardware: Select **"GPU - T4"**
- Cost: ~$0.60/hour

### Add Custom Domain

1. Go to Space Settings
2. Click "Custom domain"
3. Add your domain
4. Update DNS records
5. Wait for SSL certificate

### Enable Gradio Interface (Alternative UI)

Create `app.py`:

```python
import gradio as gr
from web.app import app

# Create Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# ☀️ Sunny AI Meeting Assistant")
    
    with gr.Row():
        meeting_url = gr.Textbox(label="Meeting URL")
        email = gr.Textbox(label="Your Email")
    
    submit_btn = gr.Button("Join Meeting")
    output = gr.Textbox(label="Status")
    
    submit_btn.click(
        fn=join_meeting,
        inputs=[meeting_url, email],
        outputs=output
    )

demo.launch()
```

---

## Monitoring & Maintenance

### View Logs

1. Go to your Space
2. Click "Logs" tab
3. Monitor real-time logs

### Check Usage

1. Go to Settings → Usage
2. View compute hours
3. Monitor storage

### Update Application

```bash
# Pull latest changes
git pull origin main

# Push to HF
git push
```

---

## Cost Optimization

### Free Tier Tips:

1. Use `base` Whisper model (faster)
2. Disable unused advanced features
3. Set shorter `max_duration_minutes`
4. Use CPU instead of GPU

### Paid Tier Benefits:

1. Faster processing
2. All features enabled
3. Better reliability
4. More concurrent users

---

## Security Best Practices

1. **Use Secrets**: Never commit API keys
2. **Private Space**: Make space private if handling sensitive data
3. **Rate Limiting**: Add rate limits to API endpoints
4. **Input Validation**: Validate all user inputs
5. **HTTPS Only**: HF Spaces provides automatic HTTPS

---

## Support & Resources

- **Hugging Face Docs**: https://huggingface.co/docs/hub/spaces
- **Docker SDK Guide**: https://huggingface.co/docs/hub/spaces-sdks-docker
- **Community Forum**: https://discuss.huggingface.co/
- **GitHub Issues**: https://github.com/Sanhith30/sunny-ai-meeting-intelligence/issues

---

## Quick Start Commands

```bash
# Create and clone space
git clone https://huggingface.co/spaces/YOUR_USERNAME/sunny-ai-meeting-assistant
cd sunny-ai-meeting-assistant

# Copy your code
cp -r /path/to/sunny-ai/* .

# Create Dockerfile (use content above)
nano Dockerfile

# Create README.md (use content above)
nano README.md

# Add secrets in HF web interface

# Push to deploy
git add .
git commit -m "Deploy Sunny AI"
git push
```

---

## 🎉 Congratulations!

Your Sunny AI is now deployed on Hugging Face Spaces with **ALL features enabled**!

**Access URL**: `https://YOUR_USERNAME-sunny-ai-meeting-assistant.hf.space`

**Features Working:**
- ✅ Auto-join meetings
- ✅ AI transcription
- ✅ Speaker diarization
- ✅ Sentiment analysis
- ✅ Topic segmentation
- ✅ Action items
- ✅ Meeting analytics
- ✅ RAG memory
- ✅ PDF reports
- ✅ Email delivery

**Next Steps:**
1. Test with a real meeting
2. Share with your team
3. Monitor usage and costs
4. Upgrade hardware if needed

---

**Need help?** Open an issue on GitHub or ask in HF Community! 🚀
