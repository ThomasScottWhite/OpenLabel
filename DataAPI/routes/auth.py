from __future__ import annotations

import logging
from typing import Final

from fastapi import APIRouter

logger = logging.getLogger(__name__)

_section_name: Final[str] = "auth"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


@router.get("/hello")
def hello() -> str:
    return "hello, world!"
