# 🚀 Sunny AI - Deployment Options

Choose the best deployment option for your needs!

---

## 🔑 Important: User API Keys

**Sunny AI is free and open-source.** Each user needs their own **free** Gemini API key:

- ✅ **No cost to you** - Users provide their own keys
- ✅ **Takes 1 minute** - Get from [Google AI Studio](https://aistudio.google.com/apikey)
- ✅ **Completely free** - No credit card required
- ✅ **Fair usage** - Sustainable for everyone

When users visit your deployed Sunny AI, they'll be prompted to enter their API key before using it.

📖 **Share this guide with your users**: [API_KEY_GUIDE.md](API_KEY_GUIDE.md)

---

## 📊 Quick Comparison

| Feature | AWS EC2 | Hugging Face Spaces | Railway |
|---------|---------|---------------------|---------|
| **Setup Time** | 30 minutes | 5 minutes | 5 minutes |
| **Cost (Free)** | ❌ | ✅ 2 vCPU, 16GB RAM | ✅ $5 credit |
| **Cost (Paid)** | $15-30/month | $0.60/hour (~$432/mo) | $20-50/month |
| **All Features** | ✅ | ✅ | ⚠️ Limited |
| **Maintenance** | Manual | Zero | Zero |
| **Custom Domain** | ✅ Full control | ⚠️ Limited | ✅ |
| **Persistent Storage** | ✅ Included | $5/month extra | ✅ Included |
| **SSL/HTTPS** | Manual setup | ✅ Automatic | ✅ Automatic |
| **Scaling** | Manual | Automatic | Automatic |
| **Best For** | Production, custom needs | Quick demos, testing | Small teams |

---

## 1️⃣ AWS EC2 (Recommended for Production)

### ✅ Pros
- Full control over infrastructure
- Cost-effective for 24/7 usage
- Persistent storage included
- Custom domain support
- Can scale as needed
- One-time setup, runs forever

### ❌ Cons
- Requires AWS account
- Manual setup and maintenance
- Need to manage security updates
- Requires basic Linux knowledge

### 💰 Cost
- **t3.small**: ~$15/month (2 vCPU, 2GB RAM)
- **t3.medium**: ~$30/month (2 vCPU, 4GB RAM)
- Storage: ~$1/month for 30GB

### 📖 Guide
See [AWS_EC2_DEPLOYMENT.md](AWS_EC2_DEPLOYMENT.md) for full instructions.

### 🎯 Best For
- Production deployments
- Teams using it regularly
- Need 24/7 availability
- Want full control

---

## 2️⃣ Hugging Face Spaces (Recommended for Demos)

### ✅ Pros
- Fastest setup (5 minutes)
- Free tier available
- Zero maintenance
- Automatic HTTPS
- Great for sharing demos
- All features work

### ❌ Cons
- Expensive for 24/7 usage ($432/month)
- Limited customization
- Persistent storage costs extra
- May have cold starts

### 💰 Cost
- **Free Tier**: 2 vCPU, 16GB RAM (with limits)
- **CPU Upgrade**: $0.60/hour (~$432/month for 24/7)
- **Persistent Storage**: $5/month for 50GB

### 📖 Guide
See [HUGGINGFACE_DEPLOYMENT.md](HUGGINGFACE_DEPLOYMENT.md) for full instructions.

### 🎯 Best For
- Quick demos and testing
- Sharing with stakeholders
- Proof of concept
- Occasional use

---

## 3️⃣ Railway (Good for Small Teams)

### ✅ Pros
- Easy setup
- Automatic deployments from GitHub
- Free $5 credit
- Good for small teams
- Automatic HTTPS

### ❌ Cons
- Limited resources on free tier
- Some advanced features may not work
- Can get expensive with usage
- Less control than EC2

### 💰 Cost
- **Free**: $5 credit (runs out quickly)
- **Paid**: $20-50/month depending on usage

### 📖 Guide
See [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) for full instructions.

### 🎯 Best For
- Small teams
- Development/staging environments
- GitHub-based workflows

---

## 🎯 Recommendation by Use Case

### For Personal Use / Testing
**→ Hugging Face Spaces (Free Tier)**
- Quick to set up
- No cost for occasional use
- Easy to share

### For Small Team (< 10 people)
**→ AWS EC2 (t3.small)**
- Cost-effective at $15/month
- Runs 24/7
- All features work
- Good performance

### For Medium Team (10-50 people)
**→ AWS EC2 (t3.medium)**
- Better performance
- Can handle concurrent users
- Still cost-effective at $30/month

### For Enterprise
**→ AWS EC2 (t3.large or bigger)**
- Full control
- Can scale horizontally
- Custom security requirements
- Integration with existing infrastructure

### For Demos / Presentations
**→ Hugging Face Spaces**
- Professional URL
- Zero setup time
- Always available
- Easy to share

---

## 📋 Feature Availability

| Feature | EC2 | HF Spaces | Railway |
|---------|-----|-----------|---------|
| Auto-join meetings | ✅ | ✅ | ✅ |
| AI transcription | ✅ | ✅ | ✅ |
| Meeting summaries | ✅ | ✅ | ✅ |
| PDF reports | ✅ | ✅ | ✅ |
| Email delivery | ✅ | ✅ | ✅ |
| Speaker diarization | ✅ | ✅ | ❌ |
| Sentiment analysis | ✅ | ✅ | ❌ |
| Topic segmentation | ✅ | ✅ | ❌ |
| Action items | ✅ | ✅ | ✅ |
| Meeting analytics | ✅ | ✅ | ❌ |
| RAG memory | ✅ | ✅ | ❌ |
| Follow-up emails | ✅ | ✅ | ✅ |

---

## 🚀 Quick Start Commands

### AWS EC2
```bash
# Use automated script
curl -O https://raw.githubusercontent.com/Sanhith30/sunny-ai-meeting-intelligence/main/scripts/ec2-setup.sh
chmod +x ec2-setup.sh
./ec2-setup.sh
```

### Hugging Face Spaces
```bash
# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/sunny-ai
cd sunny-ai

# Copy files from GitHub
git clone https://github.com/Sanhith30/sunny-ai-meeting-intelligence.git temp
cp -r temp/* .
rm -rf temp

# Push to deploy
git add .
git commit -m "Deploy Sunny AI"
git push
```

### Railway
```bash
# Connect GitHub repo
# Railway will auto-deploy from main branch
# Just push your code!
git push origin main
```

---

## 💡 Tips for Each Platform

### AWS EC2 Tips
1. Use Elastic IP to keep same IP address
2. Set up CloudWatch for monitoring
3. Enable automatic backups
4. Use security groups properly
5. Consider using Auto Scaling for high traffic

### Hugging Face Tips
1. Start with free tier to test
2. Upgrade only when needed
3. Enable persistent storage for memory features
4. Use private space for sensitive meetings
5. Monitor usage to control costs

### Railway Tips
1. Connect GitHub for auto-deploy
2. Use environment variables for secrets
3. Monitor usage to avoid surprises
4. Consider upgrading for better performance
5. Use minimal build to reduce costs

---

## 🔒 Security Considerations

### AWS EC2
- ✅ Full control over security
- ✅ Can use VPC, security groups
- ✅ Can integrate with AWS IAM
- ⚠️ You manage security updates

### Hugging Face Spaces
- ✅ Automatic security updates
- ✅ HTTPS by default
- ✅ Can make space private
- ⚠️ Less control over infrastructure

### Railway
- ✅ Automatic security updates
- ✅ HTTPS by default
- ✅ Environment variables encrypted
- ⚠️ Less control over infrastructure

---

## 📞 Support

- **AWS EC2**: [AWS_EC2_DEPLOYMENT.md](AWS_EC2_DEPLOYMENT.md)
- **Hugging Face**: [HUGGINGFACE_DEPLOYMENT.md](HUGGINGFACE_DEPLOYMENT.md)
- **Railway**: [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)
- **General**: [GitHub Issues](https://github.com/Sanhith30/sunny-ai-meeting-intelligence/issues)

---

## 🎉 Ready to Deploy?

1. Choose your platform based on the comparison above
2. Follow the specific deployment guide
3. Configure your API keys
4. Test with a meeting
5. Share with your team!

**Need help deciding?** Open an issue on GitHub and we'll help you choose! 🚀
