#!/bin/bash

# Configuration
PROJECT_ID="amdhacakthon"
SERVICE_NAME="amd-hardware-agent"
REGION="us-central1"

echo "🚀 Starting Professional Deployment to Google Cloud..."

# 1. Build and Deploy Backend to Cloud Run
echo "📦 Building and Deploying Dockerized Backend..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --project $PROJECT_ID \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY,GROQ_API_KEY=$GROQ_API_KEY"

# 2. Deploy Frontend & Proxy Rules to Firebase
echo "🌐 Deploying Frontend and Rewrites to Firebase Hosting..."
firebase deploy --only hosting --project $PROJECT_ID

echo "✨ Deployment Finished!"
echo "Check your live site at: https://$PROJECT_ID.web.app"
