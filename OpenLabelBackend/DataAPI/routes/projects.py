from __future__ import annotations

import logging
from typing import Final

from fastapi import APIRouter

from DataAPI import db

logger = logging.getLogger(__name__)

_section_name: Final[str] = "projects"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


@router.post("/hello")
def hello() -> str:
    return "hello, world!"
