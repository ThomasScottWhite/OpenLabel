from __future__ import annotations

import logging
from io import BytesIO
from typing import Final

from DataAPI import db
from DataAPI.auth_utils import auth_user
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from PIL import Image
from pydantic import BaseModel

from .. import exceptions as exc
from .. import models

logger = logging.getLogger(__name__)

_section_name: Final[str] = "projects"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


class CreateProjectRequest(BaseModel):
    name: str
    description: str
    data_type: models.DataType
    annotation_type: str
    is_public: bool


@router.get("", status_code=status.HTTP_201_CREATED)
def get_project(
    auth_token: models.TokenPayload = Depends(auth_user),
) -> list[models.Project]:
    # TODO: auth here? idk if it needs it
    return db.project.get_all_projects()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest, auth_token: models.TokenPayload = Depends(auth_user)
) -> str:
    """Creates a new project.

    Args:
        request: The specifications of the new project.
        auth_token: The authentication token provided by the Authorization header.

    Raises:
        HTTPException: 400; if the specified name has already been taken for the creating user.

    Returns:
        The created project's ID.
    """

    try:
        project_id = db.project.create_project(
            name=request.name,
            description=request.description,
            data_type=request.data_type,
            annotation_type=request.annotation_type,
            is_public=request.is_public,
            created_by=auth_token.userId,
        )
        return str(project_id)
    except exc.ProjectNameExists as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/{project_id}")
def get_project_by_id(
    project_id: models.ID, auth_token: models.TokenPayload = Depends(auth_user)
) -> models.Project:
    # TODO: authentication?? should the user have to be part of the project to see it??

    project = db.project.get_project_by_id(project_id)

    project = models.Project.model_validate(project)

    # potential auth???
    for member in project.members:
        if member.userId == auth_token.userId:
            break
    else:  # only runs if loop doesn't break (i.e., if auth user is not in members)
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Insufficient permissions to view this object."
        )

    return project


@router.patch("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_project_by_id(
    project_id: models.ID,
    data: dict,
    auth_token: models.TokenPayload = Depends(auth_user),
):
    # TODO: auth is in the function for this one

    try:
        db.project.update_project(project_id, data, auth_token.userId)
    except (exc.ResourceNotFound, exc.InvalidPatchMap, exc.ProjectNameExists) as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except exc.PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))


class CreateProjectMemberRequest(BaseModel):
    user_id: models.ID
    role_name: str


@router.post("/{project_id}/members", status_code=status.HTTP_201_CREATED)
def add_member_to_project(
    project_id: models.ID,
    request: CreateProjectMemberRequest,
    auth_token: models.TokenPayload = Depends(auth_user),
):
    # TODO: auth is in the function for this one

    try:
        db.project.add_project_member(
            project_id, request.user_id, request.role_name, auth_token.userId
        )
    except (exc.InvalidPatchMap, exc.UserAlreadyExists) as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except exc.PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get("/{project_id}/members")
def get_project_members(
    project_id: models.ID, auth_token: models.TokenPayload = Depends(auth_user)
) -> list[models.ProjectMemberDetails]:
    # TODO: do auth

    try:
        members = db.project.get_project_members(project_id)
        for member in members:
            member["role"]["roleId"] = member["role"].pop("_id")

        return members
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get("/{project_id}/images")
def get_project_images(
    project_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
    limit: int = 0,
) -> list[models.ImageMeta]:
    # TODO: do auth

    try:
        return db.image.get_images_by_project(project_id, limit)
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.post("/{project_id}/images")
async def upload_image_to_project(
    project_id: models.ID,
    file: UploadFile,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> list[models.ImageMeta]:
    # TODO: do auth

    if not file.content_type.startswith("image"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image types are allowed.",
        )

    contents = await file.read()

    try:
        image = Image.open(BytesIO(contents))
        width, height = image.size
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process the image.",
        )

    db.image.upload_image(
        BytesIO(contents),
        project_id,
        auth_token.userId,
        file.filename,
        width,
        height,
        file.content_type,
    )
