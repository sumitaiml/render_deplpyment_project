@echo off
REM HR Tech Platform - Quick Deployment Script for Windows
REM Supports: Local Docker and Azure deployment

setlocal enabledelayedexpansion

color 0A
cls

echo.
echo ========================================
echo HR Tech Platform - Deployment Helper
echo ========================================
echo.

:menu
cls
echo.
echo Select Deployment Option:
echo.
echo 1 - Local Docker Compose (Easiest - 5 min)
echo 2 - Azure Container Instances
echo 3 - Azure App Service
echo 4 - AWS EC2 with Docker
echo 5 - View Full Deployment Guide
echo 6 - Test Docker Setup
echo 7 - Cleanup (Stop all services)
echo 8 - Exit
echo.
set /p choice="Enter choice [1-8]: "

if "%choice%"=="1" goto deploy_docker
if "%choice%"=="2" goto deploy_azure
if "%choice%"=="3" goto deploy_azure_app
if "%choice%"=="4" goto deploy_aws
if "%choice%"=="5" goto view_guide
if "%choice%"=="6" goto test_docker
if "%choice%"=="7" goto cleanup
if "%choice%"=="8" goto end
echo Invalid option. Please try again.
timeout /t 2 /nobreak
goto menu

:deploy_docker
cls
echo.
echo ========================================
echo Local Docker Compose Deployment
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    goto menu
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not installed.
    echo Please update Docker Desktop to the latest version.
    pause
    goto menu
)

echo [✓] Docker and Docker Compose found
echo.
echo Creating .env file...

REM Create .env if not exists
if not exist ".env" (
    (
        echo # Database Configuration
        echo POSTGRES_USER=postgres
        echo POSTGRES_PASSWORD=hrtech_secure_pass_2024
        echo POSTGRES_DB=hrtech_db
        echo DATABASE_URL=postgresql://postgres:hrtech_secure_pass_2024@postgres:5432/hrtech_db
        echo.
        echo # Redis
        echo REDIS_URL=redis://redis:6379/0
        echo.
        echo # Backend Configuration
        echo BACKEND_HOST=0.0.0.0
        echo BACKEND_PORT=8000
        echo.
        echo # Frontend Configuration
        echo FLASK_HOST=0.0.0.0
        echo FLASK_PORT=5000
        echo.
        echo # ML Models
        echo SPACY_MODEL=en_core_web_sm
        echo SBERT_MODEL=all-MiniLM-L6-v2
        echo.
        echo # Environment
        echo ENVIRONMENT=production
        echo DEBUG=false
    ) > .env
    echo [✓] .env file created
) else (
    echo [*] .env file already exists
)

echo.
echo Building Docker images...
docker-compose build --no-cache

echo.
echo Starting services... (This may take 2-3 minutes)
docker-compose up -d

echo.
echo Waiting for services to be healthy...
timeout /t 30 /nobreak

echo.
echo Checking service status...
docker-compose ps

echo.
echo ========================================
echo [✓] Deployment Complete!
echo ========================================
echo.
echo Access the application:
echo   Frontend: http://localhost:5000
echo   API Docs: http://localhost:5000/docs
echo   Backend:  http://localhost:8000/docs
echo.
echo Useful Commands:
echo   View logs:        docker-compose logs -f
echo   Stop services:    docker-compose stop
echo   Start services:   docker-compose start
echo   Restart services: docker-compose restart
echo   Remove all:       docker-compose down -v
echo.
pause
goto menu

:deploy_azure
cls
echo.
echo ========================================
echo Azure Container Instances Deployment
echo ========================================
echo.
echo For detailed Azure deployment instructions,
echo open DEPLOYMENT_GUIDE.md and follow the Azure ACI section.
echo.
echo Quick Steps:
echo 1. Install Azure CLI from: https://docs.microsoft.com/cli/azure/install-azure-cli-windows
echo 2. Run: az login
echo 3. Create resource group: az group create --name hrtech-rg --location eastus
echo 4. Create container registry: az acr create --resource-group hrtech-rg --name hrtechregistry --sku Basic
echo 5. Build image: az acr build --registry hrtechregistry --image hrtech-backend:1.0 ./backend
echo.
pause
goto menu

:deploy_azure_app
cls
echo.
echo ========================================
echo Azure App Service Deployment
echo ========================================
echo.
echo For detailed instructions, see DEPLOYMENT_GUIDE.md
echo.
echo This option requires:
echo - Azure CLI installed
echo - Azure subscription
echo - Docker image in Azure Container Registry
echo.
pause
goto menu

:deploy_aws
cls
echo.
echo ========================================
echo AWS EC2 Deployment
echo ========================================
echo.
echo For detailed instructions, see DEPLOYMENT_GUIDE.md
echo.
echo Quick Steps:
echo 1. Launch EC2 instance (Ubuntu 20.04)
echo 2. Connect via SSH
echo 3. Install Docker and Docker Compose
echo 4. Clone repository and run docker-compose up -d
echo.
pause
goto menu

:view_guide
cls
echo.
echo ========================================
echo Opening Deployment Guide
echo ========================================
echo.
if exist "DEPLOYMENT_GUIDE.md" (
    start notepad DEPLOYMENT_GUIDE.md
) else (
    echo ERROR: DEPLOYMENT_GUIDE.md not found
    pause
)
goto menu

:test_docker
cls
echo.
echo ========================================
echo Testing Docker Setup
echo ========================================
echo.

docker --version
echo.
docker-compose --version
echo.

echo Testing Docker daemon...
docker ps
if errorlevel 1 (
    echo ERROR: Docker daemon is not running
    echo Please start Docker Desktop
) else (
    echo [✓] Docker is working correctly
)

echo.
pause
goto menu

:cleanup
cls
echo.
echo ========================================
echo Cleanup Services
echo ========================================
echo.
echo This will stop and remove all containers
echo.
set /p confirm="Continue? (yes/no): "

if /i "%confirm%"=="yes" (
    echo.
    echo Stopping services...
    docker-compose down -v
    echo [✓] All services stopped and removed
) else (
    echo Cleanup cancelled
)

echo.
pause
goto menu

:end
cls
echo.
echo Thank you for using HR Tech Platform!
echo.
echo For questions or support, visit:
echo https://github.com/sumitaiml/-AI-Powered-Resume-Job-Matching-Hiring-Intelligence-System
echo.
timeout /t 2 /nobreak
exit /b 0
