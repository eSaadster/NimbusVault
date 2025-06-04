from fastapi import FastAPI
import uvicorn
import os
import psycopg2

SERVICE_NAME = "metadata-service"

app = FastAPI()

@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"service": SERVICE_NAME, "status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
