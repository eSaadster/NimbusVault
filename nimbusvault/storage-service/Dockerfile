FROM python:3.11-slim
WORKDIR /app
COPY storage-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY storage-service/ ./
COPY shared ./shared
CMD ["python", "app.py"]
