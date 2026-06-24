"""购买教学/建仓引导 API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.tutorial_step import TutorialStep, TutorialProgress

router = APIRouter()


# 预设的建仓引导步骤数据
DEFAULT_BUILDING_STEPS = [
    {
        "category": "building",
        "step_order": 1,
        "title": "确认组合方案",
        "description": "查看你的投资组合配置详情",
        "tip": "确认各标的权重和风险等级是否符合你的预期",
    },
    {
        "category": "building",
        "step_order": 2,
        "title": "选择券商开户",
        "description": "挑选合适的券商完成开户",
        "tip": "佣金率 ≤ 0.025%，支持ETF交易，APP体验流畅",
    },
    {
        "category": "building",
        "step_order": 3,
        "title": "银证转账入金",
        "description": "将资金从银行卡转入证券账户",
        "tip": "建议先转入计划建仓金额的 40%（第一批）",
    },
    {
        "category": "building",
        "step_order": 4,
        "title": "第一批建仓（40%）",
        "description": "买入股票类ETF标的",
        "tip": "按组合权重比例买入，不要一次性全仓",
    },
    {
        "category": "building",
        "step_order": 5,
        "title": "第二批建仓（35%）",
        "description": "2周后买入债券类+商品类标的",
        "tip": "观察市场走势，若下跌可适当加仓",
    },
    {
        "category": "building",
        "step_order": 6,
        "title": "第三批建仓（25%）",
        "description": "1个月后补齐剩余仓位",
        "tip": "完成建仓后开启日常跟进模式",
    },
    {
        "category": "building",
        "step_order": 7,
        "title": "设置预警提醒",
        "description": "配置策略寿命预警和再平衡提醒",
        "tip": "建议开启推送通知，及时获取操作建议",
    },
]


def _ensure_default_steps(db: Session):
    """确保默认步骤已写入数据库."""
    existing = db.query(TutorialStep).filter(TutorialStep.category == "building").count()
    if existing == 0:
        for step_data in DEFAULT_BUILDING_STEPS:
            db.add(TutorialStep(**step_data))
        db.commit()


@router.get("/steps", response_model=list[dict])
def get_tutorial_steps(category: str = "building", db: Session = Depends(get_db)):
    """获取教程步骤列表."""
    _ensure_default_steps(db)
    steps = (
        db.query(TutorialStep)
        .filter(TutorialStep.category == category)
        .order_by(TutorialStep.step_order)
        .all()
    )
    return [
        {
            "id": s.id,
            "step_order": s.step_order,
            "title": s.title,
            "description": s.description,
            "tip": s.tip,
        }
        for s in steps
    ]


@router.get("/progress/{user_id}", response_model=dict)
def get_tutorial_progress(user_id: int, category: str = "building", db: Session = Depends(get_db)):
    """获取用户教程学习进度."""
    progress = (
        db.query(TutorialProgress)
        .filter(TutorialProgress.user_id == user_id, TutorialProgress.tutorial_category == category)
        .first()
    )
    if not progress:
        total = db.query(TutorialStep).filter(TutorialStep.category == category).count()
        return {
            "user_id": user_id,
            "category": category,
            "current_step": 0,
            "total_steps": total or len(DEFAULT_BUILDING_STEPS),
            "completed": 0,
        }
    return {
        "user_id": progress.user_id,
        "category": progress.tutorial_category,
        "current_step": progress.current_step,
        "total_steps": progress.total_steps,
        "completed": progress.completed,
    }


@router.post("/progress/{user_id}", response_model=dict)
def update_tutorial_progress(
    user_id: int,
    category: str = "building",
    current_step: int = 0,
    db: Session = Depends(get_db),
):
    """更新用户教程进度."""
    _ensure_default_steps(db)
    total = db.query(TutorialStep).filter(TutorialStep.category == category).count()

    progress = (
        db.query(TutorialProgress)
        .filter(TutorialProgress.user_id == user_id, TutorialProgress.tutorial_category == category)
        .first()
    )

    if not progress:
        progress = TutorialProgress(
            user_id=user_id,
            tutorial_category=category,
            current_step=current_step,
            total_steps=total or len(DEFAULT_BUILDING_STEPS),
            completed=1 if current_step >= (total or len(DEFAULT_BUILDING_STEPS)) else 0,
        )
        db.add(progress)
    else:
        progress.current_step = max(progress.current_step, current_step)
        progress.total_steps = total or len(DEFAULT_BUILDING_STEPS)
        if progress.current_step >= progress.total_steps:
            progress.completed = 1

    db.commit()
    db.refresh(progress)
    return {
        "user_id": progress.user_id,
        "category": progress.tutorial_category,
        "current_step": progress.current_step,
        "total_steps": progress.total_steps,
        "completed": progress.completed,
    }
