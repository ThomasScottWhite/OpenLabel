import datetime

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import models
from .config import CONFIG

ALGORITHM = "HS256"


def generate_token(user_id: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "userId": str(user_id),
        "exp": now + datetime.timedelta(hours=1),
        "iat": now,
    }
    return jwt.encode(payload, CONFIG.auth_secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> models.TokenPayload:
    try:
        payload = jwt.decode(token, CONFIG.auth_secret_key, algorithms=[ALGORITHM])
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
    decoded_payload = jwt.decode(token, CONFIG.auth_secret_key, algorithms=[ALGORITHM])
    decoded_payload["exp"] = now + datetime.timedelta(hours=1)
    return jwt.encode(decoded_payload, CONFIG.auth_secret_key, algorithms=[ALGORITHM])


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
