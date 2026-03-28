# Professional AMD Platform Deployment Script (PowerShell)
$PROJECT_ID = "amdhacakthon"
$SERVICE_NAME = "amd-hardware-agent"
$REGION = "us-central1"

Write-Host "🚀 Starting Deployment to Google Cloud..." -ForegroundColor Cyan

# 1. Deploy Backend to Cloud Run
Write-Host "📦 Building and Deploying Dockerized Backend..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
  --source . `
  --project $PROJECT_ID `
  --region $REGION `
  --allow-unauthenticated `
  --set-env-vars "GEMINI_API_KEY=$($env:GEMINI_API_KEY),GROQ_API_KEY=$($env:GROQ_API_KEY)"

# 2. Deploy Frontend to Firebase
Write-Host "🌐 Deploying Frontend to Firebase Hosting..." -ForegroundColor Yellow
firebase deploy --only hosting --project $PROJECT_ID

Write-Host "✨ Deployment Finished!" -ForegroundColor Green
$LIVE_URL = "https://" + $PROJECT_ID + ".web.app"
Write-Host "Live Site: $LIVE_URL" -ForegroundColor Green
