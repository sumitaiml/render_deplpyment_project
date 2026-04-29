#!/bin/bash
# HR Tech Platform - Quick Deployment Script
# Supports: Local Docker, Azure, AWS, and Manual deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HR Tech Platform - Deployment Helper${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Menu
show_menu() {
    echo -e "${YELLOW}Select Deployment Option:${NC}"
    echo "1) Local Docker Compose (Easiest - 5 min)"
    echo "2) Azure Container Instances"
    echo "3) Azure App Service"
    echo "4) AWS EC2 with Docker"
    echo "5) AWS ECS Fargate"
    echo "6) Manual Linux/Ubuntu Server"
    echo "7) View Deployment Guide"
    echo "8) Exit"
    echo ""
    read -p "Enter choice [1-8]: " choice
}

# Local Docker Compose
deploy_local_docker() {
    echo -e "${YELLOW}Starting Local Docker Deployment...${NC}"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"
    
    # Create .env if not exists
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Creating .env file...${NC}"
        cat > .env << 'EOF'
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=hrtech_secure_pass_2024
POSTGRES_DB=hrtech_db
DATABASE_URL=postgresql://postgres:hrtech_secure_pass_2024@postgres:5432/hrtech_db

# Redis
REDIS_URL=redis://redis:6379/0

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# ML Models
SPACY_MODEL=en_core_web_sm
SBERT_MODEL=all-MiniLM-L6-v2

# Environment
ENVIRONMENT=production
DEBUG=false
EOF
        echo -e "${GREEN}✓ .env file created${NC}"
    else
        echo -e "${YELLOW}.env file already exists${NC}"
    fi
    
    # Start services
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker-compose build --no-cache
    
    echo -e "${YELLOW}Starting services...${NC}"
    docker-compose up -d
    
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 30
    
    echo -e "${YELLOW}Checking service status...${NC}"
    docker-compose ps
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Access the application:${NC}"
    echo -e "  Frontend: ${GREEN}http://localhost:5000${NC}"
    echo -e "  API Docs: ${GREEN}http://localhost:5000/docs${NC}"
    echo -e "  Backend:  ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo "  View logs:        docker-compose logs -f"
    echo "  Stop services:    docker-compose stop"
    echo "  Start services:   docker-compose start"
    echo "  Restart services: docker-compose restart"
    echo "  Remove all:       docker-compose down -v"
    echo ""
}

# Azure Container Instances
deploy_azure_aci() {
    echo -e "${YELLOW}Azure Container Instances Deployment${NC}"
    
    if ! command -v az &> /dev/null; then
        echo -e "${RED}Azure CLI is not installed. Install from https://docs.microsoft.com/cli/azure${NC}"
        exit 1
    fi
    
    # Get Azure details
    read -p "Enter Resource Group name (default: hrtech-rg): " rg_name
    rg_name=${rg_name:-hrtech-rg}
    
    read -p "Enter Registry name (default: hrtechregistry): " registry_name
    registry_name=${registry_name:-hrtechregistry}
    
    read -p "Enter Location (default: eastus): " location
    location=${location:-eastus}
    
    echo -e "${YELLOW}Logging into Azure...${NC}"
    az login
    
    echo -e "${YELLOW}Creating resource group: $rg_name${NC}"
    az group create --name "$rg_name" --location "$location"
    
    echo -e "${YELLOW}Creating container registry: $registry_name${NC}"
    az acr create --resource-group "$rg_name" --name "$registry_name" --sku Basic
    
    echo -e "${YELLOW}Building and pushing Docker image...${NC}"
    az acr build --registry "$registry_name" --image hrtech-backend:1.0 ./backend
    
    echo -e "${GREEN}✓ Azure deployment setup complete!${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Create PostgreSQL database in Azure portal"
    echo "  2. Create Azure Container Group with the image"
    echo "  3. Configure environment variables in container"
    echo ""
}

# Manual Linux Deployment
deploy_manual_linux() {
    echo -e "${YELLOW}Manual Linux/Ubuntu Deployment Guide${NC}"
    echo ""
    echo "Copy and paste these commands on your Linux server:"
    echo ""
    cat << 'EOF'
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip python3-venv git postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx -y

# Clone repository
git clone https://github.com/sumitaiml/-AI-Powered-Resume-Job-Matching-Hiring-Intelligence-System.git
cd hrtech-platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install gunicorn

# Setup database
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE DATABASE hrtech_db;"
sudo -u postgres psql -c "CREATE USER hrtech_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hrtech_db TO hrtech_user;"

# Create .env file
cat > .env << 'ENVEOF'
DATABASE_URL=postgresql://hrtech_user:secure_password@localhost/hrtech_db
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=production
ENVEOF

# Start Redis
sudo systemctl start redis-server

# Start backend
gunicorn -w 4 -b 0.0.0.0:8000 backend.app.main:app &

# Start Flask gateway
python flask_gateway.py &

# Access at http://your-server-ip:5000
EOF
    echo ""
}

# View deployment guide
view_guide() {
    if command -v less &> /dev/null; then
        less DEPLOYMENT_GUIDE.md
    else
        cat DEPLOYMENT_GUIDE.md
    fi
}

# Main loop
while true; do
    show_menu
    
    case $choice in
        1)
            deploy_local_docker
            ;;
        2)
            echo -e "${YELLOW}Azure ACI deployment selected${NC}"
            echo "See DEPLOYMENT_GUIDE.md for detailed steps"
            deploy_azure_aci
            ;;
        3)
            echo -e "${YELLOW}Azure App Service deployment selected${NC}"
            echo "See DEPLOYMENT_GUIDE.md for detailed steps"
            ;;
        4)
            echo -e "${YELLOW}AWS EC2 deployment selected${NC}"
            echo "See DEPLOYMENT_GUIDE.md for detailed steps"
            ;;
        5)
            echo -e "${YELLOW}AWS ECS Fargate deployment selected${NC}"
            echo "See DEPLOYMENT_GUIDE.md for detailed steps"
            ;;
        6)
            deploy_manual_linux
            ;;
        7)
            view_guide
            ;;
        8)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
