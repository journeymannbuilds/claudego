#!/bin/bash
set -e

PROJECT_ID="your-gcp-project-id"  # FILL THIS IN
REGION="europe-west1"
SERVICE_NAME="longtail-mcp"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Building container..."
gcloud builds submit --tag "$IMAGE"

echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --set-env-vars "DATABRICKS_HOST=dbc-871ad75e-3eed.cloud.databricks.com" \
  --set-env-vars "DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/d490a228b5b077b3" \
  --set-env-vars "DATABRICKS_CLIENT_ID=FILL_IN" \
  --set-env-vars "DATABRICKS_CLIENT_SECRET=FILL_IN"

echo ""
echo "Deployed. URL:"
gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)'
