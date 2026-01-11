# 🚀 Feature Update & Deployment Guide

**Complete guide for updating Sunny AI with new features and deploying to AWS EC2**

---

## 📋 Table of Contents

1. [Development Workflow](#development-workflow)
2. [Testing Locally](#testing-locally)
3. [Pushing to GitHub](#pushing-to-github)
4. [Deploying to EC2](#deploying-to-ec2)
5. [Rollback if Needed](#rollback-if-needed)
6. [Best Practices](#best-practices)

---

## 🔄 Development Workflow

### Step 1: Make Changes Locally

#### On Your Windows Machine

```bash
# Navigate to your project
cd "D:\Sunny AI\sunny_ai"

# Make sure you're on main branch
git branch

# Pull latest changes (if working with team)
git pull origin main
```

#### Make Your Changes

Edit any files you want:
- Add new features in Python files
- Update UI in `web/templates/index.html`
- Modify configuration in `config.yaml`
- Update dependencies in `requirements.txt`

**Example: Adding a new feature**
```python
# Edit web/app.py or any other file
# Add your new code
```

---

## 🧪 Testing Locally

### Step 2: Test Your Changes

#### Option A: Test with Python Directly

```bash
# Activate virtual environment (if you have one)
.\venv\Scripts\activate

# Install any new dependencies
pip install -r requirements.txt

# Run the application
python -m web.app

# Open browser: http://localhost:8000
# Test your new features
```

#### Option B: Test with Docker (Recommended)

```bash
# Build Docker image locally
docker build -f Dockerfile.minimal -t sunny-ai:test .

# Run container
docker run -d -p 8000:8000 --name sunny-ai-test sunny-ai:test

# Test in browser: http://localhost:8000

# Stop and remove test container
docker stop sunny-ai-test
docker rm sunny-ai-test
```

---

## 📤 Pushing to GitHub

### Step 3: Commit Your Changes

```bash
# Check what files changed
git status

# Add all changed files
git add .

# Or add specific files
git add web/app.py
git add web/templates/index.html

# Commit with descriptive message
git commit -m "Add new feature: [describe your feature]"

# Example commit messages:
# git commit -m "Add real-time transcription feature"
# git commit -m "Fix: Email sending bug"
# git commit -m "Update: Improve UI design"
# git commit -m "Feature: Add Microsoft Teams support"
```

### Step 4: Push to GitHub

```bash
# Push to GitHub
git push origin main

# If you get errors, pull first then push
git pull origin main
git push origin main
```

✅ **Your code is now on GitHub!**

---

## 🌐 Deploying to EC2

### Step 5: Connect to Your EC2 Instance

#### On Windows (Using PuTTY)

1. Open PuTTY
2. Host: `ubuntu@13.126.247.12`
3. Port: `22`
4. Load your `.ppk` key
5. Click "Open"

#### On Mac/Linux

```bash
ssh -i your-key.pem ubuntu@13.126.247.12
```

---

### Step 6: Pull Latest Code on EC2

```bash
# Navigate to project directory
cd ~/sunny-ai-meeting-intelligence

# Check current status
git status

# Pull latest changes from GitHub
git pull origin main
```

**Expected Output:**
```
remote: Enumerating objects: 10, done.
remote: Counting objects: 100% (10/10), done.
remote: Compressing objects: 100% (5/5), done.
remote: Total 6 (delta 3), reused 0 (delta 0)
Unpacking objects: 100% (6/6), done.
From https://github.com/Sanhith30/sunny-ai-meeting-intelligence
   abc1234..def5678  main       -> origin/main
Updating abc1234..def5678
Fast-forward
 web/app.py                | 25 +++++++++++++++++++++++++
 web/templates/index.html  | 15 ++++++++++++---
 2 files changed, 37 insertions(+), 3 deletions(-)
```

---

### Step 7: Rebuild and Deploy

#### Method 1: Using Docker Compose (Recommended)

```bash
# Stop current container
sudo docker-compose -f docker-compose.ec2.yml down

# Rebuild with latest code
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# This will:
# 1. Stop the old container
# 2. Build new image with your changes
# 3. Start new container
# 4. Takes 2-3 minutes
```

#### Method 2: Using Docker Run (Alternative)

```bash
# Stop and remove old container
sudo docker stop sunny-ai
sudo docker rm sunny-ai

# Rebuild image
sudo docker build -f Dockerfile.minimal -t sunny-ai:latest .

# Run new container
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
  sunny-ai:latest
```

---

### Step 8: Verify Deployment

```bash
# Check if container is running
sudo docker ps

# Expected output:
# CONTAINER ID   IMAGE              STATUS          PORTS                    NAMES
# abc123def456   sunny-ai:latest    Up 10 seconds   0.0.0.0:8000->8000/tcp   sunny-ai
```

```bash
# Check logs for errors
sudo docker logs sunny-ai --tail 30

# Expected output (last few lines):
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

```bash
# Test health check
curl http://localhost:8000/api/health

# Expected output:
# {"status":"healthy","service":"Sunny AI",...}
```

---

### Step 9: Test in Browser

1. **Open browser**: `http://13.126.247.12`
2. **Test your new features**
3. **Verify everything works**

✅ **Deployment Complete!**

---

## 🔙 Rollback if Needed

### If Something Goes Wrong

#### Quick Rollback to Previous Version

```bash
# On EC2, check git history
git log --oneline -5

# Output shows recent commits:
# def5678 (HEAD -> main) Add new feature
# abc1234 Previous working version
# xyz9876 Another commit

# Rollback to previous commit
git checkout abc1234

# Rebuild with old code
sudo docker-compose -f docker-compose.ec2.yml down
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# Test if it works
curl http://localhost:8000/api/health
```

#### Return to Latest Version

```bash
# Go back to latest
git checkout main
git pull origin main

# Rebuild
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

---

## 📝 Complete Deployment Checklist

### Before Deployment

- [ ] Test changes locally
- [ ] Commit with clear message
- [ ] Push to GitHub
- [ ] Verify push succeeded

### During Deployment

- [ ] Connect to EC2
- [ ] Navigate to project directory
- [ ] Pull latest code
- [ ] Stop old container
- [ ] Rebuild with new code
- [ ] Start new container

### After Deployment

- [ ] Check container is running
- [ ] Check logs for errors
- [ ] Test health check endpoint
- [ ] Test in browser
- [ ] Test new features
- [ ] Monitor for 5-10 minutes

---

## 🎯 Common Scenarios

### Scenario 1: Adding a New Python Package

**Local:**
```bash
# Add package to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Test locally
pip install new-package

# Commit and push
git add requirements.txt
git commit -m "Add new-package dependency"
git push origin main
```

**EC2:**
```bash
# Pull and rebuild
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

---

### Scenario 2: Updating UI/Frontend

**Local:**
```bash
# Edit web/templates/index.html
# Make your changes

# Test locally
python -m web.app

# Commit and push
git add web/templates/index.html
git commit -m "Update: Improve homepage design"
git push origin main
```

**EC2:**
```bash
# Pull and rebuild
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

---

### Scenario 3: Updating Configuration

**Local:**
```bash
# Edit config.yaml
# Change settings

# Commit and push
git add config.yaml
git commit -m "Update: Change default meeting duration"
git push origin main
```

**EC2:**
```bash
# Pull and restart (no rebuild needed for config)
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker restart sunny-ai
```

---

### Scenario 4: Adding New API Endpoint

**Local:**
```bash
# Edit web/app.py
# Add new endpoint

@app.get("/api/new-feature")
async def new_feature():
    return {"status": "success"}

# Test locally
python -m web.app
curl http://localhost:8000/api/new-feature

# Commit and push
git add web/app.py
git commit -m "Feature: Add new API endpoint"
git push origin main
```

**EC2:**
```bash
# Pull and rebuild
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# Test new endpoint
curl http://localhost:8000/api/new-feature
```

---

## 🚨 Troubleshooting

### Problem 1: Git Pull Shows Conflicts

```bash
# Stash your local changes
git stash

# Pull latest
git pull origin main

# Reapply your changes (if needed)
git stash pop
```

### Problem 2: Docker Build Fails

```bash
# Check logs
sudo docker logs sunny-ai

# Clean up and rebuild
sudo docker system prune -a
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

### Problem 3: Container Keeps Restarting

```bash
# Check logs
sudo docker logs sunny-ai --tail 50

# Common issues:
# - Syntax error in Python code
# - Missing dependency
# - Port already in use
# - Configuration error
```

### Problem 4: Changes Not Showing

```bash
# Make sure you pulled latest code
git pull origin main

# Make sure you rebuilt the container
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# Clear browser cache
# Ctrl+Shift+R (hard refresh)
```

---

## 📊 Monitoring After Deployment

### Check Container Health

```bash
# Is it running?
sudo docker ps

# View logs in real-time
sudo docker logs sunny-ai -f

# Check resource usage
sudo docker stats sunny-ai
```

### Check Application Health

```bash
# Health check
curl http://localhost:8000/api/health

# Check specific endpoint
curl http://localhost:8000/api/your-new-endpoint
```

### Check Nginx

```bash
# Nginx status
sudo systemctl status nginx

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 🎓 Best Practices

### 1. Always Test Locally First

```bash
# Test before pushing
python -m web.app
# or
docker build -f Dockerfile.minimal -t sunny-ai:test .
docker run -p 8000:8000 sunny-ai:test
```

### 2. Use Descriptive Commit Messages

```bash
# Good commit messages:
git commit -m "Feature: Add real-time transcription"
git commit -m "Fix: Email sending timeout issue"
git commit -m "Update: Improve error handling"
git commit -m "Docs: Update API documentation"

# Bad commit messages:
git commit -m "update"
git commit -m "fix bug"
git commit -m "changes"
```

### 3. Deploy During Low Traffic

- Deploy during off-hours
- Notify users of maintenance
- Have rollback plan ready

### 4. Keep Backups

```bash
# Backup data before major updates
cd ~/sunny-ai-meeting-intelligence
tar -czf backup-$(date +%Y%m%d).tar.gz outputs/ data/ logs/
```

### 5. Monitor After Deployment

- Watch logs for 10-15 minutes
- Test all major features
- Check error rates
- Monitor resource usage

### 6. Document Your Changes

```bash
# Update CHANGELOG.md
echo "## [1.1.0] - 2026-01-11" >> CHANGELOG.md
echo "### Added" >> CHANGELOG.md
echo "- New feature description" >> CHANGELOG.md

git add CHANGELOG.md
git commit -m "Docs: Update changelog"
```

---

## 🔄 Automated Deployment (Advanced)

### Create Deployment Script

```bash
# On EC2, create script
nano ~/deploy-sunny-ai.sh
```

**Add this content:**
```bash
#!/bin/bash

echo "🚀 Starting Sunny AI Deployment..."

# Navigate to project
cd ~/sunny-ai-meeting-intelligence

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Stop old container
echo "🛑 Stopping old container..."
sudo docker-compose -f docker-compose.ec2.yml down

# Rebuild and start
echo "🔨 Building new container..."
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# Wait for startup
echo "⏳ Waiting for startup..."
sleep 10

# Check status
echo "✅ Checking status..."
sudo docker ps | grep sunny-ai

# Test health
echo "🏥 Testing health..."
curl http://localhost:8000/api/health

echo "🎉 Deployment complete!"
```

**Make executable:**
```bash
chmod +x ~/deploy-sunny-ai.sh
```

**Use it:**
```bash
# Deploy with one command
~/deploy-sunny-ai.sh
```

---

## 📞 Quick Reference Commands

### Local Development
```bash
# Test locally
python -m web.app

# Build Docker locally
docker build -f Dockerfile.minimal -t sunny-ai:test .

# Run Docker locally
docker run -p 8000:8000 sunny-ai:test

# Commit changes
git add .
git commit -m "Your message"
git push origin main
```

### EC2 Deployment
```bash
# Connect
ssh -i key.pem ubuntu@13.126.247.12

# Deploy
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml down
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# Verify
sudo docker ps
sudo docker logs sunny-ai
curl http://localhost:8000/api/health
```

### Rollback
```bash
# Rollback to previous version
git log --oneline -5
git checkout <previous-commit-hash>
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

---

## 🎉 Summary

**Complete Workflow:**

1. **Develop** → Make changes locally
2. **Test** → Test on your machine
3. **Commit** → Save changes with git
4. **Push** → Upload to GitHub
5. **Deploy** → Pull and rebuild on EC2
6. **Verify** → Test in production
7. **Monitor** → Watch for issues

**Time Required:**
- Small changes: 5-10 minutes
- Major features: 15-30 minutes
- First time: 30-60 minutes

---

## 📚 Additional Resources

- **Git Guide**: https://git-scm.com/docs
- **Docker Guide**: https://docs.docker.com/
- **AWS EC2 Guide**: https://docs.aws.amazon.com/ec2/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

---

**Need Help?**
- Check logs: `sudo docker logs sunny-ai`
- GitHub Issues: https://github.com/Sanhith30/sunny-ai-meeting-intelligence/issues
- AWS Support: https://aws.amazon.com/support/

---

**Made with ☀️ by the Sunny AI team**

*Happy deploying!* 🚀
