#!/bin/bash
# Deploy to Google Cloud Run (Free Tier)
# Prerequisites: gcloud CLI installed, project created

PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="sunny-ai"

echo "☀️ Deploying Sunny AI to Google Cloud Run..."

# Build and push container
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY,GMAIL_ADDRESS=$GMAIL_ADDRESS,GMAIL_APP_PASSWORD=$GMAIL_APP_PASSWORD"

echo "✅ Deployed! URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
