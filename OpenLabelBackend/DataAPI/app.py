from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Final

from fastapi import FastAPI

from DataAPI.routes import ROUTERS


from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info("Starting app...")

    yield

    logger.info("Closing app...")
    # shutdown


APP: Final[FastAPI] = FastAPI(lifespan=lifespan)

for router in ROUTERS:
    APP.include_router(router)
