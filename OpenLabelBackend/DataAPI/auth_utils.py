import datetime

from dotenv import load_dotenv
import os
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import secrets
from . import models

load_dotenv()
SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(32)  # 256-bit key
    with open(".env", "a") as f:
        f.write(f"\nAUTH_SECRET_KEY={SECRET_KEY}")
    print("🔑 Generated new AUTH_SECRET_KEY and saved to .env")
    
ALGORITHM = "HS256"


def generate_token(user_id: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "userId": str(user_id),
        "exp": now + datetime.timedelta(hours=1),
        "iat": now,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> models.TokenPayload:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return models.TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
        )


def refresh_token(token: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    decoded_payload["exp"] = now + datetime.timedelta(hours=1)
    return jwt.encode(decoded_payload, SECRET_KEY, algorithms=[ALGORITHM])


def auth_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> models.TokenPayload:
    token = credentials.credentials
    payload = decode_token(token)
    return payload


# Example Usage
# from fastapi import APIRouter, Depends
# from auth_dependencies import auth_user

# router = APIRouter()

# @router.get("/protected")
# def protected_route(current_user: dict = Depends(auth_user)):
#     return {"message": "Access granted", "user_id": current_user["user_id"]}
