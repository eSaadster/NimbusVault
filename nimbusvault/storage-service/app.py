from fastapi import FastAPI
from typing import Dict, List

app = FastAPI()

stored_metadata: List[Dict] = []

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"service": "storage-service", "status": "OK"}

@app.post("/store")
async def store(metadata: Dict) -> Dict[str, str]:
    stored_metadata.append(metadata)
    print(f"Stored metadata: {metadata}")
    return {"result": "saved"}
