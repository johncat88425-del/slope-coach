# Deployment Guide & Local Docker Draft (T43)

> Note: Intended for local container testing only. Do not deploy to public production without explicit review.

## Security Rules
1. **Never bake secrets into the container image**: `.env` and `.env.*` files are explicitly excluded via `.dockerignore`.
2. **Runtime Configuration**: Always pass API keys and ports at runtime via environment variables or an external env file.

## Prerequisites
- Docker / Docker Desktop installed locally
- `MODEL_API_KEY` (Meta Model API Key) in your local `.env`

## Build & Run Locally

### 1. Build Image
```bash
docker build -t slope-coach:latest .
```

### 2. Run Container (Passing Local Env File)
```bash
docker run -d \
  --name slope-coach \
  -p 8000:8000 \
  --env-file .env \
  slope-coach:latest
```

### 3. Verify Health & Audit API
```bash
# Check container logs
docker logs slope-coach

# Test API endpoints
curl -s http://localhost:8000/api/audits
```

### 4. Stop and Clean Up
```bash
docker stop slope-coach && docker rm slope-coach
```
