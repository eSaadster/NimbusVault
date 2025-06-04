import logging
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import httpx
import os
import uvicorn

SERVICE_NAME = "upload-service"
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8003/metadata")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    try:
        return {"message": f"Hello from {SERVICE_NAME}"}
    except Exception as e:
        logger.exception("Error in root endpoint")
        return {"error": "Internal server error"}

@app.get("/health")
async def health() -> dict:
    return {"service": SERVICE_NAME, "status": "OK"}

@app.get("/log")
async def log_route(request: Request):
    logger.info(f"Received request from {request.client.host} to {request.url.path}")
    return {"message": "Request logged"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    logger.info(f"Received file {file.filename} of size {len(contents)} bytes")

    metadata = {
        "filename": file.filename,
        "uploaded_by": "upload-service",  # In a real app, replace with actual user
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(METADATA_SERVICE_URL, json=metadata)
            response.raise_for_status()
        return {
            "status": "received",
            "filename": file.filename,
            "metadata_response": response.json(),
        }
    except Exception as exc:
        logger.exception("Failed to submit metadata")
        return {"status": "received", "filename": file.filename, "error": str(exc)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
