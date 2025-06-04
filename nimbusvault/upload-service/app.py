from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path
import httpx
import os
import uvicorn

from shared.logger import configure_logger, request_id_middleware
from shared.storage_utils import save_file  # Ensure this utility exists

SERVICE_NAME = "upload-service"
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8003/metadata")
UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

logger = configure_logger(SERVICE_NAME)
app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    return await request_id_middleware(request, call_next)

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.on_event("startup")
async def startup_event():
    logger.info(f"{SERVICE_NAME} starting up")

# Routes
@app.get("/")
async def root(request: Request):
    logger.info("Health check", extra={"requestId": request.state.request_id})
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    return {"service": SERVICE_NAME, "status": "OK"}

@app.get("/log")
async def log_route(request: Request):
    logger.info(f"Received request from {request.client.host} to {request.url.path}", extra={"requestId": request.state.request_id})
    return {"message": "Request logged"}

@app.post("/upload")
async def upload(file: UploadFile = File(...), request: Request = None):
    contents = await file.read()
    logger.info(f"Received file {file.filename} of size {len(contents)} bytes", extra={"requestId": request.state.request_id})

    file_path = UPLOAD_DIR / file.filename
    save_file(str(file_path), contents)

    metadata = {
        "filename": file.filename,
        "uploaded_by": SERVICE_NAME,
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
        logger.exception("Failed to submit metadata", extra={"requestId": request.state.request_id})
        return {
            "status": "received",
            "filename": file.filename,
            "error": str(exc),
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
