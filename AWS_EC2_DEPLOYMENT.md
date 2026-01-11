# 🚀 AWS EC2 Deployment Guide - Sunny AI

Complete step-by-step guide to deploy Sunny AI on Amazon EC2.

---

## 🔑 Important: User API Keys Required

**Sunny AI is free and open-source.** Each user who accesses your deployment will need their own **free** Gemini API key:

- ✅ **No cost to you** - Users provide their own keys
- ✅ **Better privacy** - Each user's data goes directly to Google
- ✅ **No rate limits** - Each user has their own quota
- ✅ **Fair usage** - Sustainable for everyone

**How it works:**
1. You deploy Sunny AI on EC2
2. Users visit your URL
3. They enter their own API key (takes 1 minute to get)
4. They can use all features for free

📖 **Share this with your users**: [API_KEY_GUIDE.md](API_KEY_GUIDE.md)

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [EC2 Instance Setup](#ec2-instance-setup)
3. [Server Configuration](#server-configuration)
4. [Application Deployment](#application-deployment)
5. [Domain & SSL Setup](#domain--ssl-setup)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You'll Need:

- ✅ AWS Account ([Sign up here](https://aws.amazon.com/))
- ✅ Credit card for AWS (Free tier available)
- ✅ SSH client (Terminal on Mac/Linux, PuTTY on Windows)
- ✅ Domain name (optional, for custom URL)

### 🔑 About API Keys:

**You DON'T need to configure API keys on the server!**

- ❌ No need to set `GEMINI_API_KEY` in `.env`
- ❌ No need to configure Gmail credentials
- ✅ Users will provide their own API keys when they use the app
- ✅ This keeps your deployment free and sustainable

**Optional**: If you want to provide a shared API key for your team, you can still configure it in `.env`, but it's not required.

### Cost Estimate:

| Instance Type | vCPU | RAM | Storage | Cost/Month |
|--------------|------|-----|---------|------------|
| **t2.micro** (Free tier) | 1 | 1 GB | 30 GB | $0 (12 months) |
| **t3.small** (Recommended) | 2 | 2 GB | 30 GB | ~$15 |
| **t3.medium** (Full features) | 2 | 4 GB | 30 GB | ~$30 |

> **Recommendation**: Start with t3.small for core features, upgrade to t3.medium for advanced features.

---

## EC2 Instance Setup

### Step 1: Launch EC2 Instance

1. **Log in to AWS Console**
   - Go to [AWS Console](https://console.aws.amazon.com/)
   - Navigate to EC2 Dashboard

2. **Click "Launch Instance"**

3. **Configure Instance:**

   **Name and Tags:**
   ```
   Name: sunny-ai-server
   ```

   **Application and OS Images (AMI):**
   - Select: **Ubuntu Server 22.04 LTS**
   - Architecture: **64-bit (x86)**

   **Instance Type:**
   - For testing: `t2.micro` (Free tier)
   - For production: `t3.small` or `t3.medium`

   **Key Pair (login):**
   - Click "Create new key pair"
   - Name: `sunny-ai-key`
   - Type: RSA
   - Format: `.pem` (Mac/Linux) or `.ppk` (Windows/PuTTY)
   - **Download and save securely!**

   **Network Settings:**
   - ✅ Allow SSH traffic from: My IP (or Anywhere for testing)
   - ✅ Allow HTTPS traffic from the internet
   - ✅ Allow HTTP traffic from the internet

   **Configure Storage:**
   - Size: **30 GB** (minimum)
   - Type: **gp3** (faster and cheaper)

4. **Click "Launch Instance"**

5. **Wait for Instance to Start** (2-3 minutes)
   - Status should show "Running"
   - Note your **Public IPv4 address**

### Step 2: Configure Security Group

1. **Go to Security Groups**
   - EC2 Dashboard → Network & Security → Security Groups
   - Select your instance's security group

2. **Edit Inbound Rules**
   - Click "Edit inbound rules"
   - Add these rules:

   | Type | Protocol | Port | Source | Description |
   |------|----------|------|--------|-------------|
   | SSH | TCP | 22 | My IP | SSH access |
   | HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
   | HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web |
   | Custom TCP | TCP | 8000 | 0.0.0.0/0 | App port |

3. **Save rules**

### Step 3: Allocate Elastic IP (Optional but Recommended)

This gives you a permanent IP address:

1. **EC2 Dashboard → Elastic IPs**
2. **Click "Allocate Elastic IP address"**
3. **Click "Allocate"**
4. **Associate with your instance:**
   - Select the Elastic IP
   - Actions → Associate Elastic IP address
   - Select your instance
   - Click "Associate"

---

## Server Configuration

### Step 1: Connect to Your Instance

#### On Mac/Linux:

```bash
# Set permissions for key file
chmod 400 ~/Downloads/sunny-ai-key.pem

# Connect to instance
ssh -i ~/Downloads/sunny-ai-key.pem ubuntu@YOUR_INSTANCE_IP
```

#### On Windows (using PuTTY):

1. Open PuTTY
2. Host Name: `ubuntu@YOUR_INSTANCE_IP`
3. Connection → SSH → Auth → Browse for your `.ppk` file
4. Click "Open"

### Step 2: Update System

```bash
# Update package list
sudo apt update

# Upgrade packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y git curl wget vim htop
```

### Step 3: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version

# Log out and back in for group changes to take effect
exit
# Then reconnect via SSH
```

### Step 4: Install Docker Compose

```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

---

## Application Deployment

### Step 1: Clone Repository

```bash
# Clone your repository
git clone https://github.com/Sanhith30/sunny-ai-meeting-intelligence.git

# Navigate to directory
cd sunny-ai-meeting-intelligence
```

### Step 2: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add your configuration:

```env
# Required
GEMINI_API_KEY=your-gemini-api-key-here

# Email (optional)
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Optional (for advanced features)
HF_TOKEN=your-huggingface-token

# Server settings
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Choose Deployment Method

#### Option A: Docker Deployment (Recommended)

**For Core Features (Lightweight):**

```bash
# Build with minimal Dockerfile
docker build -f Dockerfile.minimal -t sunny-ai:latest .

# Run container
docker run -d \
  --name sunny-ai \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  sunny-ai:latest
```

**For Full Features:**

```bash
# Build with full Dockerfile
docker build -f Dockerfile -t sunny-ai:latest .

# Run container (needs more memory)
docker run -d \
  --name sunny-ai \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  --memory="2g" \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  sunny-ai:latest
```

**Check if running:**

```bash
# View logs
docker logs -f sunny-ai

# Check status
docker ps

# Test health check
curl http://localhost:8000/api/health
```

#### Option B: Docker Compose (Easier Management)

**Create docker-compose.yml:**

```bash
nano docker-compose.yml
```

Add this content:

```yaml
version: '3.8'

services:
  sunny-ai:
    build:
      context: .
      dockerfile: Dockerfile.minimal
    container_name: sunny-ai
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GMAIL_ADDRESS=${GMAIL_ADDRESS}
      - GMAIL_APP_PASSWORD=${GMAIL_APP_PASSWORD}
      - HF_TOKEN=${HF_TOKEN}
      - HOST=0.0.0.0
      - PORT=8000
      - ENVIRONMENT=production
    volumes:
      - ./outputs:/app/outputs
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

**Deploy:**

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

#### Option C: Direct Python Installation (No Docker)

```bash
# Install Python and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y ffmpeg libsndfile1

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-railway.txt

# Install Playwright
playwright install chromium
playwright install-deps

# Run application
nohup python -m uvicorn web.app:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &

# Check if running
ps aux | grep uvicorn
tail -f app.log
```

### Step 4: Set Up Nginx Reverse Proxy

This allows you to use port 80/443 instead of 8000:

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/sunny-ai
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
}
```

**Enable and start Nginx:**

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/sunny-ai /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 5: Test Your Deployment

```bash
# Test locally
curl http://localhost:8000/api/health

# Test via Nginx
curl http://YOUR_INSTANCE_IP/api/health

# Test from browser
# Open: http://YOUR_INSTANCE_IP
```

---

## Domain & SSL Setup

### Step 1: Point Domain to EC2

1. **Go to your domain registrar** (GoDaddy, Namecheap, etc.)
2. **Add A Record:**
   - Type: `A`
   - Name: `@` (or `sunny-ai` for subdomain)
   - Value: `YOUR_ELASTIC_IP`
   - TTL: `3600`

3. **Wait for DNS propagation** (5-30 minutes)

### Step 2: Install SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose redirect HTTP to HTTPS (option 2)

# Test auto-renewal
sudo certbot renew --dry-run
```

Your site is now accessible at: `https://your-domain.com` 🎉

---

## Monitoring & Maintenance

### Set Up Automatic Backups

```bash
# Create backup script
nano ~/backup.sh
```

Add:

```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup data
tar -czf $BACKUP_DIR/sunny-ai-data-$DATE.tar.gz \
  /home/ubuntu/sunny-ai-meeting-intelligence/data \
  /home/ubuntu/sunny-ai-meeting-intelligence/outputs

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and schedule:

```bash
chmod +x ~/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /home/ubuntu/backup.sh >> /home/ubuntu/backup.log 2>&1
```

### Monitor Application

```bash
# View Docker logs
docker logs -f sunny-ai

# View application logs
tail -f logs/sunny_ai.log

# Check resource usage
htop

# Check disk space
df -h

# Check memory
free -h
```

### Set Up CloudWatch (Optional)

1. **Install CloudWatch agent:**

```bash
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

2. **Configure monitoring in AWS Console**

### Update Application

```bash
# Pull latest changes
cd ~/sunny-ai-meeting-intelligence
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Or with Docker:
docker stop sunny-ai
docker rm sunny-ai
docker build -f Dockerfile.minimal -t sunny-ai:latest .
docker run -d --name sunny-ai --restart unless-stopped -p 8000:8000 --env-file .env sunny-ai:latest
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check Docker logs
docker logs sunny-ai

# Check if port is in use
sudo netstat -tulpn | grep 8000

# Check environment variables
docker exec sunny-ai env | grep GEMINI
```

### Can't Access from Browser

```bash
# Check if app is running
curl http://localhost:8000/api/health

# Check Nginx status
sudo systemctl status nginx

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Check security group rules in AWS Console
```

### Out of Memory

```bash
# Check memory usage
free -h

# Restart application
docker-compose restart

# Upgrade instance type in AWS Console
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Test Nginx configuration
sudo nginx -t
```

### Docker Issues

```bash
# Restart Docker
sudo systemctl restart docker

# Clean up Docker
docker system prune -a

# Check Docker logs
sudo journalctl -u docker
```

---

## Performance Optimization

### 1. Enable Swap (for low memory instances)

```bash
# Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2. Configure Nginx Caching

Add to Nginx config:

```nginx
# Cache static files
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. Set Up Log Rotation

```bash
sudo nano /etc/logrotate.d/sunny-ai
```

Add:

```
/home/ubuntu/sunny-ai-meeting-intelligence/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## Security Best Practices

### 1. Configure Firewall

```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH, HTTP, HTTPS
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 2. Disable Root Login

```bash
sudo nano /etc/ssh/sshd_config
```

Change:
```
PermitRootLogin no
PasswordAuthentication no
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### 3. Set Up Fail2Ban

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Start service
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

---

## Cost Optimization

### 1. Use Reserved Instances
- Save up to 72% with 1-year commitment
- Good for production deployments

### 2. Use Spot Instances
- Save up to 90% for non-critical workloads
- Good for development/testing

### 3. Stop Instance When Not in Use
```bash
# Stop instance (keeps data)
aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# Start instance
aws ec2 start-instances --instance-ids i-1234567890abcdef0
```

### 4. Use S3 for Storage
- Store outputs/recordings in S3
- Cheaper than EBS for large files

---

## Quick Reference Commands

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# View logs
docker-compose logs -f

# Restart application
docker-compose restart

# Update application
git pull && docker-compose up -d --build

# Check health
curl http://localhost:8000/api/health

# SSH to instance
ssh -i sunny-ai-key.pem ubuntu@YOUR_IP

# Backup data
tar -czf backup.tar.gz data outputs

# Check disk space
df -h

# Check memory
free -h

# Monitor processes
htop
```

---

## Support & Resources

- **AWS Documentation**: https://docs.aws.amazon.com/ec2/
- **Docker Documentation**: https://docs.docker.com/
- **Nginx Documentation**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/
- **GitHub Issues**: https://github.com/Sanhith30/sunny-ai-meeting-intelligence/issues

---

## Conclusion

You now have Sunny AI running on AWS EC2! 🎉

**Your deployment includes:**
- ✅ Secure HTTPS access
- ✅ Automatic restarts
- ✅ Nginx reverse proxy
- ✅ SSL certificate
- ✅ Monitoring and logs
- ✅ Automatic backups

**Next steps:**
1. Test meeting functionality
2. Set up monitoring alerts
3. Configure automatic backups to S3
4. Optimize for your use case

**Need help?** Open an issue on GitHub or check the troubleshooting section above.

---

**Happy deploying! 🚀**
