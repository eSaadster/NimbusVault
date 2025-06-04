import logging
from fastapi import FastAPI, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    try:
        return {"message": "Hello from upload-service"}
    except Exception as e:
        logger.exception("Error in root endpoint")
        return {"error": "Internal server error"}

@app.get("/log")
async def log_route(request: Request):
    logger.info(f"Received request from {request.client.host} to {request.url.path}")
    return {"message": "Request logged"}
