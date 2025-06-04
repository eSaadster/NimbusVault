from fastapi import FastAPI, UploadFile, File
from pathlib import Path

from shared.storage_utils import save_file

app = FastAPI()

UPLOAD_DIR = Path("/tmp/uploads")

@app.get("/")
async def root():
    return {"message": "Hello from upload-service"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    data = await file.read()
    file_path = UPLOAD_DIR / file.filename
    save_file(str(file_path), data)
    return {"filename": file.filename}
