from fastapi import FastAPI, UploadFile, File
from pathlib import Path

from shared.storage_utils import save_file

app = FastAPI()

STORAGE_DIR = Path("/tmp/storage")

@app.get("/")
async def root():
    return {"message": "Hello from storage-service"}


@app.post("/files")
async def store_file(file: UploadFile = File(...)):
    data = await file.read()
    file_path = STORAGE_DIR / file.filename
    save_file(str(file_path), data)
    return {"filename": file.filename}
