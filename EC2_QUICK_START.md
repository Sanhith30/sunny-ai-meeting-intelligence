# ⚡ EC2 Quick Start - 5 Minutes to Deploy

The fastest way to get Sunny AI running on AWS EC2.

---

## 🚀 Super Quick Deploy (Copy & Paste)

### 1. Launch EC2 Instance

**AWS Console → EC2 → Launch Instance:**
- **AMI**: Ubuntu Server 22.04 LTS
- **Instance Type**: t3.small (or t2.micro for free tier)
- **Key Pair**: Create new and download
- **Security Group**: Allow SSH (22), HTTP (80), HTTPS (443), Custom TCP (8000)
- **Storage**: 30 GB gp3

### 2. Connect to Instance

```bash
# Mac/Linux
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP

# Windows: Use PuTTY with your .ppk file
```

### 3. Run Automated Setup

```bash
# Download and run setup script
curl -fsSL https://raw.githubusercontent.com/Sanhith30/sunny-ai-meeting-intelligence/main/scripts/ec2-setup.sh | bash

# Log out and back in for Docker permissions
exit
# Then reconnect
```

### 4. Configure Environment

```bash
cd ~/sunny-ai-meeting-intelligence

# Edit environment variables
nano .env
```

Add your API keys:
```env
GEMINI_API_KEY=your-gemini-api-key
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

Save: `Ctrl+X`, `Y`, `Enter`

### 5. Deploy Application

```bash
# Build and start
docker-compose -f docker-compose.ec2.yml up -d

# Check logs
docker-compose logs -f

# Wait for "Sunny AI Web Server started"
# Press Ctrl+C to exit logs
```

### 6. Access Your App

Open in browser:
```
http://YOUR_INSTANCE_IP
```

Check health:
```bash
curl http://YOUR_INSTANCE_IP/api/health
```

---

## ✅ That's It!

Your Sunny AI is now running on EC2! 🎉

### What You Have:
- ✅ Sunny AI running on port 8000
- ✅ Nginx reverse proxy on port 80
- ✅ Automatic restarts
- ✅ Daily backups (2 AM)
- ✅ Firewall configured

### Next Steps:

**Add SSL Certificate (Optional):**
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com
```

**Monitor Application:**
```bash
# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart
docker-compose restart
```

**Update Application:**
```bash
cd ~/sunny-ai-meeting-intelligence
git pull origin main
docker-compose -f docker-compose.ec2.yml up -d --build
```

---

## 🔧 Troubleshooting

### Can't Access from Browser?

```bash
# Check if app is running
docker ps

# Check logs
docker logs sunny-ai

# Check Nginx
sudo systemctl status nginx

# Test locally
curl http://localhost:8000/api/health
```

### Application Won't Start?

```bash
# Check environment variables
cat .env

# Rebuild
docker-compose down
docker-compose -f docker-compose.ec2.yml up -d --build

# Check logs for errors
docker-compose logs
```

### Out of Memory?

```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📊 Cost Estimate

| Instance | Monthly Cost | Best For |
|----------|-------------|----------|
| t2.micro | $0 (free tier) | Testing |
| t3.small | ~$15 | Production (core features) |
| t3.medium | ~$30 | Production (all features) |

**Save Money:**
- Stop instance when not in use
- Use Reserved Instances (save 72%)
- Use Spot Instances for dev/test (save 90%)

---

## 🎯 Common Commands

```bash
# Start application
docker-compose -f docker-compose.ec2.yml up -d

# Stop application
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Update
git pull && docker-compose -f docker-compose.ec2.yml up -d --build

# Backup data
tar -czf backup.tar.gz data outputs

# Check disk space
df -h

# Check memory
free -h
```

---

## 📚 Full Documentation

For detailed setup, SSL, monitoring, and more:
- See [AWS_EC2_DEPLOYMENT.md](AWS_EC2_DEPLOYMENT.md)

---

## 🆘 Need Help?

1. Check [AWS_EC2_DEPLOYMENT.md](AWS_EC2_DEPLOYMENT.md) troubleshooting section
2. View application logs: `docker-compose logs`
3. Open GitHub issue with error details

---

**Happy deploying! 🚀**
