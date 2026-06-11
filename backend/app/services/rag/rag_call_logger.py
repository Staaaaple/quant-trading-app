"""RAG LLM 调用记录器.

记录每次RAG质检的LLM调用情况，用于性能分析和成本监控.
"""

import json
import time
from typing import Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class RAGCallRecord:
    """单次RAG LLM调用记录."""

    # 基本信息
    timestamp: str
    step: str  # saa/taa/binding/risk_config/reliability/final
    portfolio_id: str

    # 输入
    prompt_tokens: int = 0
    prompt_preview: str = ""  # 前200字符

    # 输出
    response_tokens: int = 0
    response_preview: str = ""  # 前200字符

    # 结果
    passed: bool = False
    score: float = 0.0
    issues_count: int = 0
    adjustments_count: int = 0

    # 性能
    retrieval_time_ms: float = 0.0
    llm_time_ms: float = 0.0
    parse_time_ms: float = 0.0
    total_time_ms: float = 0.0

    # 重试信息
    retry_count: int = 0

    # 错误
    error: str | None = None


@dataclass
class PortfolioRAGSummary:
    """单次组合生成的RAG调用汇总."""

    portfolio_id: str
    timestamp: str
    profile_risk_level: str
    market_cycle: str

    # 调用统计
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_response_tokens: int = 0
    total_time_ms: float = 0.0

    # 质检结果
    steps_reviewed: list[str] = field(default_factory=list)
    steps_passed: list[str] = field(default_factory=list)
    steps_failed: list[str] = field(default_factory=list)
    total_adjustments: int = 0
    total_retries: int = 0

    # 各步详情
    step_records: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转为字典."""
        return asdict(self)


class RAGCallLogger:
    """RAG调用记录器."""

    def __init__(self, log_dir: str | None = None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent.parent / "logs" / "rag_calls"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存（最近100条）
        self._records: list[RAGCallRecord] = []
        self._max_cache = 100

    def log_call(
        self,
        step: str,
        portfolio_id: str,
        prompt: str,
        response: str,
        passed: bool,
        score: float,
        issues: list[str],
        adjustments: list[dict],
        retrieval_time_ms: float,
        llm_time_ms: float,
        parse_time_ms: float,
        retry_count: int = 0,
        error: str | None = None,
    ) -> RAGCallRecord:
        """记录一次LLM调用."""
        record = RAGCallRecord(
            timestamp=datetime.now().isoformat(),
            step=step,
            portfolio_id=portfolio_id,
            prompt_tokens=len(prompt) // 4,  # 粗略估算
            prompt_preview=prompt[:200],
            response_tokens=len(response) // 4,
            response_preview=response[:200],
            passed=passed,
            score=score,
            issues_count=len(issues),
            adjustments_count=len(adjustments),
            retrieval_time_ms=retrieval_time_ms,
            llm_time_ms=llm_time_ms,
            parse_time_ms=parse_time_ms,
            total_time_ms=retrieval_time_ms + llm_time_ms + parse_time_ms,
            retry_count=retry_count,
            error=error,
        )

        # 缓存
        self._records.append(record)
        if len(self._records) > self._max_cache:
            self._records.pop(0)

        # 持久化
        self._save_record(record)

        return record

    def _save_record(self, record: RAGCallRecord) -> None:
        """保存记录到文件."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"rag_calls_{date_str}.jsonl"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def log_portfolio_summary(
        self,
        portfolio_id: str,
        profile_risk_level: str,
        market_cycle: str,
        records: list[RAGCallRecord],
    ) -> PortfolioRAGSummary:
        """记录组合生成的RAG调用汇总."""
        summary = PortfolioRAGSummary(
            portfolio_id=portfolio_id,
            timestamp=datetime.now().isoformat(),
            profile_risk_level=profile_risk_level,
            market_cycle=market_cycle,
        )

        for record in records:
            summary.total_calls += 1
            summary.total_prompt_tokens += record.prompt_tokens
            summary.total_response_tokens += record.response_tokens
            summary.total_time_ms += record.total_time_ms

            summary.steps_reviewed.append(record.step)
            if record.passed:
                summary.steps_passed.append(record.step)
            else:
                summary.steps_failed.append(record.step)

            summary.total_adjustments += record.adjustments_count
            summary.total_retries += record.retry_count
            summary.step_records.append(asdict(record))

        # 持久化
        self._save_summary(summary)

        return summary

    def _save_summary(self, summary: PortfolioRAGSummary) -> None:
        """保存汇总到文件."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"rag_summary_{date_str}.jsonl"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(summary), ensure_ascii=False) + "\n")

    def get_recent_records(self, n: int = 10) -> list[RAGCallRecord]:
        """获取最近n条记录."""
        return self._records[-n:]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息."""
        if not self._records:
            return {}

        total = len(self._records)
        passed = sum(1 for r in self._records if r.passed)
        failed = total - passed

        avg_time = sum(r.total_time_ms for r in self._records) / total
        avg_llm_time = sum(r.llm_time_ms for r in self._records) / total

        return {
            "total_records": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "avg_total_time_ms": round(avg_time, 2),
            "avg_llm_time_ms": round(avg_llm_time, 2),
            "total_prompt_tokens": sum(r.prompt_tokens for r in self._records),
            "total_response_tokens": sum(r.response_tokens for r in self._records),
            "total_adjustments": sum(r.adjustments_count for r in self._records),
            "total_retries": sum(r.retry_count for r in self._records),
        }

    def get_step_stats(self) -> dict[str, dict[str, Any]]:
        """按步骤统计."""
        stats = {}
        for record in self._records:
            step = record.step
            if step not in stats:
                stats[step] = {
                    "count": 0,
                    "passed": 0,
                    "failed": 0,
                    "avg_time_ms": 0,
                    "total_time_ms": 0,
                }

            stats[step]["count"] += 1
            stats[step]["passed"] += 1 if record.passed else 0
            stats[step]["failed"] += 0 if record.passed else 1
            stats[step]["total_time_ms"] += record.total_time_ms

        for step in stats:
            count = stats[step]["count"]
            stats[step]["avg_time_ms"] = round(stats[step]["total_time_ms"] / count, 2) if count > 0 else 0
            stats[step]["pass_rate"] = round(stats[step]["passed"] / count, 2) if count > 0 else 0

        return stats


# 全局实例
_logger_instance: RAGCallLogger | None = None


def get_rag_logger() -> RAGCallLogger:
    """获取全局RAG调用记录器."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = RAGCallLogger()
    return _logger_instance
