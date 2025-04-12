from __future__ import annotations

import logging
from typing import Final

from fastapi import APIRouter

from TrainingAPI import db, models

logger = logging.getLogger(__name__)

_section_name: Final[str] = "example"

router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


@router.get("/hello")
def hello() -> str:
    return "hello, world!"
