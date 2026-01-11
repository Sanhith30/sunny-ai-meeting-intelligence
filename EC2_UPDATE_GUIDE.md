# 🔄 Update Your EC2 Deployment - Step by Step

This guide will help you update your existing EC2 deployment with the new user API key feature.

---

## 📋 What You'll Do

1. Connect to your EC2 instance
2. Pull the latest code from GitHub
3. Rebuild the Docker container
4. Verify everything works
5. Share with your users

**Time Required**: 5-10 minutes

---

## 🚀 Step-by-Step Instructions

### Step 1: Connect to Your EC2 Instance

#### On Windows (Using PuTTY)

1. **Open PuTTY**
2. **Enter your EC2 details**:
   - Host Name: `ubuntu@13.126.247.12`
   - Port: `22`
   - Connection type: SSH
3. **Load your private key**:
   - Go to: Connection → SSH → Auth → Credentials
   - Browse and select your `.ppk` file
4. **Click "Open"**
5. **You should see**: `ubuntu@ip-172-31-9-60:~$`

#### On Mac/Linux (Using Terminal)

```bash
# Connect via SSH
ssh -i /path/to/your-key.pem ubuntu@13.126.247.12
```

---

### Step 2: Navigate to Your Project Directory

```bash
# Go to the project folder
cd ~/sunny-ai-meeting-intelligence

# Verify you're in the right place
pwd
# Should show: /home/ubuntu/sunny-ai-meeting-intelligence
```

---

### Step 3: Pull Latest Code from GitHub

```bash
# Pull the latest changes
git pull origin main
```

**Expected Output**:
```
remote: Enumerating objects: 25, done.
remote: Counting objects: 100% (25/25), done.
remote: Compressing objects: 100% (12/12), done.
remote: Total 14 (delta 10), reused 0 (delta 0)
Unpacking objects: 100% (14/14), done.
From https://github.com/Sanhith30/sunny-ai-meeting-intelligence
   f8f921d..94ce90b  main       -> origin/main
Updating f8f921d..94ce90b
Fast-forward
 API_KEY_GUIDE.md           | 332 ++++++++++++++++++++++++++++++++++
 AWS_EC2_DEPLOYMENT.md      |  45 +++--
 CHANGELOG_API_KEYS.md      | 332 ++++++++++++++++++++++++++++++++++
 DEPLOYMENT_OPTIONS.md      |  23 ++-
 HUGGINGFACE_DEPLOYMENT.md  |  38 ++--
 README.md                  |  67 +++++--
 README_HF.md               |  28 ++-
 SHARING_GUIDE.md           |  19 +-
 USER_GUIDE.md              |  54 ++++--
 web/templates/index.html   | 156 +++++++++++-----
 10 files changed, 903 insertions(+), 116 deletions(-)
```

✅ **Success!** You now have the latest code.

---

### Step 4: Stop the Current Docker Container

```bash
# Stop the running container
sudo docker-compose -f docker-compose.ec2.yml down
```

**Expected Output**:
```
Stopping sunny-ai ... done
Removing sunny-ai ... done
Removing network sunny-ai-meeting-intelligence_default
```

---

### Step 5: Rebuild the Docker Container

```bash
# Rebuild with latest code
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

**Expected Output**:
```
Building sunny-ai
Step 1/15 : FROM python:3.11-slim
 ---> abc123def456
Step 2/15 : ENV PYTHONDONTWRITEBYTECODE=1
 ---> Using cache
 ---> xyz789abc123
...
Successfully built abc123def456
Successfully tagged sunny-ai:latest
Creating sunny-ai ... done
```

⏳ **This will take 2-3 minutes**

---

### Step 6: Verify Container is Running

```bash
# Check if container is running
sudo docker ps
```

**Expected Output**:
```
CONTAINER ID   IMAGE              COMMAND                  CREATED          STATUS          PORTS                    NAMES
abc123def456   sunny-ai:latest    "python -m uvicorn w…"   10 seconds ago   Up 8 seconds    0.0.0.0:8000->8000/tcp   sunny-ai
```

✅ **Look for**: `Up X seconds` in the STATUS column

---

### Step 7: Check Container Logs

```bash
# View the logs
sudo docker logs sunny-ai
```

**Expected Output** (last few lines):
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ **Success!** Your application is running.

---

### Step 8: Test the Health Check

```bash
# Test if the API is responding
curl http://localhost:8000/api/health
```

**Expected Output**:
```json
{
  "status": "healthy",
  "service": "Sunny AI",
  "timestamp": "2026-01-11T...",
  "gemini_configured": false,
  "llm_available": false,
  "controller_ready": true,
  "provider": "gemini"
}
```

✅ **Note**: `gemini_configured: false` is CORRECT! This means users will be prompted for their API key.

---

### Step 9: Open Port 8000 (If Not Already Done)

#### Option A: Using AWS Console (Recommended)

1. **Go to AWS Console** → EC2 → Security Groups
2. **Find your security group** (the one attached to your instance)
3. **Click "Edit inbound rules"**
4. **Click "Add rule"**
5. **Configure**:
   - Type: `Custom TCP`
   - Port range: `8000`
   - Source: `0.0.0.0/0` (Anywhere IPv4)
   - Description: `Sunny AI Web Interface`
6. **Click "Save rules"**

#### Option B: Test Locally First

```bash
# Test from EC2 itself
curl http://localhost:8000
```

If this works, the issue is just the security group.

---

### Step 10: Test from Your Browser

1. **Open your browser**
2. **Go to**: `http://13.126.247.12:8000`
3. **You should see**:
   - Sunny AI homepage
   - API key modal appears automatically
   - Beautiful interface

✅ **Success!** Your updated Sunny AI is live!

---

## 🎉 What's New?

### For You (Admin)
- ✅ No need to configure `GEMINI_API_KEY` in `.env`
- ✅ No API costs
- ✅ No rate limits
- ✅ Can share with unlimited users

### For Your Users
When they visit `http://13.126.247.12:8000`:

1. **They see a modal** asking for API key
2. **They click** "Get Free API Key from Google"
3. **They get their key** (takes 1 minute)
4. **They paste it** in the modal
5. **They click** "Save & Continue"
6. **They can use** all features for free!

---

## 📤 Share with Your Users

### Option 1: Share the URL

Simply share: **`http://13.126.247.12:8000`**

The app will automatically guide them to get their API key.

### Option 2: Share with Instructions

Send them this message:

```
🌟 Try Sunny AI - Your Free Meeting Assistant!

1. Visit: http://13.126.247.12:8000

2. Get your free API key (takes 1 minute):
   - Go to: https://aistudio.google.com/apikey
   - Sign in with Google
   - Click "Create API Key"
   - Copy your key

3. Paste your API key in Sunny AI

4. Start using it for free!

Features:
✅ Auto-join Zoom & Google Meet
✅ AI transcription
✅ Smart summaries
✅ Action items
✅ PDF reports
✅ Email delivery

Questions? Check the guide:
https://github.com/Sanhith30/sunny-ai-meeting-intelligence/blob/main/API_KEY_GUIDE.md
```

---

## 🔍 Troubleshooting

### Problem 1: "git pull" Shows Conflicts

**Solution**:
```bash
# Stash your local changes
git stash

# Pull latest code
git pull origin main

# If you had custom changes, reapply them
git stash pop
```

### Problem 2: Docker Build Fails

**Solution**:
```bash
# Clean up old containers and images
sudo docker system prune -a

# Try building again
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

### Problem 3: Container Keeps Restarting

**Check logs**:
```bash
sudo docker logs sunny-ai --tail 50
```

**Common issues**:
- Port 8000 already in use
- Missing dependencies
- Configuration errors

**Solution**:
```bash
# Stop all containers
sudo docker stop $(sudo docker ps -aq)

# Remove all containers
sudo docker rm $(sudo docker ps -aq)

# Rebuild
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

### Problem 4: Can't Access from Browser

**Check 1: Is container running?**
```bash
sudo docker ps
```

**Check 2: Is app responding locally?**
```bash
curl http://localhost:8000/api/health
```

**Check 3: Is port 8000 open in security group?**
- Go to AWS Console → EC2 → Security Groups
- Verify port 8000 is in inbound rules

**Check 4: Is Nginx configured?**
```bash
sudo systemctl status nginx
```

### Problem 5: API Key Modal Not Showing

**This is normal if**:
- You still have `GEMINI_API_KEY` in `.env` file
- The key is configured in environment variables

**To enable user API keys**:
```bash
# Edit .env file
nano .env

# Comment out or remove this line:
# GEMINI_API_KEY=your-key-here

# Save and exit (Ctrl+X, Y, Enter)

# Restart container
sudo docker-compose -f docker-compose.ec2.yml restart
```

---

## 🔄 Rollback (If Needed)

If something goes wrong, you can rollback:

```bash
# Go to project directory
cd ~/sunny-ai-meeting-intelligence

# Checkout previous version
git checkout f8f921d

# Rebuild
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

---

## ✅ Verification Checklist

After updating, verify:

- [ ] Container is running: `sudo docker ps`
- [ ] Logs show no errors: `sudo docker logs sunny-ai`
- [ ] Health check works: `curl http://localhost:8000/api/health`
- [ ] Can access from browser: `http://13.126.247.12:8000`
- [ ] API key modal appears
- [ ] Can enter API key and save
- [ ] Can join a test meeting

---

## 📊 Monitoring Your Deployment

### Check Container Status
```bash
# Is it running?
sudo docker ps

# View logs
sudo docker logs sunny-ai -f

# Check resource usage
sudo docker stats sunny-ai
```

### Check Application Health
```bash
# Health check
curl http://localhost:8000/api/health

# Check if web interface loads
curl http://localhost:8000
```

### Restart if Needed
```bash
# Restart container
sudo docker-compose -f docker-compose.ec2.yml restart

# Or rebuild completely
sudo docker-compose -f docker-compose.ec2.yml down
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

---

## 🎯 Next Steps

### 1. Set Up Custom Domain (Optional)

Make your URL prettier: `https://sunny-ai.yourdomain.com`

See: [AWS_EC2_DEPLOYMENT.md](AWS_EC2_DEPLOYMENT.md#domain--ssl-setup)

### 2. Set Up SSL/HTTPS (Recommended)

Add secure HTTPS connection:

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 3. Set Up Monitoring (Optional)

Monitor your deployment:
- AWS CloudWatch
- Uptime monitoring
- Log aggregation

### 4. Share with Your Team

Now that it's updated, share with everyone!

---

## 💡 Tips

### Tip 1: Keep Your Deployment Updated
```bash
# Check for updates weekly
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

### Tip 2: Backup Your Data
```bash
# Backup outputs and data
tar -czf sunny-ai-backup-$(date +%Y%m%d).tar.gz outputs/ data/ logs/
```

### Tip 3: Monitor Disk Space
```bash
# Check disk usage
df -h

# Clean up old Docker images
sudo docker system prune -a
```

### Tip 4: Set Up Auto-Updates (Advanced)
```bash
# Create update script
nano ~/update-sunny-ai.sh

# Add this content:
#!/bin/bash
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# Make executable
chmod +x ~/update-sunny-ai.sh

# Run weekly via cron
crontab -e
# Add: 0 2 * * 0 /home/ubuntu/update-sunny-ai.sh
```

---

## 📞 Need Help?

### Quick Commands Reference

```bash
# Connect to EC2
ssh -i your-key.pem ubuntu@13.126.247.12

# Navigate to project
cd ~/sunny-ai-meeting-intelligence

# Pull latest code
git pull origin main

# Rebuild container
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# Check status
sudo docker ps
sudo docker logs sunny-ai

# Restart
sudo docker-compose -f docker-compose.ec2.yml restart

# Stop
sudo docker-compose -f docker-compose.ec2.yml down
```

### Get Support

- **Documentation**: [AWS_EC2_DEPLOYMENT.md](AWS_EC2_DEPLOYMENT.md)
- **API Key Guide**: [API_KEY_GUIDE.md](API_KEY_GUIDE.md)
- **GitHub Issues**: https://github.com/Sanhith30/sunny-ai-meeting-intelligence/issues

---

## 🎉 You're Done!

Your EC2 deployment is now updated with the user API key feature!

**What you achieved**:
- ✅ Updated to latest version
- ✅ Users can provide their own API keys
- ✅ No API costs for you
- ✅ Sustainable and scalable
- ✅ Ready to share with everyone

**Share your Sunny AI**: `http://13.126.247.12:8000`

---

**Made with ☀️ by the Sunny AI team**

*Questions? Open an issue on GitHub!*
