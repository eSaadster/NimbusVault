FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY auth-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy service-specific code and shared modules
COPY auth-service/ ./
COPY shared ./shared

# Expose the correct port
EXPOSE 8001

# Start the service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
