from __future__ import annotations

import logging
from typing import Final

from DataAPI import db
from DataAPI.auth_utils import auth_user
from fastapi import APIRouter, Depends, HTTPException, status

from .. import exceptions as exc
from .. import models

logger = logging.getLogger(__name__)

_section_name: Final[str] = "annotations"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


@router.get("/{annotation_id}")
def get_annotation(
    annotation_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> models.Annotation:
    """Fetches the metadata for annotation with ID `annotation_id`.

    Args:
        annotation_id: The ID of the annotation to fetch.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified annotation does not exist

    Returns:
        The annotation.
    """
    # TODO: auth (may have to dig into project roles, etc.)

    annotation = db.annotation.get_annotation_by_id(annotation_id)

    if not annotation:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"annotation with ID '{str(annotation_id)}' not found",
        )

    # TODO: put the auth here, probably, since annotation gives you a project ID, etc.

    return annotation


@router.delete("/{annotation_id}", status_code=status.HTTP_201_CREATED)
def delete_annotation(
    annotation_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
):
    """Deletes an annotation from the database.

    Args:
        annotation_id: The ID of the annotation to delete.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified annotation does not exist.
    """
    # TODO: auth (may have to dig into project roles, etc.)

    try:
        db.annotation.delete_annotation(annotation_id)
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.patch("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_annotation(
    annotation_id: models.ID,
    update_data: models.UpdateAnnotation,
    auth_token: models.TokenPayload = Depends(auth_user),
):
    """Updates a single annotation.

    Args:
        annotation_id: The ID of the annotation to update.
        update_data: A mapping of partial updates to the annotation. If an invalid configuration is presented,
            a 422 error will be raised (e.g., you can't have a bbox and polygon at the same time).
        auth_token: Auth token taken from the Authorization header.
    """
    # TODO: auth (may have to dig into project roles, etc.)

    db.annotation.update_annotation(annotation_id, update_data)
