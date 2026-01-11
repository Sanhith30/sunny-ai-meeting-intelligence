#!/bin/bash
# Sunny AI - EC2 Automated Setup Script
# Run this on your EC2 instance after connecting via SSH

set -e  # Exit on error

echo "=========================================="
echo "  Sunny AI - EC2 Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    echo -e "${RED}Please run this script as ubuntu user${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl wget vim htop

echo -e "${GREEN}Step 2: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    sudo systemctl start docker
    sudo systemctl enable docker
    echo -e "${YELLOW}Docker installed. You may need to log out and back in.${NC}"
else
    echo "Docker already installed"
fi

echo -e "${GREEN}Step 3: Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

echo -e "${GREEN}Step 4: Installing Nginx...${NC}"
if ! command -v nginx &> /dev/null; then
    sudo apt install -y nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
else
    echo "Nginx already installed"
fi

echo -e "${GREEN}Step 5: Cloning repository...${NC}"
cd ~
if [ ! -d "sunny-ai-meeting-intelligence" ]; then
    git clone https://github.com/Sanhith30/sunny-ai-meeting-intelligence.git
    cd sunny-ai-meeting-intelligence
else
    echo "Repository already exists, pulling latest changes..."
    cd sunny-ai-meeting-intelligence
    git pull origin main
fi

echo -e "${GREEN}Step 6: Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Sunny AI Environment Configuration
# Edit these values with your actual credentials

# Required - Get from https://aistudio.google.com/apikey
GEMINI_API_KEY=your-gemini-api-key-here

# Optional - For email notifications
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password-here

# Optional - For speaker diarization
HF_TOKEN=your-huggingface-token-here

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
EOF
    echo -e "${YELLOW}Please edit .env file with your API keys:${NC}"
    echo "  nano .env"
else
    echo ".env file already exists"
fi

echo -e "${GREEN}Step 7: Creating directories...${NC}"
mkdir -p outputs data logs backups

echo -e "${GREEN}Step 8: Setting up Nginx configuration...${NC}"
INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
sudo tee /etc/nginx/sites-available/sunny-ai > /dev/null << EOF
server {
    listen 80;
    server_name $INSTANCE_IP;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/sunny-ai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo -e "${GREEN}Step 9: Setting up firewall...${NC}"
if ! sudo ufw status | grep -q "Status: active"; then
    sudo ufw allow 22
    sudo ufw allow 80
    sudo ufw allow 443
    sudo ufw --force enable
else
    echo "Firewall already configured"
fi

echo -e "${GREEN}Step 10: Creating backup script...${NC}"
cat > ~/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

tar -czf $BACKUP_DIR/sunny-ai-data-$DATE.tar.gz \
  /home/ubuntu/sunny-ai-meeting-intelligence/data \
  /home/ubuntu/sunny-ai-meeting-intelligence/outputs

find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x ~/backup.sh

# Add to crontab if not already there
(crontab -l 2>/dev/null | grep -q backup.sh) || (crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup.sh >> /home/ubuntu/backup.log 2>&1") | crontab -

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit environment variables:"
echo "   nano .env"
echo ""
echo "2. Build and start the application:"
echo "   docker-compose up -d"
echo ""
echo "3. Check logs:"
echo "   docker-compose logs -f"
echo ""
echo "4. Access your application:"
echo "   http://$INSTANCE_IP"
echo ""
echo "5. Check health:"
echo "   curl http://localhost:8000/api/health"
echo ""
echo "For SSL setup with domain, see AWS_EC2_DEPLOYMENT.md"
echo ""
echo -e "${YELLOW}Note: You may need to log out and back in for Docker permissions.${NC}"
echo ""
