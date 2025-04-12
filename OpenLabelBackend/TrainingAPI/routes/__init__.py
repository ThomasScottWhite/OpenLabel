import importlib
import logging
from pathlib import Path
from typing import Final

from fastapi import APIRouter

ROUTERS: Final[list[APIRouter]] = []

logger = logging.getLogger(__name__)

logger.debug("Loading routes...")

_this_file = Path(__file__)
_package_name = f"{_this_file.parents[1].stem}.{_this_file.parent.stem}"

for path in _this_file.parent.iterdir():
    # only load python files, ignoring those with "magic" names
    module_name = path.stem
    if (
        not path.is_file()
        or not path.suffix.lower() == ".py"
        or module_name.startswith("__")
    ):
        continue

    logger.debug(f"Loading module {_package_name}.{module_name}")
    mod = importlib.import_module(f".{module_name}", package=_package_name)

    if "router" in dir(mod):
        ROUTERS.append(mod.router)
    else:
        logger.warning(f"Failed to load module {_package_name}.{module_name}")
