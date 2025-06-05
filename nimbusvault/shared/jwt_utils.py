import jwt
from jwt import PyJWTError

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"


def generate_token(user_data: dict) -> str:
    """Generate a JWT token for the given user data."""
    try:
        token = jwt.encode(user_data, SECRET_KEY, algorithm=ALGORITHM)
        # In PyJWT>=2.0, encode returns a str by default
        return token
    except PyJWTError:
        return ""


def verify_token(token: str):
    """Verify a JWT token and return the contained user data or None."""
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return data
    except PyJWTError:
        return None
