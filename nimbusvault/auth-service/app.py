import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

from shared.logger import configure_logger, request_id_middleware

SERVICE_NAME = "auth-service"
BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR / 'keys/private.pem') as f:
    PRIVATE_KEY = f.read()
with open(BASE_DIR / 'keys/public.pem') as f:
    PUBLIC_KEY = f.read()

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
users = {}
next_id = 1
RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_COUNT = 5

logger = configure_logger(SERVICE_NAME)
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "auth_requests_total", "Total HTTP requests", ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "auth_request_latency_seconds", "Latency of HTTP requests", ["endpoint"]
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(duration)
    return response

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    return await request_id_middleware(request, call_next)

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# Models
class User(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str

class RegisterModel(BaseModel):
    username: str
    email: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

# Auth utils
def check_rate_limit(ip: str):
    now = datetime.utcnow()
    timestamps = RATE_LIMIT.get(ip, [])
    timestamps = [t for t in timestamps if (now - t).total_seconds() < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_COUNT:
        raise HTTPException(status_code=429, detail="Too many requests")
    timestamps.append(now)
    RATE_LIMIT[ip] = timestamps

def create_token(data: dict, expires: timedelta, refresh: bool = False):
    payload = data.copy()
    payload['exp'] = datetime.utcnow() + expires
    if refresh:
        payload['type'] = 'refresh'
    return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)

def verify_token(token: str, refresh: bool = False):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        if refresh and payload.get('type') != 'refresh':
            raise jwt.JWTError()
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')

def get_token_from_request(request: Request):
    auth = request.headers.get('Authorization')
    if auth and auth.lower().startswith('bearer '):
        return auth.split(' ', 1)[1]
    return request.cookies.get('access_token')

def get_current_user(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    return payload

# Routes
@app.post('/register')
async def register(data: RegisterModel, request: Request):
    check_rate_limit(request.client.host)
    global next_id
    if data.username in users:
        raise HTTPException(status_code=400, detail='User exists')
    user = User(
        id=next_id,
        username=data.username,
        email=data.email,
        password_hash=pwd_context.hash(data.password),
    )
    users[data.username] = user
    next_id += 1
    return {'message': 'registered'}

@app.post('/login')
async def login(data: LoginModel, request: Request):
    check_rate_limit(request.client.host)
    user = users.get(data.username)
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token_data = {'sub': user.username, 'uid': user.id}
    access = create_token(token_data, timedelta(minutes=30))
    refresh = create_token(token_data, timedelta(days=7), refresh=True)
    response = JSONResponse({'access_token': access, 'refresh_token': refresh})
    response.set_cookie('access_token', access, httponly=True)
    response.set_cookie('refresh_token', refresh, httponly=True)
    return response

@app.post('/refresh')
async def refresh(request: Request):
    token = request.cookies.get('refresh_token') or get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='No token')
    payload = verify_token(token, refresh=True)
    user = users.get(payload['sub'])
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    access = create_token({'sub': user.username, 'uid': user.id}, timedelta(minutes=30))
    response = JSONResponse({'access_token': access})
    response.set_cookie('access_token', access, httponly=True)
    return response

@app.get('/me')
async def me(user=Depends(get_current_user)):
    return {'user': user}

@app.get("/")
async def root():
    return {'message': f'Hello from {SERVICE_NAME}'}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health():
    return {"service": SERVICE_NAME, "status": "OK"}

@app.get("/health/live")
async def health_live():
    return {"status": "ok"}

@app.get("/health/ready")
async def health_ready():
    return {"status": "ok"}

@app.get("/health/detailed")
async def health_detailed():
    return {"status": "ok", "dependencies": {}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
