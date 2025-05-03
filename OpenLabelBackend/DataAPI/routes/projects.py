from __future__ import annotations

import logging
from io import BytesIO
from typing import Any, Final

from DataAPI import db
from DataAPI.auth_utils import auth_user
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel

from .. import exceptions as exc
from DataAPI import models

logger = logging.getLogger(__name__)

_section_name: Final[str] = "projects"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


@router.get("")
def get_projects(
    auth_token: models.TokenPayload = Depends(auth_user),
) -> list[models.Project]:
    # TODO: auth here? idk if it needs it
    return db.project.get_all_projects()


class CreateProjectRequest(BaseModel):
    name: str
    description: str
    dataType: models.DataType
    annotationType: models.ProjectAnnotationType
    isPublic: bool
    labels: list[str]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest, auth_token: models.TokenPayload = Depends(auth_user)
) -> models.HasProjectID:
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
            data_type=request.dataType,
            annotation_type=request.annotationType,
            is_public=request.isPublic,
            created_by=auth_token.userId,
        )
        return models.HasProjectID(projectId=project_id)
    except exc.ProjectNameExists as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/{project_id}")
def get_project_by_id(
    project_id: models.ID, auth_token: models.TokenPayload = Depends(auth_user)
) -> models.ProjectWithFiles:
    # TODO: authentication?? should the user have to be part of the project to see it??

    project = db.project.get_project_by_id(project_id)

    if project is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Project with ID {str(project_id)} does not exist.",
        )

    files = db.file.get_files_by_project(project_id)

    # # potential auth???
    # for member in project.members:
    #     if member.userId == auth_token.userId:
    #         break
    # else:  # only runs if loop doesn't break (i.e., if auth user is not in members)
    #     raise HTTPException(
    #         status.HTTP_403_FORBIDDEN, "Insufficient permissions to view this object."
    #     )

    return dict(**project.model_dump(), files=files)


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


@router.get("/{project_id}/files")
def get_project_images(
    project_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
    limit: int = 0,
) -> list[models.FileMeta]:
    # TODO: do auth

    try:
        return db.file.get_files_by_project(project_id, limit)
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.post("/{project_id}/files", status_code=status.HTTP_201_CREATED)
async def upload_images_to_project(
    project_id: models.ID,
    files: list[UploadFile],
    auth_token: models.TokenPayload = Depends(auth_user),
) -> list[models.FileMeta]:
    # TODO: do auth

    images: list[dict[str, Any]] = []

    for file in files:
        contents = BytesIO(await file.read())
        await file.close()

        images.append(
            dict(
                file=contents,
                project_id=project_id,
                creator_id=auth_token.userId,
                filename=file.filename,
                content_type=file.content_type,
            )
        )
        db.file.upload_file()

    return db.file.upload_files(images)
