"""Embedding 服务 — 文本向量化.

支持多种 Embedding 后端:
- sentence-transformers (本地, 默认)
- OpenAI API (云端)
- 其他兼容 OpenAI 接口的模型

部署时通过环境变量 EMBEDDING_BACKEND 切换.
"""

import os
import asyncio
from typing import Any
from functools import lru_cache

import numpy as np

from app.core.config import settings


class EmbeddingService:
    """Embedding 服务统一接口."""

    def __init__(self, backend: str | None = None, model_name: str | None = None):
        """初始化 Embedding 服务.

        Args:
            backend: "sentence_transformers" | "openai" | "mock"
            model_name: 模型名称, backend 为 None 时使用默认
        """
        self.backend = backend or settings.EMBEDDING_BACKEND or os.getenv("EMBEDDING_BACKEND", "mock")
        self.model_name = model_name or settings.EMBEDDING_MODEL or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self._model: Any = None
        self._dim: int = 384  # 默认维度 (all-MiniLM-L6-v2)

    def _load_model(self) -> None:
        """懒加载模型."""
        if self._model is not None:
            return

        if self.backend == "sentence_transformers":
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                self._dim = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers 未安装. 运行: pip install sentence-transformers"
                )

        elif self.backend == "openai":
            try:
                import openai

                self._model = openai
                # text-embedding-3-small 维度 1536
                self._dim = 1536
            except ImportError:
                raise ImportError("openai 未安装. 运行: pip install openai")

        elif self.backend == "mock":
            # Mock模式: 返回随机向量(仅用于测试)
            self._model = "mock"
            self._dim = 384

        else:
            raise ValueError(
                f"不支持的 Embedding backend: {self.backend}. "
                f"支持的backend: sentence_transformers, openai, mock. "
            )

    @property
    def dimension(self) -> int:
        """获取向量维度."""
        self._load_model()
        return self._dim

    def encode(self, texts: str | list[str]) -> np.ndarray:
        """将文本编码为向量.

        Args:
            texts: 单个文本或文本列表

        Returns:
            向量数组, shape: (n_texts, dimension)
        """
        self._load_model()

        if isinstance(texts, str):
            texts = [texts]

        if self.backend == "sentence_transformers":
            embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return np.array(embeddings, dtype=np.float32)

        elif self.backend == "openai":
            return self._encode_openai(texts)

        elif self.backend == "mock":
            return self._encode_mock(texts)

        else:
            raise ValueError(
                f"不支持的 backend: {self.backend}. "
            )

    async def encode_async(self, texts: str | list[str]) -> np.ndarray:
        """异步编码（在线程池中执行）."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.encode, texts)

    def _encode_openai(self, texts: list[str]) -> np.ndarray:
        """OpenAI API 编码."""
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 环境变量未设置")

        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model=self.model_name,
            input=texts,
        )
        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings, dtype=np.float32)

    def _encode_mock(self, texts: list[str]) -> np.ndarray:
        """Mock 编码 — 基于文本哈希的确定性向量."""
        embeddings = []
        for text in texts:
            # 使用文本哈希生成确定性向量
            np.random.seed(hash(text) % (2**32))
            vec = np.random.randn(self._dim).astype(np.float32)
            vec = vec / np.linalg.norm(vec)  # 归一化
            embeddings.append(vec)
        return np.array(embeddings, dtype=np.float32)


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """获取全局 Embedding 服务实例（单例）."""
    return EmbeddingService()
