from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "quant-trading-app"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    SQLITE_DB_PATH: str = "./quant_trading.db"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
