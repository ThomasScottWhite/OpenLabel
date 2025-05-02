import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)
logging.getLogger("pymongo").setLevel("INFO")

import argparse
import sys

import uvicorn
from DataAPI.config import CONFIG
from fastapi import FastAPI

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
parser.add_argument(
    "--populate-test-data",
    help="Populate the database with test data.",
    action="store_true",
)

args = parser.parse_args()

if args.populate_test_data:
    from . import test

    test.init_test_data()
    sys.exit()

if args.port is not None:
    CONFIG.port = args.port


# note: if you want to modify config before initializing the app object, do so
#       before importing APP

app: FastAPI | str | None = None

if args.reload:
    logger.warning(
        "When using --reload, any config parameters overrided by command line arguments will not be recognized in the running app!"
    )
    app = "DataAPI.app:APP"
else:
    from DataAPI.app import APP

    app = APP


uvicorn.run(app, host="127.0.0.1", port=CONFIG.port, reload=args.reload)
