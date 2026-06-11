"""向量存储 — FAISS 实现.

支持:
- 内存索引 (FAISS IndexFlatIP / IndexFlatL2)
- 持久化存储 (pickle 保存/加载)
- 增量添加/删除
- 元数据过滤

后续可扩展支持 pgvector / Milvus.
"""

import os
import json
import pickle
from typing import Any
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class VectorItem:
    """向量存储项."""

    id: str
    embedding: np.ndarray
    metadata: dict[str, Any]
    text: str  # 原始文本


class VectorStore:
    """FAISS 向量存储."""

    def __init__(
        self,
        dimension: int = 384,
        index_type: str = "flat_ip",  # flat_ip (内积) 或 flat_l2 (欧氏距离)
        persist_dir: str | None = None,
    ):
        """初始化向量存储.

        Args:
            dimension: 向量维度
            index_type: "flat_ip" | "flat_l2"
            persist_dir: 持久化目录, None 则不持久化
        """
        self.dimension = dimension
        self.index_type = index_type
        self.persist_dir = persist_dir

        self._index: Any = None
        self._items: list[VectorItem] = []
        self._id_to_idx: dict[str, int] = {}

        self._faiss_available = self._check_faiss()

    def _check_faiss(self) -> bool:
        """检查 FAISS 是否可用."""
        try:
            import faiss

            return True
        except ImportError:
            return False

    def _create_index(self) -> Any:
        """创建 FAISS 索引."""
        if not self._faiss_available:
            raise ImportError(
                "faiss-cpu 未安装. 运行: pip install faiss-cpu"
            )

        import faiss

        if self.index_type == "flat_ip":
            # 内积索引 (需归一化向量, 等价于余弦相似度)
            return faiss.IndexFlatIP(self.dimension)
        elif self.index_type == "flat_l2":
            return faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "flat_ip_idmap":
            # 带 ID 映射的内积索引，支持 add_with_ids
            base = faiss.IndexFlatIP(self.dimension)
            return faiss.IndexIDMap2(base)
        else:
            raise ValueError(f"不支持的索引类型: {self.index_type}")

    def _ensure_index(self) -> None:
        """确保索引已创建."""
        if self._index is None:
            self._index = self._create_index()

    def add_items(
        self,
        ids: list[str],
        embeddings: np.ndarray,
        metadatas: list[dict[str, Any]] | None = None,
        texts: list[str] | None = None,
    ) -> None:
        """批量添加向量.

        Args:
            ids: 唯一标识列表
            embeddings: 向量数组 (n, dimension)
            metadatas: 元数据列表
            texts: 原始文本列表
        """
        self._ensure_index()

        if len(ids) != len(embeddings):
            raise ValueError("ids 和 embeddings 长度不一致")

        metadatas = metadatas or [{} for _ in ids]
        texts = texts or ["" for _ in ids]

        # 归一化 (内积索引需要)
        if self.index_type == "flat_ip":
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            embeddings = embeddings / norms

        # 保存元数据
        start_idx = len(self._items)

        # 添加到 FAISS
        if self.index_type == "flat_ip_idmap":
            # 使用 IDMap 索引，支持 add_with_ids
            import faiss
            # 将字符串 ID 映射为整数 ID
            int_ids = np.array([start_idx + i for i in range(len(ids))], dtype=np.int64)
            self._index.add_with_ids(embeddings.astype(np.float32), int_ids)
        else:
            self._index.add(embeddings.astype(np.float32))
        for i, (id_, emb, meta, text) in enumerate(zip(ids, embeddings, metadatas, texts)):
            if id_ in self._id_to_idx:
                raise ValueError(f"重复 ID: {id_}")

            self._id_to_idx[id_] = start_idx + i
            self._items.append(
                VectorItem(
                    id=id_,
                    embedding=emb,
                    metadata=meta,
                    text=text,
                )
            )

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_dict: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """相似度检索.

        Args:
            query_embedding: 查询向量 (dimension,)
            top_k: 返回结果数
            filter_dict: 元数据过滤条件 {key: value}

        Returns:
            [{"id": str, "score": float, "metadata": dict, "text": str}, ...]
        """
        self._ensure_index()

        if len(self._items) == 0:
            return []

        # 归一化查询向量
        if self.index_type == "flat_ip":
            query_embedding = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)

        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)

        # FAISS 检索
        scores, indices = self._index.search(query_embedding, min(top_k * 3, len(self._items)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._items):
                continue

            item = self._items[idx]

            # 元数据过滤
            if filter_dict:
                match = True
                for key, value in filter_dict.items():
                    if item.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            results.append({
                "id": item.id,
                "score": float(score),
                "metadata": item.metadata,
                "text": item.text,
            })

            if len(results) >= top_k:
                break

        return results

    def delete(self, id_: str) -> bool:
        """删除向量（标记删除, 不重建索引）."""
        if id_ not in self._id_to_idx:
            return False

        idx = self._id_to_idx[id_]
        self._items[idx] = VectorItem(
            id="__deleted__",
            embedding=np.zeros(self.dimension),
            metadata={},
            text="",
        )
        del self._id_to_idx[id_]
        return True

    def get(self, id_: str) -> dict[str, Any] | None:
        """获取指定 ID 的向量."""
        if id_ not in self._id_to_idx:
            return None

        item = self._items[self._id_to_idx[id_]]
        return {
            "id": item.id,
            "metadata": item.metadata,
            "text": item.text,
        }

    def count(self) -> int:
        """获取有效向量数量."""
        return sum(1 for item in self._items if item.id != "__deleted__")

    def save(self, name: str) -> str:
        """保存索引到磁盘.

        Args:
            name: 索引名称

        Returns:
            保存路径
        """
        if self.persist_dir is None:
            raise ValueError("persist_dir 未设置")

        dir_path = Path(self.persist_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        save_path = dir_path / f"{name}.pkl"

        data = {
            "dimension": self.dimension,
            "index_type": self.index_type,
            "items": self._items,
            "id_to_idx": self._id_to_idx,
        }

        with open(save_path, "wb") as f:
            pickle.dump(data, f)

        return str(save_path)

    def load(self, name: str) -> bool:
        """从磁盘加载索引.

        Args:
            name: 索引名称

        Returns:
            是否成功加载
        """
        if self.persist_dir is None:
            return False

        load_path = Path(self.persist_dir) / f"{name}.pkl"
        if not load_path.exists():
            return False

        with open(load_path, "rb") as f:
            data = pickle.load(f)

        self.dimension = data["dimension"]
        self.index_type = data["index_type"]
        self._items = data["items"]
        self._id_to_idx = data["id_to_idx"]

        # 重建 FAISS 索引
        self._index = self._create_index()

        valid_embeddings = []
        for item in self._items:
            if item.id != "__deleted__":
                valid_embeddings.append(item.embedding)

        if valid_embeddings:
            embeddings = np.array(valid_embeddings, dtype=np.float32)
            if self.index_type in ("flat_ip", "flat_ip_idmap"):
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms = np.where(norms == 0, 1, norms)
                embeddings = embeddings / norms
            if self.index_type == "flat_ip_idmap":
                import faiss
                int_ids = np.array([i for i, item in enumerate(self._items) if item.id != "__deleted__"], dtype=np.int64)
                self._index.add_with_ids(embeddings, int_ids)
            else:
                self._index.add(embeddings)

        return True

    def exists(self, name: str) -> bool:
        """检查索引是否存在."""
        if self.persist_dir is None:
            return False
        return (Path(self.persist_dir) / f"{name}.pkl").exists()


# 全局存储实例
_store_instances: dict[str, VectorStore] = {}


def get_vector_store(name: str = "default", **kwargs) -> VectorStore:
    """获取或创建向量存储实例.

    Args:
        name: 存储名称
        **kwargs: VectorStore 构造参数

    Returns:
        VectorStore 实例
    """
    if name not in _store_instances:
        persist_dir = kwargs.get("persist_dir")
        if persist_dir is None:
            # 默认持久化目录
            base_dir = Path(__file__).parent.parent.parent.parent / "data" / "vector_stores"
            base_dir.mkdir(parents=True, exist_ok=True)
            kwargs["persist_dir"] = str(base_dir)

        _store_instances[name] = VectorStore(**kwargs)

    return _store_instances[name]
