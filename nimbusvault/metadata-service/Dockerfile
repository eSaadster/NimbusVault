FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY metadata-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files and shared modules
COPY metadata-service/ ./
COPY shared ./shared

# Expose correct port
EXPOSE 8003

# Start the service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]
