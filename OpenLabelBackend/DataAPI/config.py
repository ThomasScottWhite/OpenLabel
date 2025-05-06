import secrets
from pathlib import Path
from typing import Final

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Config(BaseSettings):
    # put app config parameters here
    # values will be automatically updated from environment variables
    port: int = 6969

    mongo_uri: str = "mongodb://localhost:27017"
    database_name: str = "openlabel_db"
    auth_secret_key: str = secrets.token_urlsafe(32)
    temp_dir: str = str((Path(__file__).parent / "temp").resolve())

    # TODO: (optional) get env file setup
    # model_config = SettingsConfigDict(env_file=Path("insert_path_here"))


CONFIG: Final[_Config] = _Config()
