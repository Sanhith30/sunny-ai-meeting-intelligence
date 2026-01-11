# Google Cloud Setup Script for Windows
# Run this in PowerShell after installing gcloud CLI

Write-Host "☀️ Sunny AI - Google Cloud Setup" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow

# Step 1: Login to Google Cloud
Write-Host "`n📝 Step 1: Logging into Google Cloud..." -ForegroundColor Cyan
gcloud auth login

# Step 2: Create a new project
$PROJECT_ID = "sunny-ai-" + (Get-Random -Maximum 99999)
Write-Host "`n📝 Step 2: Creating project: $PROJECT_ID" -ForegroundColor Cyan
gcloud projects create $PROJECT_ID --name="Sunny AI"

# Step 3: Set the project
Write-Host "`n📝 Step 3: Setting active project..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# Step 4: Enable required APIs
Write-Host "`n📝 Step 4: Enabling Cloud Run API..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Step 5: Set region
Write-Host "`n📝 Step 5: Setting region..." -ForegroundColor Cyan
gcloud config set run/region us-central1

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "`nNext: Run the deploy script" -ForegroundColor Cyan
