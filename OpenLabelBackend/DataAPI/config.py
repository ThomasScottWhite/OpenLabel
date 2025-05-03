from typing import Final

from pydantic_settings import BaseSettings


class _Config(BaseSettings):
    # put app config parameters here
    # values will be automatically updated from environment variables
    port: int = 6969

    mongo_uri: str = "mongodb://localhost:27017"
    database_name: str = "openlabel_db"
    auth_secret_key: str = "notverysecretkey"  # override this in env variables


CONFIG: Final[_Config] = _Config()
