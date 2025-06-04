from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Dict, List
import os
import uvicorn

from shared.storage_utils import save_file  # Ensure this utility exists

SERVICE_NAME = "storage-service"
STORAGE_DIR = Path("/tmp/storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)  # Ensure storage directory exists

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

stored_metadata: List[Dict] = []

@app.get("/")
async def root():
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    return {"service": SERVICE_NAME, "status": "OK"}

@app.post("/store")
async def store(metadata: Dict) -> Dict[str, str]:
    stored_metadata.append(metadata)
    print(f"Stored metadata: {metadata}")
    return {"result": "saved"}

@app.post("/files")
async def store_file(file: UploadFile = File(...)):
    data = await file.read()
    file_path = STORAGE_DIR / file.filename
    save_file(str(file_path), data)
    return {"filename": file.filename}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
