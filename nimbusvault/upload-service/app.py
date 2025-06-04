from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health():
    return {"service": "upload-service", "status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
