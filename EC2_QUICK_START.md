# EC2 Quick Start - Copy & Paste Commands

## Initial Setup (First Time Only)

```bash
# Connect to EC2
ssh -i your-key.pem ubuntu@13.126.247.12

# Clone repository
cd ~
git clone https://github.com/YOUR_USERNAME/sunny-ai-meeting-intelligence.git
cd sunny-ai-meeting-intelligence

# Install Docker (if not installed)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Install Nginx (if not installed)
sudo apt-get install -y nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/sunny-ai
```

Paste this Nginx config:
```nginx
server {
    listen 80;
    server_name _;

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
    }
}
```

```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/sunny-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Deploy Application

```bash
# Make sure you're in the project directory
cd ~/sunny-ai-meeting-intelligence

# Pull latest code
git pull origin main

# Build Docker image
sudo docker build -f Dockerfile.minimal -t sunny-ai-meeting-intelligence-sunny-ai .

# Run container
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
  sunny-ai-meeting-intelligence-sunny-ai

# Check status
sudo docker ps
sudo docker logs sunny-ai --tail 30
```

## Update Application (When You Have New Code)

```bash
# Connect to EC2
ssh -i your-key.pem ubuntu@13.126.247.12
cd ~/sunny-ai-meeting-intelligence

# Pull latest code
git pull origin main

# Stop and remove old container
sudo docker stop sunny-ai
sudo docker rm sunny-ai

# Rebuild image
sudo docker build -f Dockerfile.minimal -t sunny-ai-meeting-intelligence-sunny-ai .

# Start new container
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
  sunny-ai-meeting-intelligence-sunny-ai

# Verify
sudo docker ps
sudo docker logs sunny-ai --tail 30
```

## Useful Commands

```bash
# View logs (live)
sudo docker logs sunny-ai -f

# View last 50 lines of logs
sudo docker logs sunny-ai --tail 50

# Check container status
sudo docker ps

# Restart container
sudo docker restart sunny-ai

# Stop container
sudo docker stop sunny-ai

# Start container
sudo docker start sunny-ai

# Remove container
sudo docker rm sunny-ai

# Execute command inside container
sudo docker exec -it sunny-ai bash

# Check Nginx status
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Container won't start
```bash
sudo docker logs sunny-ai
```

### "Invalid host header" error
Make sure environment variables are set:
```bash
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
  sunny-ai-meeting-intelligence-sunny-ai
```

### Browser automation errors
Check if Playwright is installed:
```bash
sudo docker exec sunny-ai playwright --version
sudo docker exec sunny-ai ls -la /root/.cache/ms-playwright/
```

### Can't access from browser
1. Check EC2 Security Group allows port 80
2. Check Nginx is running: `sudo systemctl status nginx`
3. Check container is running: `sudo docker ps`
4. Check logs: `sudo docker logs sunny-ai --tail 30`

## Access Your Application

Open browser: `http://13.126.247.12`

## Your EC2 Details

- **Public IP**: 13.126.247.12
- **Private IP**: 172.31.9.60
- **SSH**: `ssh -i your-key.pem ubuntu@13.126.247.12`
- **Project Path**: `/home/ubuntu/sunny-ai-meeting-intelligence`
- **Container Name**: `sunny-ai`
- **Port**: 8000 (internal), 80 (external via Nginx)
