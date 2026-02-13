# Multi-stage build for React Frontend + Python Backend

# 1. Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
# Ensure .env is empty or configured for relative paths
RUN echo "VITE_API_URL=" > .env && echo "VITE_WS_URL=" >> .env
RUN npm run build

# 2. Build Runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for building python wheels if needed)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python Code
COPY . .

# Copy Frontend Build from builder stage
COPY --from=frontend-builder /app/dashboard/dist ./dashboard/dist

# Expose port
EXPOSE 3000

# Set Env vars for production
ENV PYTHONUNBUFFERED=1

# Command to run the unified server
CMD ["python", "unified_server.py"]
