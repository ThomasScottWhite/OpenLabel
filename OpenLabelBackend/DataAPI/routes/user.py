from __future__ import annotations

import logging
from typing import Final

from bson.objectid import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from .. import db, models

logger = logging.getLogger(__name__)

_section_name: Final[str] = "user"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    role_name: str = "annotator"


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(request: CreateUserRequest) -> str:

    try:
        created_id = db.user.create_user(
            request.username,
            request.email,
            request.password,
            request.first_name,
            request.last_name,
            request.role_name,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception:
        raise

    return str(created_id)


@router.get("")
def get_users(limit: int = 100) -> list[models.UserNoPasswordWithID]:

    users = db.user.get_users(limit)
    print(users)

    return users


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def get_user_by_id(data: LoginRequest) -> models.UserNoPasswordWithID:

    token = db.user.login(data.username, data.password)

    if token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Provided username and/or password was invalid.",
        )

    return token


@router.get("/{user_id}")
def get_user_by_id(user_id: str) -> models.UserNoPasswordWithID:

    user = db.user.get_user_by_id(ObjectId(user_id))

    return user


@router.put("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_user_by_id(user_id: str, data: dict):
    # TODO: need to authenticate user here to ensure update permission

    # don't do anything if no data is passed
    if not data:
        return

    try:
        db.user.update_user(ObjectId(user_id), data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception:
        raise


@router.get("/{user_id}/preferences")
def get_user_preferences(user_id: str) -> models.UserPreferences:

    user = db.user.get_user_preferences(ObjectId(user_id))

    return user


@router.put("/{user_id}/preferences", status_code=status.HTTP_204_NO_CONTENT)
def update_user_preferences(user_id: str, data: dict):

    try:
        db.user.update_user_preferences(ObjectId(user_id), data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception:
        raise
