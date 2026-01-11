# ☀️ Sunny AI - User Guide

**Your Complete Guide to Using Sunny AI Meeting Assistant**

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Using the Web Interface](#using-the-web-interface)
3. [Using the Command Line](#using-the-command-line)
4. [Using the API](#using-the-api)
5. [Understanding Your Reports](#understanding-your-reports)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## 🚀 Getting Started

### Prerequisites

Before using Sunny AI, make sure you have:

1. **API Keys** (all free):
   - Google Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
   - Gmail app password from [Google Account](https://myaccount.google.com/apppasswords)
   - (Optional) HuggingFace token for speaker diarization

2. **Meeting Links**:
   - Google Meet URL (e.g., `https://meet.google.com/abc-defg-hij`)
   - Zoom meeting URL (e.g., `https://zoom.us/j/123456789`)

3. **Email Address**:
   - Where you want to receive meeting summaries

### First-Time Setup

1. **Configure Environment Variables**:
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your API keys
   GEMINI_API_KEY=your-gemini-api-key-here
   GMAIL_ADDRESS=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-app-password-here
   HF_TOKEN=your-huggingface-token-here  # Optional
   ```

2. **Customize Settings** (optional):
   - Edit `config.yaml` to adjust meeting duration, audio quality, AI models, etc.

3. **Test Your Setup**:
   ```bash
   # Run the web interface
   python -m web.app
   
   # Open http://localhost:8000 in your browser
   ```

---

## 🌐 Using the Web Interface

### Starting the Web Interface

```bash
# Start the server
python -m web.app

# Or specify custom host/port
python main.py --server --host 0.0.0.0 --port 8000
```

Open your browser to `http://localhost:8000`

### Joining a Meeting

1. **Enter Meeting Details**:
   - Paste your meeting URL (Google Meet or Zoom)
   - Enter your email address
   - Choose whether to send email summary

2. **Click "Join Meeting"**:
   - Sunny AI will open a browser window
   - The bot will join the meeting automatically
   - You'll see real-time status updates

3. **Monitor Progress**:
   - Watch the status indicator change:
     - 🔄 Starting
     - 🚪 Joining meeting
     - 🎙️ Recording audio
     - 📝 Transcribing
     - 🧠 Generating summary
     - 📄 Creating PDF
     - 📧 Sending email
     - ✅ Completed

4. **Get Your Results**:
   - Download PDF report from the interface
   - Check your email for the summary
   - View analytics and insights

### Dashboard Features

- **Active Sessions**: See all ongoing meetings
- **Meeting History**: Browse past meetings
- **Quick Actions**: Download PDFs, view transcripts
- **Analytics**: See meeting statistics and trends

---

## 💻 Using the Command Line

### Basic Usage

```bash
# Join a meeting and send summary via email
python main.py --url "https://meet.google.com/abc-defg-hij" --email "you@email.com"

# Join without sending email
python main.py --url "https://zoom.us/j/123456789" --email "you@email.com" --no-email

# Use custom config file
python main.py --config my_config.yaml --url "..." --email "..."
```

### Command Line Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--url` | `-u` | Meeting URL | `--url "https://meet.google.com/..."` |
| `--email` | `-e` | Recipient email | `--email "user@example.com"` |
| `--no-email` | | Skip email sending | `--no-email` |
| `--config` | `-c` | Config file path | `--config custom.yaml` |
| `--server` | `-s` | Run API server | `--server` |
| `--host` | | Server host | `--host 0.0.0.0` |
| `--port` | `-p` | Server port | `--port 8000` |
| `--log-level` | | Logging level | `--log-level DEBUG` |

### Example Workflows

**1. Quick Meeting Join**:
```bash
python main.py -u "https://meet.google.com/abc-defg-hij" -e "me@email.com"
```

**2. Silent Recording (no email)**:
```bash
python main.py -u "https://zoom.us/j/123456789" -e "me@email.com" --no-email
```

**3. Debug Mode**:
```bash
python main.py -u "..." -e "..." --log-level DEBUG
```

---

## 🔌 Using the API

### Starting the API Server

```bash
python main.py --server --port 8000
```

API documentation available at: `http://localhost:8000/docs`

### API Endpoints

#### 1. Join a Meeting

```bash
curl -X POST "http://localhost:8000/api/meetings/join" \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_url": "https://meet.google.com/abc-defg-hij",
    "recipient_email": "you@email.com",
    "send_email": true
  }'
```

**Response**:
```json
{
  "session_id": 1,
  "status": "starting",
  "message": "Meeting session started"
}
```

#### 2. Check Meeting Status

```bash
curl "http://localhost:8000/api/meetings/1/status"
```

**Response**:
```json
{
  "session_id": 1,
  "status": "recording",
  "platform": "google_meet",
  "duration": "00:15:30",
  "progress": 45
}
```

#### 3. Get Meeting Summary

```bash
curl "http://localhost:8000/api/meetings/1/summary"
```

**Response**:
```json
{
  "session_id": 1,
  "summary": "The team discussed Q1 roadmap...",
  "key_points": ["Point 1", "Point 2"],
  "action_items": [
    {
      "task": "Update documentation",
      "owner": "John",
      "deadline": "2026-01-15"
    }
  ]
}
```

#### 4. Download PDF Report

```bash
curl "http://localhost:8000/api/meetings/1/pdf" --output meeting_summary.pdf
```

#### 5. Get Meeting Analytics

```bash
curl "http://localhost:8000/api/meetings/1/analytics"
```

**Response**:
```json
{
  "duration": "00:45:30",
  "speakers": 4,
  "topics": 5,
  "sentiment": "positive",
  "speaker_stats": [
    {
      "speaker": "Speaker 1",
      "speaking_time": "15m 30s",
      "percentage": 34
    }
  ]
}
```

#### 6. Search Past Meetings (RAG)

```bash
curl -X POST "http://localhost:8000/api/memory/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did we decide about the API design?",
    "limit": 5
  }'
```

#### 7. Ask Questions About Meetings

```bash
curl -X POST "http://localhost:8000/api/memory/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who was assigned to work on the authentication feature?"
  }'
```

---

## 📊 Understanding Your Reports

### PDF Report Structure

Your meeting summary PDF includes:

#### 1. Header Section
- Meeting date and time
- Platform (Google Meet/Zoom)
- Duration
- Number of participants

#### 2. Executive Summary
- High-level overview of the meeting
- Main discussion points
- Key decisions made

#### 3. Speaker Analysis (if enabled)
- List of speakers identified
- Speaking time for each person
- Percentage of total speaking time
- Visual breakdown

#### 4. Detailed Transcript
- Full conversation with timestamps
- Speaker labels
- Organized by topic

#### 5. Topic Segmentation (if enabled)
- Meeting broken into topics
- Timestamp for each topic
- Summary of each topic

#### 6. Action Items (if enabled)
- Extracted tasks
- Assigned owners
- Deadlines mentioned
- Priority levels

#### 7. Sentiment Analysis (if enabled)
- Overall meeting sentiment
- Positive/negative moments
- Conflict detection
- Agreement levels

#### 8. Meeting Analytics
- Participation balance
- Word count statistics
- Engagement metrics
- Speaking pace

### Email Summary

The email you receive includes:

- **Subject**: "Meeting Summary - [Date] - [Platform]"
- **Body**: 
  - Quick summary
  - Key action items
  - Link to full PDF (if hosted)
  - Meeting metadata

---

## 🎯 Advanced Features

### 1. Speaker Diarization

**What it does**: Identifies who said what in the meeting

**How to enable**:
```yaml
# In config.yaml
advanced_features:
  diarization_enabled: true
  huggingface_token: "your-hf-token"
  min_speakers: 1
  max_speakers: 10
```

**Requirements**:
- HuggingFace token (free)
- Accept pyannote.audio terms on HuggingFace

**Output**:
- Speaker labels in transcript
- Speaking time per person
- Participation analytics

### 2. Topic Segmentation

**What it does**: Automatically breaks meeting into topics

**How to enable**:
```yaml
advanced_features:
  topic_segmentation_enabled: true
  min_topic_duration_seconds: 60
  max_topics: 10
```

**Output**:
- Topic titles
- Timestamps for each topic
- Topic summaries

### 3. Sentiment Analysis

**What it does**: Analyzes emotional tone of discussions

**How to enable**:
```yaml
advanced_features:
  sentiment_enabled: true
  sentiment_use_llm: true
```

**Output**:
- Overall sentiment (positive/negative/neutral)
- Sentiment timeline
- Conflict detection
- Agreement levels

### 4. Action Item Extraction

**What it does**: Automatically finds tasks and assignments

**How to enable**:
```yaml
advanced_features:
  action_items_enabled: true
  action_items_use_llm: true
```

**Output**:
- Task descriptions
- Assigned owners
- Deadlines
- Priority levels

### 5. Meeting Analytics

**What it does**: Provides detailed meeting metrics

**How to enable**:
```yaml
advanced_features:
  analytics_enabled: true
```

**Output**:
- Participation balance
- Speaking patterns
- Engagement scores
- Meeting efficiency metrics

### 6. RAG Memory System

**What it does**: Allows you to search and ask questions about past meetings

**How to enable**:
```yaml
advanced_features:
  rag_memory_enabled: true
  memory_persist_dir: "./data/memory"
```

**Usage**:
```bash
# Search past meetings
curl -X POST "http://localhost:8000/api/memory/search" \
  -d '{"query": "API design decisions"}'

# Ask questions
curl -X POST "http://localhost:8000/api/memory/ask" \
  -d '{"question": "What did we decide about authentication?"}'
```

### 7. Follow-up Email Generator

**What it does**: Creates professional follow-up emails

**How to enable**:
```yaml
advanced_features:
  followup_email_enabled: true
  company_name: "Your Company"
  sender_name: "Your Name"
```

**Output**:
- Professional email draft
- Includes action items
- Meeting recap
- Next steps

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Bot Can't Join Meeting

**Problem**: Browser opens but bot doesn't join

**Solutions**:
- Check meeting URL is correct
- Ensure meeting hasn't started yet (for waiting rooms)
- Try with `headless: false` in config to see what's happening
- Check if meeting requires authentication

#### 2. No Audio Recorded

**Problem**: Meeting completes but no audio file

**Solutions**:
- Check system audio permissions
- Ensure `ffmpeg` is installed
- Try different audio settings in config
- Check if meeting had any audio

#### 3. Transcription Fails

**Problem**: Audio recorded but transcription fails

**Solutions**:
- Check Whisper model is downloaded
- Try smaller model size (base or small)
- Ensure audio file is valid
- Check disk space

#### 4. Summary Generation Fails

**Problem**: Transcription works but no summary

**Solutions**:
- Verify Gemini API key is correct
- Check API quota/limits
- Try different model (gemini-1.5-flash)
- Check internet connection

#### 5. Email Not Sent

**Problem**: Summary generated but email fails

**Solutions**:
- Verify Gmail credentials
- Use App Password, not regular password
- Check SMTP settings
- Verify recipient email is valid

#### 6. Speaker Diarization Not Working

**Problem**: No speaker labels in transcript

**Solutions**:
- Verify HuggingFace token
- Accept pyannote.audio terms on HF
- Check if audio quality is sufficient
- Try adjusting min/max speakers

### Debug Mode

Run with debug logging to see detailed information:

```bash
python main.py --log-level DEBUG --url "..." --email "..."
```

### Log Files

Check logs in `./logs/` directory:
- `sunny_ai.log` - Main application log
- `meeting_<id>.log` - Per-meeting logs

---

## 💡 Best Practices

### For Best Results

1. **Meeting Duration**:
   - Works best with 15-60 minute meetings
   - For longer meetings, adjust `max_duration_minutes` in config

2. **Audio Quality**:
   - Ensure good internet connection
   - Use meetings with clear audio
   - Avoid meetings with heavy background noise

3. **Speaker Diarization**:
   - Works best with 2-6 speakers
   - Requires clear, distinct voices
   - May struggle with overlapping speech

4. **API Keys**:
   - Keep your API keys secure
   - Don't commit `.env` file to git
   - Rotate keys periodically

5. **Resource Usage**:
   - Speaker diarization is CPU-intensive
   - Consider using smaller Whisper models for faster processing
   - Clean up old recordings periodically

### Privacy & Security

1. **Data Storage**:
   - Audio files stored in `./outputs/`
   - Transcripts stored in database
   - Delete sensitive recordings after processing

2. **API Keys**:
   - Never share your API keys
   - Use environment variables
   - Rotate keys if compromised

3. **Meeting Content**:
   - Be aware of what's being recorded
   - Follow your organization's policies
   - Inform meeting participants

### Performance Tips

1. **Faster Processing**:
   ```yaml
   transcription:
     model_size: "base"  # Smaller = faster
     device: "cuda"  # If you have GPU
   
   advanced_features:
     diarization_enabled: false  # Disable if not needed
   ```

2. **Better Accuracy**:
   ```yaml
   transcription:
     model_size: "large"  # Larger = more accurate
   
   summarization:
     gemini_model: "gemini-1.5-pro"  # More capable model
   ```

3. **Cost Optimization**:
   - Use `gemini-1.5-flash` (free tier)
   - Disable features you don't need
   - Process shorter meetings

---

## 📞 Getting Help

### Resources

- **Documentation**: See [README.md](README.md)
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Docs**: `http://localhost:8000/docs`
- **GitHub Issues**: Report bugs and request features

### Support Channels

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and community support
- **Email**: For private inquiries

### Contributing

Found a bug or want to add a feature? Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 🎓 Example Use Cases

### 1. Daily Standup
```bash
# Quick 15-minute standup
python main.py -u "https://meet.google.com/..." -e "team@company.com"
```

### 2. Client Meeting
```yaml
# Enable all features for important meetings
advanced_features:
  diarization_enabled: true
  sentiment_enabled: true
  action_items_enabled: true
  followup_email_enabled: true
```

### 3. Training Session
```yaml
# Focus on transcription accuracy
transcription:
  model_size: "large"
  
advanced_features:
  topic_segmentation_enabled: true
```

### 4. Interview Recording
```yaml
# Detailed speaker analysis
advanced_features:
  diarization_enabled: true
  analytics_enabled: true
  sentiment_enabled: true
```

---

## 🚀 Next Steps

Now that you know how to use Sunny AI:

1. **Try your first meeting**: Start with a short test meeting
2. **Explore features**: Enable advanced features one by one
3. **Customize**: Adjust config to your needs
4. **Integrate**: Use the API in your workflows
5. **Share feedback**: Help us improve!

---

**Happy Meeting! ☀️**

*Built with ❤️ for productive meetings*
