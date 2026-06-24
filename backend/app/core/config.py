from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "quant-trading-app"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    SQLITE_DB_PATH: str = "./quant_trading.db"

    # RAG / LLM 配置
    # Windows + NVIDIA GPU 默认用 transformers + 4-bit 量化
    LLM_BACKEND: str = "transformers"  # mlx | openai | transformers | mock (生产环境严禁mock)
    QWEN_MLX_MODEL_PATH: str = ""  # Qwen3-14B-MLX-4bit 模型路径 (mlx后端, macOS)
    TRANSFORMERS_MODEL_NAME: str = "Qwen/Qwen3-8B"  # HuggingFace模型名称 (transformers后端)
    TRANSFORMERS_LOAD_IN_4BIT: bool = True  # 是否使用4-bit量化 (节省显存)
    EMBEDDING_BACKEND: str = "sentence_transformers"  # sentence_transformers | openai | mock (生产环境严禁mock)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # 回测配置：开发环境无真实数据或策略占位时启用 mock/demo 回退
    BACKTEST_DEMO_FALLBACK: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
