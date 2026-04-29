# HR Tech Platform - Deployment Guide

Complete step-by-step deployment instructions for multiple environments.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Deployment with Docker Compose](#local-deployment-with-docker-compose)
3. [Cloud Deployment (Azure)](#cloud-deployment-azure)
4. [Cloud Deployment (AWS)](#cloud-deployment-aws)
5. [Manual Server Deployment](#manual-server-deployment)
6. [Production Checklist](#production-checklist)

---

## Prerequisites

### For All Deployments:
- Git installed (`git --version` to verify)
- Project cloned from GitHub: `git clone https://github.com/sumitaiml/-AI-Powered-Resume-Job-Matching-Hiring-Intelligence-System.git`

### For Docker Deployments:
- Docker installed (download from [docker.com](https://www.docker.com/))
- Docker Compose installed (usually included with Docker Desktop)
- Verify: `docker --version` and `docker-compose --version`

### For Azure Deployment:
- Azure CLI installed
- Azure subscription active
- `az --version` to verify

### For AWS Deployment:
- AWS CLI installed
- AWS credentials configured
- AWS account with EC2/ECS permissions

---

## Local Deployment with Docker Compose

### Easiest & Fastest Option - 5 Minutes Setup

#### **Step 1: Navigate to Project Directory**
```bash
cd hrtech-platform
```

#### **Step 2: Create Environment File**
Create `.env` file in the project root:
```bash
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=hrtech_db
DATABASE_URL=postgresql://postgres:secure_password_here@postgres:5432/hrtech_db

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
```

#### **Step 3: Build and Start Services**
```bash
# Start all services in the background
docker-compose up -d

# OR start with logs visible (for troubleshooting)
docker-compose up

# Wait for all services to be healthy (2-3 minutes)
```

#### **Step 4: Verify Deployment**
```bash
# Check all services are running
docker-compose ps

# Access the application
# Frontend: http://localhost:5000
# API Docs: http://localhost:5000/docs
# Backend (direct): http://localhost:8000/docs
```

#### **Step 5: Test the Application**
1. Open `http://localhost:5000` in your browser
2. Upload a test resume
3. Create a test job
4. Run ranking
5. Verify results display correctly

#### **Step 6: View Logs**
```bash
# All services logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis
```

#### **Step 7: Stop Services**
```bash
# Stop but keep data
docker-compose stop

# Stop and remove everything
docker-compose down

# Stop and remove including database volumes
docker-compose down -v
```

---

## Cloud Deployment (Azure)

### Option A: Azure Container Instances (ACI) - Simple & Fast

#### **Step 1: Install Azure CLI**
```bash
# Windows
choco install azure-cli

# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### **Step 2: Login to Azure**
```bash
az login
# Opens browser for authentication
```

#### **Step 3: Create Resource Group**
```bash
az group create \
  --name hrtech-rg \
  --location eastus
```

#### **Step 4: Create Azure Container Registry**
```bash
az acr create \
  --resource-group hrtech-rg \
  --name hrtechregistry \
  --sku Basic
```

#### **Step 5: Build and Push Docker Images**
```bash
# Login to registry
az acr login --name hrtechregistry

# Build backend image
docker build -t hrtechregistry.azurecr.io/hrtech-backend:1.0 ./backend

# Push to registry
docker push hrtechregistry.azurecr.io/hrtech-backend:1.0
```

#### **Step 6: Create PostgreSQL Database**
```bash
az postgres server create \
  --resource-group hrtech-rg \
  --name hrtech-db-server \
  --location eastus \
  --admin-user admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name B_Gen5_1
```

#### **Step 7: Create Azure Container Group**
```bash
az container create \
  --resource-group hrtech-rg \
  --name hrtech-backend \
  --image hrtechregistry.azurecr.io/hrtech-backend:1.0 \
  --environment-variables \
    DATABASE_URL="postgresql://admin:YourSecurePassword123!@hrtech-db-server.postgres.database.azure.com:5432/hrtech_db" \
    FLASK_HOST="0.0.0.0" \
    FLASK_PORT="5000" \
  --ports 5000 8000 \
  --registry-login-server hrtechregistry.azurecr.io \
  --registry-username <username> \
  --registry-password <password>
```

#### **Step 8: Get Public IP**
```bash
az container show \
  --resource-group hrtech-rg \
  --name hrtech-backend \
  --query ipAddress.ip --output tsv

# Access: http://<public-ip>:5000
```

---

### Option B: Azure App Service (Recommended for Production)

#### **Step 1: Create App Service Plan**
```bash
az appservice plan create \
  --name hrtech-plan \
  --resource-group hrtech-rg \
  --sku B1 \
  --is-linux
```

#### **Step 2: Create Web App**
```bash
az webapp create \
  --resource-group hrtech-rg \
  --plan hrtech-plan \
  --name hrtech-app \
  --deployment-container-image-name hrtechregistry.azurecr.io/hrtech-backend:1.0
```

#### **Step 3: Configure Environment Variables**
```bash
az webapp config appsettings set \
  --resource-group hrtech-rg \
  --name hrtech-app \
  --settings \
    DATABASE_URL="postgresql://..." \
    REDIS_URL="redis://..." \
    ENVIRONMENT=production
```

#### **Step 4: Enable Continuous Deployment**
```bash
az webapp deployment container config \
  --name hrtech-app \
  --resource-group hrtech-rg \
  --enable-continuous-deployment
```

---

## Cloud Deployment (AWS)

### Option A: AWS EC2 with Docker

#### **Step 1: Launch EC2 Instance**
```bash
# Using AWS CLI
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups allow-web
```

#### **Step 2: Connect to Instance**
```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

#### **Step 3: Install Docker**
```bash
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo usermod -a -G docker ec2-user
```

#### **Step 4: Install Docker Compose**
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### **Step 5: Clone Repository**
```bash
git clone https://github.com/sumitaiml/-AI-Powered-Resume-Job-Matching-Hiring-Intelligence-System.git
cd hrtech-platform
```

#### **Step 6: Create .env File**
```bash
nano .env
# Paste environment variables (see prerequisites section)
```

#### **Step 7: Start Services**
```bash
docker-compose up -d
```

#### **Step 8: Setup SSL with Let's Encrypt**
```bash
sudo yum install certbot -y
sudo certbot certonly --standalone -d your-domain.com
```

---

### Option B: AWS ECS with Fargate (Serverless)

#### **Step 1: Create ECR Repository**
```bash
aws ecr create-repository --repository-name hrtech-backend
```

#### **Step 2: Build and Push Docker Image**
```bash
docker build -t hrtech-backend .
docker tag hrtech-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/hrtech-backend:latest

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/hrtech-backend:latest
```

#### **Step 3: Create ECS Cluster**
```bash
aws ecs create-cluster --cluster-name hrtech-cluster
```

#### **Step 4: Create Task Definition**
Create `ecs-task-definition.json`:
```json
{
  "family": "hrtech-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "hrtech-backend",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/hrtech-backend:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://..."
        }
      ]
    }
  ]
}
```

#### **Step 5: Register Task Definition**
```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

#### **Step 6: Create Service**
```bash
aws ecs create-service \
  --cluster hrtech-cluster \
  --service-name hrtech-service \
  --task-definition hrtech-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

---

## Manual Server Deployment

### Step-by-Step for Linux/Ubuntu Server

#### **Step 1: SSH into Server**
```bash
ssh user@your-server-ip
```

#### **Step 2: Update System**
```bash
sudo apt update
sudo apt upgrade -y
```

#### **Step 3: Install Python & Dependencies**
```bash
sudo apt install python3 python3-pip python3-venv git postgresql postgresql-contrib redis-server -y
```

#### **Step 4: Clone Repository**
```bash
git clone https://github.com/sumitaiml/-AI-Powered-Resume-Job-Matching-Hiring-Intelligence-System.git
cd hrtech-platform
```

#### **Step 5: Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### **Step 6: Install Python Dependencies**
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### **Step 7: Configure PostgreSQL**
```bash
sudo systemctl start postgresql
sudo sudo -u postgres psql -c "CREATE DATABASE hrtech_db;"
sudo sudo -u postgres psql -c "CREATE USER hrtech_user WITH PASSWORD 'secure_password';"
sudo sudo -u postgres psql -c "ALTER ROLE hrtech_user SET client_encoding TO 'utf8';"
sudo sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hrtech_db TO hrtech_user;"
```

#### **Step 8: Create Environment File**
```bash
nano .env
```
Add:
```
DATABASE_URL=postgresql://hrtech_user:secure_password@localhost/hrtech_db
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=production
```

#### **Step 9: Run Migrations & Start Backend**
```bash
# Start backend
python backend/app/main.py

# OR with gunicorn (for production)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 backend.app.main:app
```

#### **Step 10: Start Flask Gateway (in separate terminal)**
```bash
source venv/bin/activate
python flask_gateway.py
```

#### **Step 11: Setup Nginx as Reverse Proxy**
```bash
sudo apt install nginx -y
```

Create `/etc/nginx/sites-available/hrtech`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/hrtech /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### **Step 12: Setup SSL (Let's Encrypt)**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

#### **Step 13: Setup Systemd Services (Auto-restart)**

Create `/etc/systemd/system/hrtech-backend.service`:
```ini
[Unit]
Description=HRTech Backend
After=network.target postgresql.service

[Service]
User=your-user
WorkingDirectory=/home/your-user/hrtech-platform
Environment="PATH=/home/your-user/hrtech-platform/venv/bin"
ExecStart=/home/your-user/hrtech-platform/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 backend.app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hrtech-backend
sudo systemctl start hrtech-backend
```

---

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Enable SSL/TLS (HTTPS)
- [ ] Configure firewall rules (only allow necessary ports)
- [ ] Enable database authentication
- [ ] Use environment variables for secrets (not hardcoded)
- [ ] Enable CORS only for trusted domains
- [ ] Setup rate limiting
- [ ] Enable request validation

### Performance
- [ ] Enable caching (Redis)
- [ ] Setup CDN for static files
- [ ] Enable gzip compression
- [ ] Setup database backups (daily)
- [ ] Configure connection pooling
- [ ] Setup monitoring and alerts
- [ ] Enable auto-scaling (if on cloud)

### Monitoring & Logging
- [ ] Setup centralized logging (CloudWatch, ELK stack)
- [ ] Configure health checks
- [ ] Setup error tracking (Sentry)
- [ ] Monitor database performance
- [ ] Setup uptime monitoring
- [ ] Create backup & disaster recovery plan

### Database
- [ ] Create database backups
- [ ] Enable automated backups
- [ ] Test backup restoration
- [ ] Setup replication (optional)
- [ ] Document database schema

### Deployment
- [ ] Use CI/CD pipeline (GitHub Actions, GitLab CI)
- [ ] Automated testing before deployment
- [ ] Blue-green deployment strategy
- [ ] Rollback plan
- [ ] Version control for configs

---

## Troubleshooting

### Docker Issues
```bash
# Check logs
docker-compose logs backend

# Restart services
docker-compose restart

# Full rebuild
docker-compose down -v && docker-compose up -d
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Connect to database
docker exec -it hrtech-postgres psql -U postgres -d hrtech_db
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml or .env
# Or kill the process using the port

# Linux/Mac
lsof -i :5000
kill -9 <PID>

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### API Not Responding
```bash
# Check backend logs
docker-compose logs backend

# Test API directly
curl http://localhost:8000/docs

# Verify database connection
docker exec hrtech-backend python -c "from app.core import get_db; print('DB OK')"
```

---

## Performance Optimization Tips

1. **Database Optimization**
   - Create indexes on frequently queried columns
   - Archive old ranking data
   - Use connection pooling

2. **Caching**
   - Cache job listings
   - Cache candidate profiles
   - Cache ranking models

3. **API Optimization**
   - Use pagination
   - Compress responses (gzip)
   - Implement request throttling

4. **Frontend Optimization**
   - Minify CSS/JS
   - Lazy load images
   - Use service workers for offline support

---

## Support & Documentation

- **API Documentation**: `http://your-domain/docs`
- **Project Repository**: https://github.com/sumitaiml/-AI-Powered-Resume-Job-Matching-Hiring-Intelligence-System
- **Issue Tracking**: GitHub Issues

---

**Last Updated**: April 2026
