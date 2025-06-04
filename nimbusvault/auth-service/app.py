import os
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from passlib.hash import bcrypt

BASE_DIR = Path(__file__).resolve().parent
with open(BASE_DIR / 'keys/private.pem') as f:
    PRIVATE_KEY = f.read()
with open(BASE_DIR / 'keys/public.pem') as f:
    PUBLIC_KEY = f.read()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

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

users = {}
next_id = 1
RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_COUNT = 5


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
    return jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')


def verify_token(token: str, refresh: bool = False):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
        if refresh and payload.get('type') != 'refresh':
            raise jwt.InvalidTokenError
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail='Invalid token')


def get_token_from_request(request: Request) -> str | None:
    auth = request.headers.get('Authorization')
    if auth and auth.lower().startswith('bearer '):
        return auth.split(' ', 1)[1]
    cookie = request.cookies.get('access_token')
    return cookie


def get_current_user(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    return payload


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
        password_hash=bcrypt.hash(data.password),
    )
    users[data.username] = user
    next_id += 1
    return {'message': 'registered'}


@app.post('/login')
async def login(data: LoginModel, request: Request):
    check_rate_limit(request.client.host)
    user = users.get(data.username)
    if not user or not bcrypt.verify(data.password, user.password_hash):
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
    token = request.cookies.get('refresh_token')
    if not token:
        auth = request.headers.get('Authorization')
        if auth and auth.lower().startswith('bearer '):
            token = auth.split(' ', 1)[1]
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


@app.get('/')
async def root():
    return {'message': 'Hello from auth-service'}

