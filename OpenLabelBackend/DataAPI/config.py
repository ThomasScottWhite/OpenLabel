from typing import Final
import os
from pydantic_settings import BaseSettings

# Modify the environment variable to set the test database
class _Config(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    database_name: str = "openlabel_db"


CONFIG: Final[_Config] = _Config()
