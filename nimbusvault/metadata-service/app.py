import sys
from pathlib import Path
from fastapi import FastAPI, Depends
import os
import psycopg2

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / 'shared'))
from auth_middleware import AuthMiddleware, get_current_user

PUBLIC_KEY_PATH = BASE_DIR / 'auth-service' / 'keys' / 'public.pem'
with open(PUBLIC_KEY_PATH) as f:
    PUBLIC_KEY = f.read()

app = FastAPI()
app.add_middleware(AuthMiddleware, public_key=PUBLIC_KEY)

@app.get("/")
async def root():
    return {"message": "Hello from metadata-service"}


@app.get("/public")
async def public_route():
    return {"message": "public"}


@app.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"message": "protected", "user": user}

