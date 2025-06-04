from pathlib import Path
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, public_key: str):
        super().__init__(app)
        self.public_key = public_key

    async def dispatch(self, request: Request, call_next):
        token = None
        auth = request.headers.get('Authorization')
        if auth and auth.lower().startswith('bearer '):
            token = auth.split(' ', 1)[1]
        if not token:
            token = request.cookies.get('access_token')
        if token:
            try:
                payload = jwt.decode(token, self.public_key, algorithms=['RS256'])
                request.state.user = payload
            except jwt.PyJWTError:
                return JSONResponse(status_code=401, content={'detail': 'Invalid token'})
        else:
            request.state.user = None
        return await call_next(request)

def get_current_user(request: Request):
    if not getattr(request.state, 'user', None):
        raise HTTPException(status_code=401, detail='Not authenticated')
    return request.state.user

