import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

SERVICE_NAME = "upload-service"

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
