# ⚡ Quick Update Commands - EC2

Copy and paste these commands to update your EC2 deployment in 2 minutes!

---

## 🚀 Full Update (Copy All at Once)

```bash
# Connect to EC2 (use PuTTY on Windows or this command on Mac/Linux)
ssh -i your-key.pem ubuntu@13.126.247.12

# Navigate to project
cd ~/sunny-ai-meeting-intelligence

# Pull latest code
git pull origin main

# Stop current container
sudo docker-compose -f docker-compose.ec2.yml down

# Rebuild with latest code
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# Check if running
sudo docker ps

# View logs
sudo docker logs sunny-ai --tail 20

# Test health check
curl http://localhost:8000/api/health
```

---

## 📋 Step-by-Step Commands

### 1. Connect to EC2
```bash
ssh -i your-key.pem ubuntu@13.126.247.12
```

### 2. Go to Project
```bash
cd ~/sunny-ai-meeting-intelligence
```

### 3. Pull Latest Code
```bash
git pull origin main
```

### 4. Rebuild Container
```bash
sudo docker-compose -f docker-compose.ec2.yml down
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

### 5. Verify
```bash
sudo docker ps
sudo docker logs sunny-ai
curl http://localhost:8000/api/health
```

---

## ✅ Expected Results

### After `git pull`:
```
Updating f8f921d..4700034
Fast-forward
 10 files changed, 903 insertions(+), 116 deletions(-)
```

### After `docker ps`:
```
CONTAINER ID   IMAGE              STATUS          PORTS                    NAMES
abc123def456   sunny-ai:latest    Up 10 seconds   0.0.0.0:8000->8000/tcp   sunny-ai
```

### After `curl health check`:
```json
{
  "status": "healthy",
  "gemini_configured": false,
  "llm_available": false
}
```
**Note**: `gemini_configured: false` is CORRECT! Users will provide their own keys.

---

## 🌐 Test in Browser

Open: **http://13.126.247.12:8000**

You should see:
- ✅ Sunny AI homepage
- ✅ API key modal appears
- ✅ "Get Free API Key from Google" link

---

## 🔧 Troubleshooting Commands

### Container not running?
```bash
sudo docker-compose -f docker-compose.ec2.yml restart
```

### See errors in logs?
```bash
sudo docker logs sunny-ai --tail 50
```

### Clean rebuild?
```bash
sudo docker system prune -a
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

### Check disk space?
```bash
df -h
```

---

## 📤 Share with Users

**Your URL**: `http://13.126.247.12:8000`

**Message to send**:
```
🌟 Try Sunny AI - Free Meeting Assistant!

Visit: http://13.126.247.12:8000

You'll need a free API key (takes 1 minute):
1. Go to: https://aistudio.google.com/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy and paste in Sunny AI

Enjoy! ☀️
```

---

## 🎯 Done!

Your EC2 is now updated with user API key feature!

**Full guide**: [EC2_UPDATE_GUIDE.md](EC2_UPDATE_GUIDE.md)
