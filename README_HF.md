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

## 🚀 Features

### Core Features
- 🎥 **Auto-join Meetings**: Zoom & Google Meet support
- 🎤 **AI Transcription**: Powered by OpenAI Whisper
- � **Smart Summaries**: Using Google Gemini AI
- 📄 **PDF Reports**: Professional meeting reports
- 📧 **Email Delivery**: Automatic summary delivery
- 🌐 **Web Interface**: Beautiful, easy-to-use UI
- 🔌 **REST API**: Full programmatic access

### Advanced Features
- 👥 **Speaker Diarization**: Identify who said what
- 😊 **Sentiment Analysis**: Track meeting mood and engagement
- 📊 **Topic Segmentation**: Automatic topic detection
- ✅ **Action Item Extraction**: AI-powered task identification
- 📈 **Meeting Analytics**: Comprehensive metrics and insights
- 💌 **Follow-up Emails**: Auto-generated professional emails
- 🔍 **RAG Memory System**: Search across all past meetings

## 🎯 Quick Start

### 1. Get Your Free API Key (Required)

**Important:** Sunny AI requires your own free Gemini API key to work.

1. Visit **[Google AI Studio](https://aistudio.google.com/apikey)**
2. Sign in with Google
3. Click "Create API Key"
4. Copy your key

**Why?** Sunny AI is free and open-source. Each user provides their own API key to keep it free for everyone!

### 2. Configure API Keys

Go to **Settings → Repository secrets** and add:

- `GEMINI_API_KEY`: Your Gemini API key (**REQUIRED**)
- `HF_TOKEN`: Your HuggingFace token (optional, for speaker diarization)
- `GMAIL_ADDRESS`: Your Gmail address (optional, for email features)
- `GMAIL_APP_PASSWORD`: Gmail app password (optional)

### 3. Wait for Build

The app will automatically build and start. This takes about 10-15 minutes.

### 4. Start Using!

1. Open the web interface
2. The app will ask for your API key on first use
3. Enter your Gemini API key
4. Enter a meeting URL (Zoom or Google Meet)
5. Enter your email address
6. Click "Join Meeting"
7. Sunny AI will join, record, transcribe, and send you a summary!

## 📖 How It Works

1. **Join**: Sunny AI joins your meeting as a participant
2. **Record**: Captures high-quality audio throughout the meeting
3. **Transcribe**: Converts speech to text using Whisper AI
4. **Analyze**: Identifies speakers, topics, sentiment, and action items
5. **Summarize**: Generates intelligent summary using Gemini AI
6. **Report**: Creates professional PDF report
7. **Deliver**: Sends summary to your email

## 🎨 Use Cases

- **Remote Teams**: Never miss important meeting details
- **Sales Calls**: Track commitments and action items
- **Interviews**: Focus on conversation, not note-taking
- **Lectures**: Get comprehensive notes automatically
- **Client Meetings**: Professional summaries for follow-up
- **Team Standups**: Track decisions and blockers

## 📊 What You Get

### Meeting Summary Includes:
- Executive summary
- Key discussion points
- Decisions made
- Action items with owners and deadlines
- Speaker breakdown
- Topic timeline
- Sentiment analysis
- Meeting analytics
- Follow-up email draft

## 🔒 Privacy & Security

- All processing happens in your Space
- No data is stored permanently (unless you enable persistent storage)
- Audio files are deleted after processing
- Transcripts are only sent to your email
- HTTPS encryption for all communications

## ⚙️ Configuration

### Hardware Requirements

**Free Tier** (2 vCPU, 16GB RAM):
- ✅ Core features work
- ✅ Basic transcription
- ⚠️ Advanced features may be slow

**Upgraded** ($0.60/hour):
- ✅ All features enabled
- ✅ Fast processing
- ✅ Better performance

### Enable Persistent Storage

To keep meeting history:
1. Go to Settings
2. Enable "Persistent storage"
3. Select 50GB
4. Cost: $5/month

## 🛠️ Advanced Usage

### API Endpoints

```bash
# Health check
curl https://YOUR-SPACE.hf.space/api/health

# Join meeting
curl -X POST https://YOUR-SPACE.hf.space/api/meetings/join \
  -H "Content-Type: application/json" \
  -d '{"meeting_url": "https://zoom.us/j/123", "recipient_email": "you@email.com"}'

# Get status
curl https://YOUR-SPACE.hf.space/api/meetings/1/status

# Get summary
curl https://YOUR-SPACE.hf.space/api/meetings/1/summary

# Download PDF
curl https://YOUR-SPACE.hf.space/api/meetings/1/pdf -o summary.pdf
```

### Search Past Meetings

```bash
# Search memory
curl -X POST https://YOUR-SPACE.hf.space/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What did we decide about the project timeline?"}'

# Ask questions
curl -X POST https://YOUR-SPACE.hf.space/api/memory/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What action items were assigned to John?"}'
```

## 📚 Documentation

- [User Guide](https://github.com/Sanhith30/sunny-ai-meeting-intelligence/blob/main/USER_GUIDE.md)
- [Deployment Guide](https://github.com/Sanhith30/sunny-ai-meeting-intelligence/blob/main/HUGGINGFACE_DEPLOYMENT.md)
- [GitHub Repository](https://github.com/Sanhith30/sunny-ai-meeting-intelligence)
- [API Documentation](https://YOUR-SPACE.hf.space/docs)

## 🆚 Comparison with Otter.ai

Sunny AI provides **85% feature parity** with Otter.ai:

| Feature | Sunny AI | Otter.ai |
|---------|----------|----------|
| Auto-join meetings | ✅ | ✅ |
| AI transcription | ✅ | ✅ |
| Speaker identification | ✅ | ✅ |
| Meeting summaries | ✅ | ✅ |
| Action items | ✅ | ✅ |
| PDF export | ✅ | ✅ |
| Email delivery | ✅ | ✅ |
| Sentiment analysis | ✅ | ❌ |
| RAG memory | ✅ | ❌ |
| Self-hosted | ✅ | ❌ |
| **Cost** | **Free/Low** | **$16.99/mo** |

[Full comparison](https://github.com/Sanhith30/sunny-ai-meeting-intelligence/blob/main/OTTER_COMPARISON.md)

## 🐛 Troubleshooting

### Build Fails
- Check if all secrets are set correctly
- Try upgrading to CPU upgrade or GPU space

### Out of Memory
- Upgrade space hardware
- Reduce meeting duration limit in config

### Features Not Working
- Verify `GEMINI_API_KEY` is valid
- Verify `HF_TOKEN` is valid
- Check space logs for errors

### Email Not Sending
- Verify Gmail credentials
- Enable "Less secure app access" or use App Password
- Check spam folder

## 💡 Tips

1. **Test with short meetings first** to verify everything works
2. **Upgrade hardware** for best experience with all features
3. **Enable persistent storage** to keep meeting history
4. **Use private space** if handling sensitive meetings
5. **Monitor usage** to control costs

## 🤝 Contributing

Contributions welcome! Please visit the [GitHub repository](https://github.com/Sanhith30/sunny-ai-meeting-intelligence).

## 📄 License

MIT License - See [LICENSE](https://github.com/Sanhith30/sunny-ai-meeting-intelligence/blob/main/LICENSE) file

## 🙏 Acknowledgments

Built with:
- [OpenAI Whisper](https://github.com/openai/whisper) - Transcription
- [Google Gemini](https://ai.google.dev/) - Summarization
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) - Speaker diarization
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Playwright](https://playwright.dev/) - Browser automation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Sanhith30/sunny-ai-meeting-intelligence/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Sanhith30/sunny-ai-meeting-intelligence/discussions)
- **Email**: [Your Email]

---

**Made with ☀️ by [Your Name]**

**⭐ Star us on [GitHub](https://github.com/Sanhith30/sunny-ai-meeting-intelligence) if you find this useful!**
