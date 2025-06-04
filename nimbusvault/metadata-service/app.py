from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import os
import psycopg2

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from metadata-service"}


DATABASE_URL = os.getenv("DATABASE_URL")


class Metadata(BaseModel):
    filename: str
    uploaded_by: str
    timestamp: datetime


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
