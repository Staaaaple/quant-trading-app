from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "quant-trading-app"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    SQLITE_DB_PATH: str = "./quant_trading.db"

    # RAG / LLM 配置
    LLM_BACKEND: str = "mlx"  # mlx | openai | mock (生产环境严禁mock)
    QWEN_MLX_MODEL_PATH: str = ""  # Qwen3-14B-MLX-4bit 模型路径
    EMBEDDING_BACKEND: str = "sentence_transformers"  # sentence_transformers | openai | mock (生产环境严禁mock)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
