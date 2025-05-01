from __future__ import annotations

import logging
from typing import Annotated, Final

from bson.objectid import ObjectId
from DataAPI.auth_utils import auth_user
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .. import db
from .. import exceptions as exc
from .. import models

logger = logging.getLogger(__name__)

_section_name: Final[str] = "user"


# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


def resolve_user_id(user_id: str, auth_token: models.TokenPayload = Depends(auth_user)):
    """Resolves a `user_id` URL parameter to a ObjectId.

    Notably, if `user_id` == "me", the userId from the auth token will be used.

    Args:
        user_id: The user-given user id.
        auth_token: Authorization information.

    Returns:
        The resolved user id.
    """
    if user_id.lower() == "me":
        return auth_token.userId
    return models.ID(user_id)


AutoID = Annotated[models.ID, Depends(resolve_user_id)]


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    role_name: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(request: CreateUserRequest) -> models.TokenOnlyResponse:
    """Creates a new user and signs them in simultaneously.

    Args:
        request: The parameters of the user.

    Raises:
        HTTPException: 400; if the provided user or email already exists, or if the provide role does not exist

    Returns:
        The auth bearer token to use to authorize further requests.
    """

    try:
        token = db.user.create_user(
            request.username,
            request.email,
            request.password,
            request.first_name,
            request.last_name,
            request.role_name,
        )
    except (exc.UserAlreadyExists, exc.EmailAlreadyExists, exc.RoleNotFound) as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            str(e),
        )

    return {"token": token}


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def get_user_by_id(data: LoginRequest) -> models.TokenOnlyResponse:

    token = db.user.login(data.username, data.password)

    if token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Provided username and/or password was invalid.",
        )

    return {"token": token}


@router.post("/logout")
def get_user_by_id(auth_token: models.TokenPayload = Depends(auth_user)):
    # TODO: this
    raise NotImplementedError


@router.get("")
def get_users(limit: int = 100) -> list[models.UserNoPasswordWithID]:
    """Gets a list of all users.

    Args:
        limit: The maximum number of users to return. Defaults to 100.

    Returns:
        A list of users matching the provided parameters.
    """

    users = db.user.get_users(limit)

    return users


@router.get("/{user_id}")
def get_user_by_id(
    user_id: AutoID,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> models.UserNoPasswordWithID:
    """Fetches a user's data by ID.

    Args:
        user_id: The ID of the user to fetch. If "me", will infer a user ID based off the Authorization information.
        auth_token: The authentication token provided by the Authorization header.

    Returns:
        The infomration regarding the user.
    """
    # TODO: auth stuff (if needed, else delete auth_token arg)

    user = db.user.get_user_by_id(ObjectId(user_id))

    if user is None:
        HTTPException(status.HTTP_404_NOT_FOUND, "Could not find requested user.")

    return user


@router.patch("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_user_by_id(
    user_id: AutoID,
    data: dict,
    auth_token: models.TokenPayload = Depends(auth_user),
):
    """Updates a user by its ID.

    Args:
        user_id: The ID of the user to fetch. If "me", will infer a user ID based off the Authorization information.
        data: A mapping of the fields to update to their new values. See `models.User` for the valid fields.
            `role_name` is also a valid field to update and will update a user's `roleId` indirectly.
        auth_token: The authentication token provided by the Authorization header.

    Raises:
        HTTPException: 403; if the caller lacks sufficient permissions to modify the specified user.
        HTTPException: 400; if the `data` field is improperly formatted.
    """
    # TODO: do auth here; ensure auth_token allows modification of user with id user_id

    # basic auth potentially
    if auth_token.userId != user_id:
        raise HTTPException(status.HTTP_403_UNAUTHORIZED, "Invalid permissions.")

    if not data:
        return

    try:
        db.user.update_user(user_id, data)
    except (
        exc.UserAlreadyExists,
        exc.EmailAlreadyExists,
        exc.InvalidPatchMap,
        exc.RoleNotFound,
    ) as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/{user_id}/preferences")
def get_user_preferences(
    user_id: AutoID,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> models.UserPreferences:
    """Fetches the user's preferences.

    Args:
        user_id: The ID of the user to fetch. If "me", will infer a user ID based off the Authorization information.
        auth_token: The authentication token provided by the Authorization header.

    Returns:
        The user's preferences.
    """
    # TODO: do auth by comparing permissions of auth_token to the user being modified (user_id)

    user = db.user.get_user_preferences(user_id)

    return user


@router.patch("/{user_id}/preferences", status_code=status.HTTP_204_NO_CONTENT)
def update_user_preferences(
    user_id: AutoID, data: dict, auth_token: models.TokenPayload = Depends(auth_user)
):
    """Updates a user by its ID.

    Args:
        user_id: The ID of the user to fetch. If "me", will infer a user ID based off the Authorization information.
        data: A mapping of the fields to update to their new values. See `models.UserPreferences` for the valid fields.
            `role_name` is also a valid field to update and will update a user's `roleId` indirectly.
        auth_token: The authentication token provided by the Authorization header.

    Raises:
        HTTPException: 403; if the caller lacks sufficient permissions to modify the specified user.
        HTTPException: 400; if the `data` field is improperly formatted.
    """
    # TODO: do auth by comparing permissions of auth_token to the user being modified (user_id)

    # basic auth potentially
    if auth_token.userId != user_id:
        raise HTTPException(status.HTTP_403_UNAUTHORIZED, "Invalid permissions.")

    try:
        db.user.update_user_preferences(user_id, data)
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get("/{user_id}/projects")
def get_user_projects(
    user_id: AutoID,
    auth_token: models.TokenPayload = Depends(auth_user),
    owner: bool | None = None,
) -> list[models.Project]:
    """Fetches the user's projects.

    Args:
        user_id: The ID of the user to fetch. If "me", will infer a user ID based off the Authorization information.
        auth_token: The authentication token provided by the Authorization header.
        owner: Whether to only return projects the user owns (True), projects they don't own (False), or all projects (None/unset).

    Returns:
        The user's projects.
    """
    # TODO: do auth by comparing permissions of auth_token to the user being modified (user_id) perhaps??

    projects = db.project.get_projects_by_user(user_id)

    return filter(
        lambda p: owner is None or ((p["createdBy"] == user_id) == owner), projects
    )
