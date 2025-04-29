from typing import Final

from pydantic_settings import BaseSettings


class _Config(BaseSettings):
    # put app config parameters here
    # values will be automatically updated from environment variables
    port: int = 6969

    mongo_uri: str = "mongodb://localhost:27017"
    database_name: str = "openlabel_db"


CONFIG: Final[_Config] = _Config()
