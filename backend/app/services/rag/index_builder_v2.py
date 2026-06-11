"""索引构建器V2 — 支持六大知识源.

构建FAISS向量索引，支持：
- 个股分析案例
- 资产配置理论
- 基础金融常识
- 估值案例
- 行为金融案例
- 论文片段

直接从YAML文件构建索引，不依赖数据库schema。
"""

import os
import yaml
from typing import Any
from pathlib import Path
from sqlalchemy.orm import Session

from .embedding_service import EmbeddingService, get_embedding_service
from .vector_store import VectorStore, get_vector_store


class IndexBuilderV2:
    """新版索引构建器 - 六大知识源."""

    INDEX_NAMES = {
        "stock_cases": "stock_case_index",
        "allocation_theory": "allocation_theory_index",
        "finance_basics": "finance_basic_index",
        "valuation_cases": "valuation_case_index",
        "behavioral_cases": "behavioral_case_index",
        "paper_chunks": "paper_chunk_index",
        "allocation_cases": "allocation_case_index",
        "risk_control_cases": "risk_control_case_index",
        "strategy_binding_cases": "strategy_binding_case_index",
    }

    # YAML文件所在目录名
    DATA_DIRS = {
        "stock_cases": "stock_cases",
        "allocation_theory": "allocation_theory",
        "finance_basics": "finance_basics",
        "valuation_cases": "valuation_cases",
        "behavioral_cases": "behavioral_cases",
        "paper_chunks": "paper_chunks",
        "allocation_cases": "allocation_cases",
        "risk_control_cases": "risk_control_cases",
        "strategy_binding_cases": "strategy_binding_cases",
    }

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        data_dir: Path | None = None,
    ):
        self.embedding = embedding_service or get_embedding_service()
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent.parent / "data" / "knowledge"
        else:
            self.data_dir = data_dir

    def _get_store(self, name: str) -> VectorStore:
        """获取或创建向量存储实例."""
        return get_vector_store(
            name=name,
            dimension=self.embedding.dimension,
        )

    def _load_yaml_files(self, subdir: str) -> list[dict[str, Any]]:
        """加载指定目录下的所有YAML文件."""
        dir_path = self.data_dir / subdir
        if not dir_path.exists():
            return []

        items = []
        for file_path in sorted(dir_path.glob("*.yaml")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    items.append(data)
            except Exception as e:
                print(f"Warning: failed to load {file_path}: {e}")
        return items

    def _extract_text_from_yaml(self, data: dict[str, Any]) -> str:
        """从YAML数据中提取可嵌入的文本内容."""
        parts = []

        # 通用字段
        for key in ["id", "symbol", "name", "topic", "bias_name", "paper_title", "case_type"]:
            if key in data and data[key]:
                parts.append(f"{key}: {data[key]}")

        # 长文本字段
        for key in ["summary", "explanation", "abstract_summary", "lesson_summary",
                    "valuation_methodology", "outcome", "real_world_example",
                    "impact_on_investment", "mitigation_strategy", "content",
                    "key_factors", "risk_factors", "key_concepts", "practical_application",
                    "limitations", "methodology", "implications", "key_findings",
                    "key_assumptions"]:
            if key in data and data[key]:
                value = data[key]
                if isinstance(value, str):
                    parts.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                if isinstance(v, str):
                                    parts.append(v)
                                else:
                                    parts.append(str(v))
                        elif isinstance(item, str):
                            parts.append(item)
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if isinstance(v, str):
                            parts.append(v)

        return "\n".join(parts)

    def _extract_metadata(self, data: dict[str, Any], attrs: list[str]) -> dict[str, Any]:
        """从YAML数据中提取元数据."""
        metadata = {}
        for attr in attrs:
            if attr in data and data[attr] is not None:
                value = data[attr]
                # 确保元数据可JSON序列化
                if isinstance(value, (str, int, float, bool)):
                    metadata[attr] = value
                elif isinstance(value, list):
                    metadata[attr] = ", ".join(str(v) for v in value[:5])  # 限制长度
                else:
                    metadata[attr] = str(value)[:100]  # 限制长度
        return metadata

    def _build_index_from_yaml(
        self,
        source_name: str,
        index_name: str,
        id_field: str,
        metadata_fields: list[str],
    ) -> dict[str, Any]:
        """从YAML文件构建索引."""
        store = self._get_store(index_name)

        # 检查是否已有索引
        if store.exists(index_name):
            store.load(index_name)
            return {
                "index_name": index_name,
                "count": store.count(),
                "status": "loaded_existing",
            }

        # 从YAML文件加载数据
        subdir = self.DATA_DIRS.get(source_name, source_name)
        items = self._load_yaml_files(subdir)
        if not items:
            return {
                "index_name": index_name,
                "count": 0,
                "status": "no_data",
            }

        # 准备数据
        ids = []
        texts = []
        metadatas = []

        for item in items:
            item_id = item.get(id_field)
            if not item_id:
                continue

            text = self._extract_text_from_yaml(item)
            if not text.strip():
                continue

            ids.append(str(item_id))
            texts.append(text)
            metadatas.append(self._extract_metadata(item, metadata_fields))

        if not texts:
            return {
                "index_name": index_name,
                "count": 0,
                "status": "no_valid_content",
            }

        # 生成Embedding
        embeddings = self.embedding.encode(texts)

        # 添加到向量存储
        store.add_items(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            texts=texts,
        )

        # 保存索引
        store.save(index_name)

        return {
            "index_name": index_name,
            "count": store.count(),
            "status": "built",
        }

    def build_stock_case_index(self, db: Session | None = None) -> dict[str, Any]:
        """构建个股案例索引."""
        return self._build_index_from_yaml(
            source_name="stock_cases",
            index_name=self.INDEX_NAMES["stock_cases"],
            id_field="id",
            metadata_fields=["symbol", "name", "industry", "return_metrics"],
        )

    def build_allocation_theory_index(self, db: Session | None = None) -> dict[str, Any]:
        """构建资产配置理论索引."""
        return self._build_index_from_yaml(
            source_name="allocation_theory",
            index_name=self.INDEX_NAMES["allocation_theory"],
            id_field="id",
            metadata_fields=["name", "category", "origin_year"],
        )

    def build_finance_basic_index(self, db: Session | None = None) -> dict[str, Any]:
        """构建基础常识索引."""
        return self._build_index_from_yaml(
            source_name="finance_basics",
            index_name=self.INDEX_NAMES["finance_basics"],
            id_field="id",
            metadata_fields=["topic", "category", "difficulty"],
        )

    def build_valuation_case_index(self, db: Session | None = None) -> dict[str, Any]:
        """构建估值案例索引."""
        return self._build_index_from_yaml(
            source_name="valuation_cases",
            index_name=self.INDEX_NAMES["valuation_cases"],
            id_field="id",
            metadata_fields=["case_type", "symbol", "name"],
        )

    def build_behavioral_case_index(self, db: Session | None = None) -> dict[str, Any]:
        """构建行为金融案例索引."""
        return self._build_index_from_yaml(
            source_name="behavioral_cases",
            index_name=self.INDEX_NAMES["behavioral_cases"],
            id_field="id",
            metadata_fields=["bias_name", "category"],
        )

    def build_paper_chunk_index(self, db: Session | None = None) -> dict[str, Any]:
        """构建论文片段索引."""
        return self._build_index_from_yaml(
            source_name="paper_chunks",
            index_name=self.INDEX_NAMES["paper_chunks"],
            id_field="id",
            metadata_fields=["paper_title", "authors", "year", "topic"],
        )

    def build_allocation_case_index(self, db: Session | None = None) -> dict[str, Any]:
        """构建资产配置案例索引."""
        return self._build_index_from_yaml(
            source_name="allocation_cases",
            index_name=self.INDEX_NAMES["allocation_cases"],
            id_field="id",
            metadata_fields=["profile", "cycle", "category"],
        )

    def build_risk_control_case_index(self, db: Session | None = None) -> dict[str, Any]:
        """构建风控案例索引."""
        return self._build_index_from_yaml(
            source_name="risk_control_cases",
            index_name=self.INDEX_NAMES["risk_control_cases"],
            id_field="id",
            metadata_fields=["name", "profile_type", "category"],
        )

    def build_strategy_binding_case_index(self, db: Session | None = None) -> dict[str, Any]:
        """构建策略绑定案例索引."""
        return self._build_index_from_yaml(
            source_name="strategy_binding_cases",
            index_name=self.INDEX_NAMES["strategy_binding_cases"],
            id_field="id",
            metadata_fields=["name", "outcome", "category"],
        )

    def build_all(self, db: Session | None = None, force_rebuild: bool = False) -> dict[str, Any]:
        """构建所有索引.

        Args:
            db: 数据库会话（可选，保持兼容性）
            force_rebuild: 是否强制重建

        Returns:
            {"stock_cases": {...}, "allocation_theory": {...}, ...}
        """
        # 如强制重建，删除现有索引文件
        if force_rebuild:
            for name in self.INDEX_NAMES.values():
                store = self._get_store(name)
                # 清除已加载的索引，下次会重新构建
                if hasattr(store, '_index') and store._index is not None:
                    store._index = None
                    store._items = []
                    store._id_to_idx = {}
                # 删除持久化文件
                import os
                persist_path = Path(store.persist_dir) / f"{name}.pkl"
                if persist_path.exists():
                    os.remove(persist_path)
                    print(f"Removed existing index: {persist_path}")

        results = {
            "stock_cases": self.build_stock_case_index(),
            "allocation_theory": self.build_allocation_theory_index(),
            "finance_basics": self.build_finance_basic_index(),
            "valuation_cases": self.build_valuation_case_index(),
            "behavioral_cases": self.build_behavioral_case_index(),
            "paper_chunks": self.build_paper_chunk_index(),
            "allocation_cases": self.build_allocation_case_index(),
            "risk_control_cases": self.build_risk_control_case_index(),
            "strategy_binding_cases": self.build_strategy_binding_case_index(),
        }

        return results

    def get_stats(self) -> dict[str, Any]:
        """获取所有索引统计信息."""
        stats = {}
        for name, index_name in self.INDEX_NAMES.items():
            store = self._get_store(index_name)
            if store.exists(index_name):
                store.load(index_name)
                stats[name] = {
                    "exists": True,
                    "count": store.count(),
                }
            else:
                stats[name] = {
                    "exists": False,
                    "count": 0,
                }
        return stats
