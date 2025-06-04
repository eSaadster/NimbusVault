FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY upload-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and shared modules
COPY upload-service/ ./
COPY shared ./shared

# Expose service port
EXPOSE 8002

# Start the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
