# ⚡ Deployment Quick Reference

**One-page cheat sheet for deploying updates to EC2**

---

## 🔄 Standard Update Flow

### On Your Windows Machine

```bash
# 1. Make your changes
# Edit files in VS Code or your editor

# 2. Test locally (optional but recommended)
python -m web.app
# Open: http://localhost:8000

# 3. Commit and push
git add .
git commit -m "Feature: Describe your changes"
git push origin main
```

### On Your EC2 Instance

```bash
# 1. Connect via PuTTY
# Host: ubuntu@13.126.247.12

# 2. Deploy (copy all these commands)
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml down
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# 3. Verify
sudo docker ps
sudo docker logs sunny-ai --tail 20
```

### Test in Browser

```
http://13.126.247.12
```

**Done!** ✅

---

## 📋 Common Commands

### Local Development

```bash
# Test locally
python -m web.app

# Commit changes
git add .
git commit -m "Your message"
git push origin main
```

### EC2 Deployment

```bash
# Quick deploy
cd ~/sunny-ai-meeting-intelligence && \
git pull origin main && \
sudo docker-compose -f docker-compose.ec2.yml down && \
sudo docker-compose -f docker-compose.ec2.yml up -d --build

# Check status
sudo docker ps
sudo docker logs sunny-ai

# Restart only (no rebuild)
sudo docker restart sunny-ai
```

### Troubleshooting

```bash
# View logs
sudo docker logs sunny-ai --tail 50

# Check if running
sudo docker ps

# Restart Nginx
sudo systemctl restart nginx

# Clean rebuild
sudo docker system prune -a
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

---

## 🎯 Deployment Scenarios

### Scenario 1: Small Code Change

```bash
# Local
git add .
git commit -m "Fix: Bug description"
git push origin main

# EC2
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker restart sunny-ai
```

### Scenario 2: New Feature

```bash
# Local
git add .
git commit -m "Feature: New feature name"
git push origin main

# EC2
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml down
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

### Scenario 3: New Dependency

```bash
# Local
# Add to requirements.txt
git add requirements.txt
git commit -m "Add: New package"
git push origin main

# EC2
cd ~/sunny-ai-meeting-intelligence
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

---

## 🚨 Emergency Rollback

```bash
# On EC2
cd ~/sunny-ai-meeting-intelligence
git log --oneline -5
git checkout <previous-commit-hash>
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

---

## ✅ Verification Checklist

After deployment:

- [ ] `sudo docker ps` shows container running
- [ ] `sudo docker logs sunny-ai` shows no errors
- [ ] `curl http://localhost:8000/api/health` returns healthy
- [ ] Browser test: `http://13.126.247.12` works
- [ ] Test your new feature

---

## 📞 Quick Help

**Container not running?**
```bash
sudo docker logs sunny-ai
sudo docker restart sunny-ai
```

**Changes not showing?**
```bash
git pull origin main
sudo docker-compose -f docker-compose.ec2.yml up -d --build
# Hard refresh browser: Ctrl+Shift+R
```

**Port issues?**
```bash
sudo netstat -tulpn | grep 8000
sudo systemctl status nginx
```

---

## 🔗 Full Guides

- **Detailed Guide**: [FEATURE_UPDATE_DEPLOYMENT_GUIDE.md](FEATURE_UPDATE_DEPLOYMENT_GUIDE.md)
- **EC2 Setup**: [AWS_EC2_DEPLOYMENT.md](AWS_EC2_DEPLOYMENT.md)
- **Update Guide**: [EC2_UPDATE_GUIDE.md](EC2_UPDATE_GUIDE.md)

---

**Save this page for quick reference!** 📌
