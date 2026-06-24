"""A/B测试框架 API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import random

from app.db.session import get_db
from app.models.ab_test import ABTest, ABTestResult, ABTestStatistics

router = APIRouter()


class ABTestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    target_metric: str = "return"
    variant_a_name: str = "变体A"
    variant_a_config: Optional[Dict[str, Any]] = None
    variant_b_name: str = "变体B"
    variant_b_config: Optional[Dict[str, Any]] = None
    target_sample_size: int = 100


class ABTestResultCreate(BaseModel):
    user_id: int
    variant: str
    metric_value: Optional[float] = None
    context: Optional[Dict[str, Any]] = None


@router.get("", response_model=list[dict])
def list_ab_tests(status: Optional[str] = None, db: Session = Depends(get_db)):
    """获取A/B测试列表."""
    query = db.query(ABTest)
    if status:
        query = query.filter(ABTest.status == status)
    tests = query.order_by(ABTest.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "hypothesis": t.hypothesis,
            "target_metric": t.target_metric,
            "variant_a_name": t.variant_a_name,
            "variant_b_name": t.variant_b_name,
            "status": t.status,
            "start_date": t.start_date.isoformat() if t.start_date else None,
            "end_date": t.end_date.isoformat() if t.end_date else None,
            "target_sample_size": t.target_sample_size,
            "current_sample_a": t.current_sample_a,
            "current_sample_b": t.current_sample_b,
            "significance_level": t.significance_level,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tests
    ]


@router.post("", response_model=dict)
def create_ab_test(payload: ABTestCreate, db: Session = Depends(get_db)):
    """创建A/B测试."""
    test = ABTest(
        name=payload.name,
        description=payload.description,
        hypothesis=payload.hypothesis,
        target_metric=payload.target_metric,
        variant_a_name=payload.variant_a_name,
        variant_a_config=payload.variant_a_config,
        variant_b_name=payload.variant_b_name,
        variant_b_config=payload.variant_b_config,
        target_sample_size=payload.target_sample_size,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return {"id": test.id, "message": "A/B测试创建成功"}


@router.post("/{test_id}/assign", response_model=dict)
def assign_variant(test_id: int, user_id: int, db: Session = Depends(get_db)):
    """为用户分配A/B测试变体."""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")
    if test.status != "running":
        raise HTTPException(status_code=400, detail="测试未运行")

    # 检查用户是否已分配
    existing = (
        db.query(ABTestResult)
        .filter(ABTestResult.test_id == test_id, ABTestResult.user_id == user_id)
        .first()
    )
    if existing:
        return {"test_id": test_id, "user_id": user_id, "variant": existing.variant}

    # 随机分配，尽量保持均衡
    if test.current_sample_a <= test.current_sample_b:
        variant = "A"
        test.current_sample_a += 1
    else:
        variant = "B"
        test.current_sample_b += 1

    result = ABTestResult(
        test_id=test_id,
        user_id=user_id,
        variant=variant,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return {"test_id": test_id, "user_id": user_id, "variant": variant}


@router.post("/{test_id}/result", response_model=dict)
def record_result(
    test_id: int,
    payload: ABTestResultCreate,
    db: Session = Depends(get_db),
):
    """记录A/B测试结果."""
    result = (
        db.query(ABTestResult)
        .filter(ABTestResult.test_id == test_id, ABTestResult.user_id == payload.user_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="用户未参与该测试")

    result.metric_value = payload.metric_value
    result.context = payload.context
    db.commit()
    db.refresh(result)
    return {"message": "结果记录成功"}


@router.get("/{test_id}/statistics", response_model=dict)
def get_test_statistics(test_id: int, db: Session = Depends(get_db)):
    """获取A/B测试统计结果."""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")

    a_results = (
        db.query(ABTestResult)
        .filter(ABTestResult.test_id == test_id, ABTestResult.variant == "A", ABTestResult.metric_value.isnot(None))
        .all()
    )
    b_results = (
        db.query(ABTestResult)
        .filter(ABTestResult.test_id == test_id, ABTestResult.variant == "B", ABTestResult.metric_value.isnot(None))
        .all()
    )

    def _stats(results):
        if not results:
            return None
        values = [r.metric_value for r in results]
        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        std = variance ** 0.5
        return {
            "count": n,
            "mean": round(mean, 4),
            "std": round(std, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }

    a_stats = _stats(a_results)
    b_stats = _stats(b_results)

    # 简单t检验（假设方差相等）
    winner = "inconclusive"
    p_value = None
    if a_stats and b_stats and a_stats["count"] > 1 and b_stats["count"] > 1:
        import math
        n1, n2 = a_stats["count"], b_stats["count"]
        m1, m2 = a_stats["mean"], b_stats["mean"]
        s1, s2 = a_stats["std"], b_stats["std"]
        # 合并标准差
        pooled_std = math.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
        if pooled_std > 0:
            se = pooled_std * math.sqrt(1 / n1 + 1 / n2)
            t_stat = (m1 - m2) / se
            # 简化的p值估算
            from math import exp
            p_value = min(1.0, 2 * (1 - (1 / (1 + exp(-abs(t_stat) * 0.8)))))
            if p_value < test.significance_level:
                winner = "A" if m1 > m2 else "B" if m2 > m1 else "tie"
            else:
                winner = "inconclusive"

    return {
        "test_id": test_id,
        "test_name": test.name,
        "target_metric": test.target_metric,
        "variant_a": a_stats,
        "variant_b": b_stats,
        "p_value": round(p_value, 4) if p_value else None,
        "significant": winner != "inconclusive",
        "winner": winner,
        "status": test.status,
    }
