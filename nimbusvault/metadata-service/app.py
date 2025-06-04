from fastapi import FastAPI
import os
import psycopg2

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from metadata-service"}


@app.get("/health")
async def health():
    return {"service": "metadata-service", "status": "OK"}
