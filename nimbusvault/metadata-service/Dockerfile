FROM python:3.11-slim
WORKDIR /app
COPY metadata-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY metadata-service/ ./
COPY shared ./shared
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]
