import os

SERVICE_NAME = "metadata-service"
DATABASE_URL = os.getenv("DATABASE_URL", "")
DB_CONNECT_TIMEOUT = 3  # seconds
