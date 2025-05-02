from __future__ import annotations

import logging
from typing import Final

from DataAPI import db
from DataAPI.auth_utils import auth_user
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel

from .. import exceptions as exc
from .. import models

logger = logging.getLogger(__name__)

_section_name: Final[str] = "annotations"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


def create_project(
    auth_token: models.TokenPayload = Depends(auth_user),
) -> list[models.Project]:
    pass


@router.post("")
def upload_files(file: list[UploadFile]):
    print(file)
