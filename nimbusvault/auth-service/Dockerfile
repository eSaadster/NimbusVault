FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and copy requirements
COPY auth-service/requirements.txt ./requirements.txt
RUN apt-get update && apt-get install -y curl \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# Copy service-specific code and shared modules
COPY auth-service/ ./
COPY shared ./shared

# Expose the correct port
EXPOSE 8001

# Start the service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:8001/health/ready || exit 1
