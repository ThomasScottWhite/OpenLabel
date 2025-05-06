from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Final

from DataAPI import db, models
from DataAPI.auth_utils import auth_user
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from .. import exceptions as exc

logger = logging.getLogger(__name__)

_section_name: Final[str] = "projects"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


@router.get("")
def get_projects(
    auth_token: models.TokenPayload = Depends(auth_user),
) -> list[models.Project]:
    """Returns all projects.

    Args:
        auth_token: Auth token taken from the Authorization header.
    """
    # TODO: auth here? idk if it needs it
    return db.project.get_all_projects()


class CreateProjectRequest(BaseModel):
    name: str
    description: str
    dataType: models.DataType
    annotationType: models.AnnotationType
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
    """Returns a single project by its ID, including its files and annotations.

    Args:
        project_id: The ID of the project to fetch.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the project does not exist.
    """
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
    """Partially updates a project by ID.

    Args:
        project_id: The ID of the project to update.
        data: A partial update mapping that maps keys to their new values.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 422; if the update is invalid.
        HTTPException: 404; if the specified project does not exist.
    """
    # TODO: auth is in the function for this one

    try:
        db.project.update_project(project_id, data, auth_token.userId)
    except (exc.ResourceNotFound, exc.InvalidPatchMap, exc.ProjectNameExists) as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
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
    """Adds a member to a project.

    Args:
        project_id: The ID of the project to which to add the new member.
        request: The new member information.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 422; if the specified user is already a member.
        HTTPException: 403; if the requesting user does not have permission to add a member.
        HTTPException: 404; if the provided project does not exist.
    """
    # TODO: auth is in the function for this one

    try:
        db.project.add_project_member(
            project_id, request.user_id, request.role_name, auth_token.userId
        )
    except exc.UserAlreadyExists as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except exc.PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get("/{project_id}/members")
def get_project_members(
    project_id: models.ID, auth_token: models.TokenPayload = Depends(auth_user)
) -> list[models.ProjectMemberDetails]:
    """Returns a detailed list of project members for a single project.

    Args:
        project_id: The ID of the project to fetch.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified project does not exist.

    Returns:
        _description_
    """
    # TODO: do auth

    try:
        members = db.project.get_project_members(project_id)

        return members
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get("/{project_id}/files")
def get_project_images(
    project_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
    limit: int = 0,
) -> list[models.FileMeta]:
    """Returns a list of the file meta for all files in a project.

    Args:
        project_id: The project for which to fetch files.
        auth_token: Auth token taken from the Authorization header.
        limit: The maximum number of images to return. If 0, the limit is unset.
            Defaults to 0.

    Raises:
        HTTPException: 404; if the project does not exist.
    """
    # TODO: do auth
    try:
        return db.file.get_files_by_project(project_id, limit)
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.post("/{project_id}/files", status_code=status.HTTP_201_CREATED)
async def upload_files_to_project(
    project_id: models.ID,
    files: list[UploadFile],
    auth_token: models.TokenPayload = Depends(auth_user),
) -> list[models.FileMeta]:
    """Uploads one or more files to a project.

    Args:
        project_id: The project to upload the files to.
        files: The files to upload.
        auth_token: Auth token taken from the Authorization header.

    Returns:
        A list of the generated file meta objects from the uploaded files.
    """
    # TODO: do auth

    prepared_files: list[dict[str, Any]] = []

    for file in files:
        contents = BytesIO(await file.read())
        await file.close()

        prepared_files.append(
            dict(
                file=contents,
                project_id=project_id,
                creator_id=auth_token.userId,
                filename=file.filename,
                content_type=file.content_type,
            )
        )

    return db.file.upload_files(prepared_files)


@router.get("/{project_id}/export")
def get_project_images(
    project_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
    format: models.ExportFormat | None = None,
) -> FileResponse:
    """Exports a project's data (annotations and files) to a ZIP corresponding
    to the specified format.

    Args:
        project_id: The ID of the project to export.
        auth_token: Auth token taken from the Authorization header.
        format: The format to export the project in. If None, the format is inferred based
            on project data type. Defaults to None.

    Raises:
        HTTPException: 404; if the project does not exist
        HTTPException: 422; if the format is None and an export type cannot be inferred.
        HTTPException: 501; if a format is not implemented yet.

    Returns:
        The ZIP file containing the exported data.
    """
    # TODO: do auth
    project = db.project.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")

    if format is None:
        if project.settings.dataType == models.DataType.IMAGE:
            format = models.ExportFormat.COCO
        elif project.settings.dataType == models.DataType.TEXT:
            format = models.ExportFormat.CLASSIFICATION
        else:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Could not infer default export format for project.",
            )

    zip_path: Path | None = None

    try:
        zip_path = db.export.export_project(project_id, format)
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except NotImplementedError as e:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, str(e))

    if zip_path is None:
        raise HTTPException(
            status.HTTP_501_NOT_IMPLEMENTED, "Provided format not implemented."
        )

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=zip_path.name,
        background=BackgroundTask(zip_path.unlink),
    )
