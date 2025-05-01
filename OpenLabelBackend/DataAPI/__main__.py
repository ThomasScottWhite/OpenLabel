import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)

import argparse

import uvicorn
from DataAPI.config import CONFIG

parser = argparse.ArgumentParser()

parser.add_argument(
    "-p",
    "--port",
    type=int,
    default=None,
    help="Override app port",
    choices=range(0, 2**16),
)
parser.add_argument(
    "-r", "--reload", help="Toggle app auto reloading on changes", action="store_true"
)

args = parser.parse_args()

if args.port is not None:
    CONFIG.port = args.port


from DataAPI.app import APP

# note: if you want to modify config before initializing the app object, do so
#       before importing APP

app = APP

if args.reload:
    logger.warning(
        "When using --reload, any config parameters overrided by command line arguments will not be recognized in the running app!"
    )
    app = "DataAPI.app:APP"


uvicorn.run(app, host="127.0.0.1", port=CONFIG.port, reload=args.reload)
