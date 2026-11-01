# Hugging Face Space (Docker SDK) for the public demo (T228).
# The Space holds only this file and README.md; it builds from the public GitHub repo.
# MODEL_API_KEY must be set as a Space *secret* (Settings -> Variables and secrets), never in a file.
FROM node:20-alpine AS src
ARG REPO=https://github.com/johncat88425-del/slope-coach
ARG REF=main
RUN apk add --no-cache git && git clone --depth 1 --branch "$REF" "$REPO" /src
WORKDIR /src/frontend
RUN npm ci && npm run build

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
WORKDIR /app
COPY --from=src /src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=src /src/backend ./backend
COPY --from=src /src/physics ./physics
COPY --from=src /src/meta_client ./meta_client
COPY --from=src /src/frontend/dist ./frontend/dist
RUN mkdir -p data/uploads && chown -R user /app
USER user
# Public demo: per-visitor hourly limit, 80 MB uploads, and a $25 ceiling on this server's own spend.
ENV PYTHONUNBUFFERED=1 PUBLIC_DEMO=1 PUBLIC_MAX_PER_HOUR=10 PUBLIC_MAX_UPLOAD_MB=80 \
    SPEND_LIMIT_USD=25 SLOPE_STORE_PATH="" PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips=*"]
