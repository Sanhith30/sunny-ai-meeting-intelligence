#!/bin/bash
# Sunny AI Production Deployment Script

set -e

echo "🌞 Sunny AI Deployment Script"
echo "=============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: Some commands may require sudo${NC}"
fi

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo ""
echo "Step 1: Checking prerequisites..."

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

# Check pip
if command_exists pip3; then
    echo -e "${GREEN}✓ pip installed${NC}"
else
    echo -e "${RED}✗ pip not found${NC}"
    exit 1
fi

echo ""
echo "Step 2: Setting up virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}→ Virtual environment already exists${NC}"
fi

source venv/bin/activate

echo ""
echo "Step 3: Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo "Step 4: Installing Playwright browsers..."
playwright install chromium
echo -e "${GREEN}✓ Playwright browsers installed${NC}"

echo ""
echo "Step 5: Creating directories..."
mkdir -p data outputs logs temp
echo -e "${GREEN}✓ Directories created${NC}"

echo ""
echo "Step 6: Checking environment variables..."

if [ -f ".env" ]; then
    source .env
    if [ -n "$GEMINI_API_KEY" ]; then
        echo -e "${GREEN}✓ GEMINI_API_KEY configured${NC}"
    else
        echo -e "${YELLOW}⚠ GEMINI_API_KEY not set in .env${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env file not found. Copy .env.example to .env and configure${NC}"
    cp .env.example .env 2>/dev/null || true
fi

echo ""
echo "=============================="
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "To start Sunny AI:"
echo "  source venv/bin/activate"
echo "  python -m web.app"
echo ""
echo "Or with Docker:"
echo "  docker-compose up -d"
echo ""
