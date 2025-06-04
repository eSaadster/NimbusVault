from fastapi import FastAPI, UploadFile, File
import httpx
import os

METADATA_SERVICE_URL = os.environ.get("METADATA_SERVICE_URL", "http://metadata-service:8003")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from upload-service"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    print(f"Received file {file.filename} of size {len(contents)} bytes")

    metadata = {"info": f"Uploaded {file.filename}, size {len(contents)} bytes"}

    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{METADATA_SERVICE_URL}/metadata", json=metadata)
        except Exception as exc:
            print(f"Failed to submit metadata: {exc}")

    return {"status": "received", "filename": file.filename}
