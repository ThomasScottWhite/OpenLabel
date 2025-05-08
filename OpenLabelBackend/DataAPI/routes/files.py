from __future__ import annotations

import base64
import logging
from typing import Final

from DataAPI import db
from DataAPI.auth_utils import auth_user
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel

from .. import exceptions as exc
from .. import models

logger = logging.getLogger(__name__)

_section_name: Final[str] = "files"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


@router.get("/{file_id}")
def get_file_meta(
    file_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> models.FileMeta:
    """Fetches the metadata for file with ID `file_id`.

    Args:
        file_id: The ID of the file for which to fetch metadata.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified file does not exist

    Returns:
        The file meta.
    """
    # TODO: auth (may have to dig into project roles, etc.)

    meta = db.file.get_file_by_id(file_id)

    if not meta:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"File with ID '{str(file_id)}' not found"
        )

    # TODO: put the auth here, probably, since meta gives you a project ID

    return meta


@router.delete("/{file_id}")
def delete_image(
    file_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
):
    """Deletes an file from the database.

    Args:
        file_id: The ID of the file to delete.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified file does not exist.
    """
    # TODO: auth (may have to dig into project roles, etc.)

    try:
        db.file.delete_file(file_id)
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get("/{file_id}/download")
def download_file(
    file_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> models.File:
    """Download the specified file and its corresponding metadata.

    Args:
        file_id: The ID of the file to download.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified file does not exist.

    Returns:
        A JSON payload containing a base64-encoded file (the `data` field) and
        the file's metadata (a metadata object).
    """
    # TODO: auth (may have to dig into project roles, etc.)

    download = db.file.download_file(file_id)

    if download is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Image with ID '{str(file_id)}' not found"
        )

    data, meta = download

    encoded_data = None
    if meta.contentType.startswith("image"):
        encoded_data = base64.b64encode(data.getvalue()).decode()
    elif meta.contentType.startswith("text"):
        encoded_data = data.getvalue().decode("utf-8")

    annotations = db.annotation.get_annotations_by_file(file_id)

    return models.File(data=encoded_data, metadata=meta, annotations=annotations)


@router.get("/{file_id}/annotations")
def get_file_annotations(
    file_id: models.ID,
    limit: int = 0,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> list[models.Annotation]:
    """Returns a list of a file's annotations.

    Args:
        file_id: The ID of the file for which to fetch anotations.
        limit: The maximum number of annotations to fetch. If 0, the limit is unset.
            Defaults to 0.
        auth_token: Auth token taken from the Authorization header.

    Returns:
        A list of annotations for the file
    """
    # TODO: auth?

    return db.annotation.get_annotations_by_file(file_id, limit)


@router.post("/{file_id}/annotations", status_code=status.HTTP_201_CREATED)
def create_file_annotation(
    file_id: models.ID,
    annotation: models.CreateAnnotation,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> models.HasAnnotationID:
    """Creates an annotation for a file.

    Args:
        file_id: The file for which to create the annotation.
        annotation: The annotation data.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified file does not exist.

    Returns:
        The ID of the created annotation.
    """
    # TODO: auth?

    file_meta = db.file.get_file_by_id(file_id)

    if file_meta is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Image with ID '{str(file_id)}' not found"
        )

    annotation_id: models.ID

    if annotation.type == models.AnnotationType.CLASSIFICATION:
        annotation_id = db.annotation.create_classification_annotation(
            file_id=file_id,
            project_id=file_meta.projectId,
            created_by=auth_token.userId,
            label=annotation.label,
        )
    elif annotation.type == models.AnnotationType.OBJECT_DETECTION:
        annotation_id = db.annotation.create_object_detection_annotation(
            file_id=file_id,
            project_id=file_meta.projectId,
            created_by=auth_token.userId,
            label=annotation.label,
            bbox=annotation.bbox,
        )
    elif annotation.type == models.AnnotationType.SEGMENTATION:
        annotation_id = db.annotation.create_segmentation_annotation(
            file_id=file_id,
            project_id=file_meta.projectId,
            created_by=auth_token.userId,
            label=annotation.label,
            points=annotation.points,
        )

    return models.HasAnnotationID(annotationId=annotation_id)
