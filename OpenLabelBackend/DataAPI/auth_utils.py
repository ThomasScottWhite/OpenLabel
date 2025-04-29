import jwt
import datetime
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


SECRET_KEY = "mynamejeff" 
ALGORITHM = "HS256"

def generate_token(user_id: str) -> str:
    payload = {
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

def auth_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> dict:
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
