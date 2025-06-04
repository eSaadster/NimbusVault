from fastapi import FastAPI
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "common"))
from storage_utils import save_file

app = FastAPI()

@app.get("/")
async def root():
    save_file("auth.txt", "auth-service")
    return {"message": "Hello from auth-service"}
