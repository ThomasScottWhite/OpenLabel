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

_section_name: Final[str] = "images"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


def create_project(
    auth_token: models.TokenPayload = Depends(auth_user),
) -> list[models.Project]:
    pass


@router.get("/{image_id}")
def get_image_meta(
    image_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> models.ImageMeta:
    """Fetches the metadata for image with ID `image_id`.

    Args:
        image_id: The ID of the image for which to fetch metadata.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified image does not exist

    Returns:
        The image meta.
    """
    # TODO: auth (may have to dig into project roles, etc.)

    meta = db.image.get_image_by_id(image_id)

    if not meta:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Image with ID '{str(image_id)}' not found"
        )

    # TODO: put the auth here, probably, since meta gives you a project ID

    return meta


@router.delete("/{image_id}", status_code=status.HTTP_201_CREATED)
def delete_image(
    image_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
):
    """Deletes an image from the database.

    Args:
        image_id: The ID of the image to delete.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified image does not exist.
    """
    # TODO: auth (may have to dig into project roles, etc.)

    try:
        db.image.delete_image(image_id)
    except exc.ResourceNotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


class ImageDownload(BaseModel):
    data: str
    metadata: models.ImageMeta


@router.get("/{image_id}/download")
def download_image(
    image_id: models.ID,
    auth_token: models.TokenPayload = Depends(auth_user),
) -> ImageDownload:
    """Download the specified image and its corresponding metadata.

    Args:
        image_id: The ID of the image to download.
        auth_token: Auth token taken from the Authorization header.

    Raises:
        HTTPException: 404; if the specified image does not exist.

    Returns:
        A JSON payload containing a base64-encoded image (the `data` field) and
        the image's metadata (a metadata object).
    """
    # TODO: auth (may have to dig into project roles, etc.)

    download = db.image.download_image(image_id)

    if download is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Image with ID '{str(image_id)}' not found"
        )

    data, meta = download

    encoded_data = base64.b64encode(data.getvalue()).decode()

    return ImageDownload(data=encoded_data, metadata=meta)
