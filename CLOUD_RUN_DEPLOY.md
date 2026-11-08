# NetraAI — Google Cloud Run deployment

This repository is prepared for Cloud Run while keeping the existing Vercel frontend.

## Runtime configuration

Recommended production settings:

- Region: asia-south1
- CPU: 2 vCPU
- Memory: 4 GiB
- Concurrency: 1
- Max instances: 1
- Timeout: 900 seconds
- Container port: 8080
- Public access: enabled

Concurrency and max instances are intentionally limited because the current inference
pipeline is CPU/memory heavy and writes case artifacts to the container filesystem.

## One-time Google Cloud setup

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

gcloud artifacts repositories create netraai \
  --repository-format=docker \
  --location=asia-south1 \
  --description="NetraAI backend images"
```

## Deploy

Run from the repository root:

```bash
gcloud builds submit --config cloudbuild.yaml
```

The build uses `Dockerfile.cloudrun`, pushes the image to Artifact Registry and deploys
`netraai-api` to Cloud Run.

## Verify the backend

```bash
SERVICE_URL=$(gcloud run services describe netraai-api \
  --region asia-south1 \
  --format='value(status.url)')

echo "$SERVICE_URL"
curl "$SERVICE_URL/api/health"
```

Expected health fields include:

- status = healthy
- engine_loaded = true
- global_model = true
- lesion_model = true
- structural_layer = true

## Connect the existing Vercel frontend

Set the existing Vercel project's environment variable:

```
VITE_API_URL=https://YOUR-CLOUD-RUN-SERVICE-URL
```

Then redeploy the existing frontend project. The frontend now prefers VITE_API_URL in
production, so the Vercel domain does not need to change.
