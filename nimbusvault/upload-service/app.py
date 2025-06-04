from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
from datetime import datetime

METADATA_SERVICE_URL = os.getenv(
    "METADATA_SERVICE_URL",
    "http://metadata-service:8003/metadata",
)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from upload-service"}


class UploadRequest(BaseModel):
    filename: str
    content: str
    uploaded_by: str


@app.post("/upload")
async def upload_file(upload: UploadRequest):
    print(f"Received file {upload.filename} from {upload.uploaded_by}")
    metadata = {
        "filename": upload.filename,
        "uploaded_by": upload.uploaded_by,
        "timestamp": datetime.utcnow().isoformat(),
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(METADATA_SERVICE_URL, json=metadata)
    return {"metadata": response.json()}
