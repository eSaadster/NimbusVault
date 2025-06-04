from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import psycopg2
from shared.logger import configure_logger, request_id_middleware

logger = configure_logger("metadata-service")
app = FastAPI()

@app.middleware('http')
async def add_request_id(request: Request, call_next):
    return await request_id_middleware(request, call_next)

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.on_event("startup")
async def startup_event():
    logger.info("Metadata service starting up")

@app.get("/")
async def root(request: Request):
    logger.info("Health check", extra={"requestId": request.state.request_id})
    return {"message": "Hello from metadata-service"}
