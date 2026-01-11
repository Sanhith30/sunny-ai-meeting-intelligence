# 🚀 Sunny AI Production Deployment Guide

This guide covers deploying Sunny AI for real-world production use.

## 📋 Prerequisites

- Domain name (e.g., `sunny-ai.yourdomain.com`)
- Cloud server (4+ vCPU, 8GB+ RAM recommended)
- SSL certificate (Let's Encrypt is free)
- Gemini API key
- Gmail App Password (for email delivery)

---

## Option 1: Docker Deployment (Recommended)

### Step 1: Server Setup

```bash
# SSH into your server
ssh user@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Clone the project
git clone https://github.com/yourusername/sunny-ai.git
cd sunny-ai
```

### Step 2: Configure Environment

```bash
# Create production .env file
cat > .env << 'EOF'
# Production Environment
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
WORKERS=2

# API Keys
GEMINI_API_KEY=your-gemini-api-key
HF_TOKEN=your-huggingface-token

# Email Configuration
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Security
ALLOWED_HOSTS=sunny-ai.yourdomain.com,www.sunny-ai.yourdomain.com
EOF
```

### Step 3: SSL Setup with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot -y

# Get SSL certificate
sudo certbot certonly --standalone -d sunny-ai.yourdomain.com

# Copy certificates
mkdir -p ssl
sudo cp /etc/letsencrypt/live/sunny-ai.yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/sunny-ai.yourdomain.com/privkey.pem ssl/
sudo chown -R $USER:$USER ssl/
```

### Step 4: Update Nginx Config

Edit `nginx.conf` and replace `your-domain.com` with your actual domain.

### Step 5: Deploy

```bash
# Build and start
docker-compose up -d --build

# Check logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Step 6: Auto-renewal for SSL

```bash
# Add to crontab
echo "0 0 1 * * certbot renew --quiet && docker-compose restart nginx" | crontab -
```

---

## Option 2: Direct Server Deployment

### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install system dependencies
sudo apt install ffmpeg libsndfile1 portaudio19-dev nginx certbot -y
```

### Step 2: Setup Application

```bash
# Clone project
cd /home/ubuntu
git clone https://github.com/yourusername/sunny-ai.git
cd sunny-ai

# Run deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Configure environment
cp .env.example .env
nano .env  # Edit with your values
```

### Step 3: Setup Systemd Service

```bash
# Copy service file
sudo cp scripts/sunny-ai.service /etc/systemd/system/

# Edit paths if needed
sudo nano /etc/systemd/system/sunny-ai.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable sunny-ai
sudo systemctl start sunny-ai

# Check status
sudo systemctl status sunny-ai
```

### Step 4: Configure Nginx

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/sunny-ai
```

Add:
```nginx
server {
    listen 80;
    server_name sunny-ai.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sunny-ai.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/sunny-ai.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sunny-ai.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/sunny-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Option 3: Platform-as-a-Service

### Railway.app

1. Connect your GitHub repo to Railway
2. Add environment variables in Railway dashboard
3. Deploy automatically

### Render.com

1. Create new Web Service
2. Connect GitHub repo
3. Set build command: `pip install -r requirements.txt && playwright install chromium`
4. Set start command: `python -m web.app`
5. Add environment variables

### DigitalOcean App Platform

1. Create new App
2. Connect GitHub repo
3. Configure as Python app
4. Add environment variables
5. Deploy

---

## 🔒 Security Checklist

- [ ] SSL/HTTPS enabled
- [ ] Environment variables secured (not in code)
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] API docs disabled in production
- [ ] Firewall configured (only 80, 443 open)
- [ ] Regular security updates

---

## 📊 Monitoring

### Health Check Endpoint

```bash
curl https://sunny-ai.yourdomain.com/api/health
```

### Log Monitoring

```bash
# Docker
docker-compose logs -f sunny-ai

# Systemd
sudo journalctl -u sunny-ai -f
```

### Recommended Tools

- **Uptime**: UptimeRobot, Pingdom
- **Logs**: Papertrail, Logtail
- **Metrics**: Prometheus + Grafana
- **Errors**: Sentry

---

## 🔄 Updates

### Docker

```bash
git pull
docker-compose down
docker-compose up -d --build
```

### Direct

```bash
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart sunny-ai
```

---

## 💰 Cost Estimates

| Service | Monthly Cost |
|---------|-------------|
| DigitalOcean Droplet (4GB) | ~$24 |
| Domain | ~$1 |
| SSL (Let's Encrypt) | Free |
| Gemini API | Free tier available |
| **Total** | **~$25/month** |

---

## 🆘 Troubleshooting

### App won't start
```bash
# Check logs
sudo journalctl -u sunny-ai -n 100

# Check Python path
which python3
```

### SSL issues
```bash
# Renew certificate
sudo certbot renew

# Check certificate
sudo certbot certificates
```

### Memory issues
```bash
# Check memory
free -h

# Increase swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📞 Support

For issues, create a GitHub issue or contact support.
