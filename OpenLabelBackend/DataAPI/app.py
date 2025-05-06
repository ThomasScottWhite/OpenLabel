from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Final

from fastapi import FastAPI
from rich.logging import RichHandler

from .config import CONFIG
from .routes import ROUTERS

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info("Starting app...")
    temp_dir = Path(CONFIG.temp_dir)

    logger.debug(f"Creating temp dir: {CONFIG.temp_dir}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    yield

    logger.debug(f"Cleaning temp dir: {CONFIG.temp_dir}")
    if temp_dir.exists():
        for path in temp_dir.iterdir():
            path.unlink()

    logger.info("Closing app...")
    # shutdown


APP: Final[FastAPI] = FastAPI(lifespan=lifespan)

for router in ROUTERS:
    APP.include_router(router)
