from typing import Final
import os
from pydantic_settings import BaseSettings

# Modify the environment variable to set the test database
os.environ["DB_TEST"] = "1"
class _Config(BaseSettings):

    DB_TEST: bool = os.getenv("DB_TEST", "0") == "1"

    mongo_url: str = None
    database_name: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.DB_TEST:
            self.mongo_uri = "mongodb://localhost:27017/test_db" 
            self.database_name = "test_db"
        else:
            self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/openlabel_db")
            self.database_name = os.getenv("DB_NAME", "openlabel_db")

CONFIG: Final[_Config] = _Config()
