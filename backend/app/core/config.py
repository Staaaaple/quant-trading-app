import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "quant-trading-app"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Render 使用 /tmp 目录（可写），本地开发使用当前目录
    SQLITE_DB_PATH: str = os.environ.get("SQLITE_DB_PATH", "./quant_trading.db")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
