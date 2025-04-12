from typing import Final

from pydantic_settings import BaseSettings


class _Config(BaseSettings):
    # put app config parameters here
    # values will be automatically updated from environment variables
    port: int = 6970


CONFIG: Final[_Config] = _Config()
