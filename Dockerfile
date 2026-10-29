# Dockerfile: Production & Local Test Deployment Draft for Slope Coach (T43)

# -------------------------------------------------------------
# Stage 1: Build Frontend Assets
# -------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# -------------------------------------------------------------
# Stage 2: Backend Runtime & Services
# -------------------------------------------------------------
FROM python:3.11-slim AS runtime

# System runtime dependencies: ffmpeg is required for video analysis
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application modules
COPY backend/ ./backend/
COPY physics/ ./physics/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Copy built frontend into backend static directory if configured
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose backend API / App port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Default command starts FastAPI backend
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
