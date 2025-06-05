FROM python:3.11-slim

WORKDIR /app

# Install system utilities (e.g., curl for healthcheck) and Python dependencies
COPY storage-service/requirements.txt ./requirements.txt
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and shared code
COPY storage-service/ ./
COPY shared ./shared

# Expose service port
EXPOSE 8004

# Start the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8004"]

# Healthcheck for service readiness
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8004/health/ready || exit 1
