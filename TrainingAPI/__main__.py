import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)

import uvicorn

from TrainingAPI.app import APP
from TrainingAPI.config import CONFIG

# note: if you want to modify config before initializing the app object, do so
#       before importing APP


uvicorn.run(APP, host="127.0.0.1", port=CONFIG.port)
