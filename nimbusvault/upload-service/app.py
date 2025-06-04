import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# Enable CORS for all origins, methods, and headers
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

@app.get("/log")
async def log_route(request: Request):
    logger.info(f"Received request from {request.client.host} to {request.url.path}")
    return {"message": "Request logged"}

@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"service": SERVICE_NAME, "status": "OK"}

class UploadRequest(BaseModel):
    filename: str
    content: str
    uploaded_by: str

@app.post("/upload")
async def upload_file(upload: UploadRequest):
    logger.info(f"Received file {upload.filename} from {upload.uploaded_by}")
    metadata = {
        "filename": upload.filename,
        "uploaded_by": upload.uploaded_by,
        "timestamp": datetime.utcnow().isoformat(),
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(METADATA_SERVICE_URL, json=metadata)
    return {"metadata": response.json()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
