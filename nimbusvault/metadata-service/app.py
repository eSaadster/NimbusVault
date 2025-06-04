from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import os
import psycopg2

SERVICE_NAME = "metadata-service"

app = FastAPI()

# Enable CORS for all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

class Metadata(BaseModel):
    filename: str
    uploaded_by: str
    timestamp: datetime

@app.get("/")
async def root():
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"service": SERVICE_NAME, "status": "OK"}

@app.post("/metadata")
async def create_metadata(metadata: Metadata):
    if not DATABASE_URL:
        return {"error": "DATABASE_URL not set"}

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO metadata (filename, uploaded_by, timestamp) VALUES (%s, %s, %s) RETURNING id",
        (metadata.filename, metadata.uploaded_by, metadata.timestamp),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": new_id,
        "filename": metadata.filename,
        "uploaded_by": metadata.uploaded_by,
        "timestamp": metadata.timestamp.isoformat(),
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
