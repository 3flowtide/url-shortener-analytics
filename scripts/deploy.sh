#!/usr/bin/env bash
# usage: PROJECT_ID=my-project REGION=us-central1 ./scripts/deploy.sh

set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID to your GCP project id}"
REGION="${REGION:-us-central1}"
SQL_INSTANCE="${SQL_INSTANCE:-shortener-db}"
SQL_DATABASE="${SQL_DATABASE:-shortener}"
SQL_USER="${SQL_USER:-app_user}"
SERVICE_NAME="${SERVICE_NAME:-url-shortener}"
PUBSUB_TOPIC="${PUBSUB_TOPIC:-click-events}"
FUNCTION_NAME="${FUNCTION_NAME:-process-click-event}"

echo "==> Enabling required APIs"
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  pubsub.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  eventarc.googleapis.com \
  --project "$PROJECT_ID"

# grant iam roles
echo "==> Ensuring the default compute service account can build and run this app"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
for ROLE in roles/storage.objectViewer roles/artifactregistry.writer roles/logging.logWriter roles/cloudsql.client roles/pubsub.publisher; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${COMPUTE_SA}" --role="$ROLE" --condition=None --quiet >/dev/null
done

echo "==> Creating Cloud SQL instance (skipped if it already exists)"
gcloud sql instances describe "$SQL_INSTANCE" --project "$PROJECT_ID" >/dev/null 2>&1 || \
  gcloud sql instances create "$SQL_INSTANCE" \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region="$REGION" \
    --project "$PROJECT_ID"

gcloud sql databases create "$SQL_DATABASE" --instance="$SQL_INSTANCE" --project "$PROJECT_ID" || true

echo "==> Creating database user $SQL_USER (skipped if it already exists)"
if ! gcloud sql users list --instance="$SQL_INSTANCE" --project "$PROJECT_ID" \
    --format='value(name)' | grep -qx "$SQL_USER"; then
  SQL_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
  gcloud sql users create "$SQL_USER" --instance="$SQL_INSTANCE" \
    --password="$SQL_PASSWORD" --project "$PROJECT_ID"
  echo "==> Generated password for $SQL_USER: $SQL_PASSWORD (save this -- it is not stored anywhere else)"
else
  echo "==> User $SQL_USER already exists; set SQL_PASSWORD to its existing password before running this script."
  SQL_PASSWORD="${SQL_PASSWORD:?SQL_USER already exists -- set SQL_PASSWORD to its current password}"
fi

INSTANCE_CONNECTION_NAME="$(gcloud sql instances describe "$SQL_INSTANCE" \
  --project "$PROJECT_ID" --format='value(connectionName)')"
DATABASE_URL="postgresql+psycopg2://${SQL_USER}:${SQL_PASSWORD}@/${SQL_DATABASE}?host=/cloudsql/${INSTANCE_CONNECTION_NAME}"

echo "==> Creating Pub/Sub topic"
gcloud pubsub topics create "$PUBSUB_TOPIC" --project "$PROJECT_ID" || true

echo "==> Deploying Cloud Run service"
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --add-cloudsql-instances "$INSTANCE_CONNECTION_NAME" \
  --set-env-vars "DATABASE_URL=${DATABASE_URL},PUBSUB_ENABLED=true,PUBSUB_PROJECT_ID=${PROJECT_ID},PUBSUB_TOPIC=${PUBSUB_TOPIC}" \
  --allow-unauthenticated

echo "==> Deploying Cloud Function (async click processing)"
gcloud functions deploy "$FUNCTION_NAME" \
  --gen2 \
  --runtime=python311 \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --source=. \
  --entry-point=process_click_event \
  --trigger-topic="$PUBSUB_TOPIC" \
  --set-env-vars "DATABASE_URL=${DATABASE_URL}"

echo "==> Attaching Cloud SQL to the function's underlying Cloud Run service"
gcloud run services update "$FUNCTION_NAME" \
  --region "$REGION" --project "$PROJECT_ID" \
  --add-cloudsql-instances "$INSTANCE_CONNECTION_NAME"

echo "==> Done. Remember to set BASE_URL on the Cloud Run service to its public URL:"
echo "    gcloud run services update $SERVICE_NAME --region $REGION --update-env-vars BASE_URL=<service-url>"
