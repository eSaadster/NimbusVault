FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and Python requirements
COPY upload-service/requirements.txt ./requirements.txt
RUN apt-get update && apt-get install -y curl \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# Copy service code and shared modules
COPY upload-service/ ./
COPY shared ./shared

# Expose service port
EXPOSE 8002

# Start the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]

# Define container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:8002/health/ready || exit 1
