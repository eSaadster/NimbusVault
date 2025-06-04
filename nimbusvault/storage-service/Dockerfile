FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY storage-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and shared code
COPY storage-service/ ./
COPY shared ./shared

# Expose service port
EXPOSE 8004

# Start the service using Uvicorn if it's a FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8004"]
