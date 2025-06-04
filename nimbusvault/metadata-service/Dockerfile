FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and Python requirements
COPY metadata-service/requirements.txt ./requirements.txt
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files and shared modules
COPY metadata-service/ ./
COPY shared ./shared

# Expose correct port
EXPOSE 8003

# Start the service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8003/health/ready || exit 1
