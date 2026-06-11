"""知识库数据加载器.

将YAML文件加载到数据库中.
"""

import os
import yaml
from pathlib import Path
from typing import Any
from sqlalchemy.orm import Session

from app.models.rag_knowledge import (
    StockAnalysisCase,
    AllocationTheory,
    FinanceBasic,
    ValuationTimingCase,
    BehavioralCase,
)


def load_yaml_file(path: Path) -> dict[str, Any]:
    """加载YAML文件."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_stock_cases(db: Session, data_dir: Path) -> int:
    """加载个股分析案例."""
    count = 0
    cases_dir = data_dir / "stock_cases"

    for file_path in cases_dir.glob("*.yaml"):
        data = load_yaml_file(file_path)

        # 检查是否已存在
        existing = db.query(StockAnalysisCase).filter(
            StockAnalysisCase.case_id == data["case_id"]
        ).first()
        if existing:
            continue

        case = StockAnalysisCase(
            case_id=data["case_id"],
            symbol=data["symbol"],
            name=data["name"],
            industry=data.get("industry"),
            bull_period=data.get("bull_period"),
            price_start=data.get("price_start"),
            price_peak=data.get("price_peak"),
            return_pct=data.get("return_pct"),
            industry_trend=data.get("investment_logic", {}).get("industry_trend"),
            company_moat=data.get("investment_logic", {}).get("company_moat"),
            growth_driver=data.get("investment_logic", {}).get("growth_driver"),
            competitive_advantage=data.get("investment_logic", {}).get("competitive_advantage"),
            key_metrics=data.get("key_metrics"),
            valuation_at_buy=data.get("valuation_at_buy"),
            valuation_at_peak=data.get("valuation_at_peak"),
            entry_signals=data.get("entry_signals"),
            exit_signals=data.get("exit_signals"),
            key_insights=data.get("key_insights"),
            lessons=data.get("lessons"),
            content=data.get("content", ""),
        )
        db.add(case)
        count += 1

    db.commit()
    return count


def load_allocation_theory(db: Session, data_dir: Path) -> int:
    """加载资产配置理论."""
    count = 0
    theory_dir = data_dir / "allocation_theory"

    for file_path in theory_dir.glob("*.yaml"):
        data = load_yaml_file(file_path)

        existing = db.query(AllocationTheory).filter(
            AllocationTheory.theory_id == data["theory_id"]
        ).first()
        if existing:
            continue

        theory = AllocationTheory(
            theory_id=data["theory_id"],
            name=data["name"],
            name_cn=data.get("name_cn"),
            category=data.get("category"),
            origin_authors=data.get("origin_authors"),
            origin_year=data.get("origin_year"),
            origin_paper=data.get("origin_paper"),
            core_formula=data.get("core_formula"),
            explanation=data.get("explanation"),
            assumptions=data.get("assumptions"),
            limitations=data.get("limitations"),
            application=data.get("application"),
            china_adaptation=data.get("china_adaptation"),
            content=data.get("content", ""),
        )
        db.add(theory)
        count += 1

    db.commit()
    return count


def load_finance_basics(db: Session, data_dir: Path) -> int:
    """加载基础金融常识."""
    count = 0
    basics_dir = data_dir / "finance_basics"

    for file_path in basics_dir.glob("*.yaml"):
        data = load_yaml_file(file_path)

        existing = db.query(FinanceBasic).filter(
            FinanceBasic.entry_id == data["entry_id"]
        ).first()
        if existing:
            continue

        basic = FinanceBasic(
            entry_id=data["entry_id"],
            topic=data["topic"],
            category=data.get("category"),
            difficulty=data.get("difficulty"),
            definition=data.get("definition"),
            simple_explanation=data.get("simple_explanation"),
            usage=data.get("usage"),
            cautions=data.get("cautions"),
            example=data.get("example"),
            related_concepts=data.get("related_concepts"),
            common_questions=data.get("common_questions"),
            content=data.get("content", ""),
        )
        db.add(basic)
        count += 1

    db.commit()
    return count


def load_valuation_cases(db: Session, data_dir: Path) -> int:
    """加载估值案例."""
    count = 0
    cases_dir = data_dir / "valuation_cases"

    for file_path in cases_dir.glob("*.yaml"):
        data = load_yaml_file(file_path)

        existing = db.query(ValuationTimingCase).filter(
            ValuationTimingCase.case_id == data["case_id"]
        ).first()
        if existing:
            continue

        case = ValuationTimingCase(
            case_id=data["case_id"],
            case_type=data.get("case_type"),
            symbol=data.get("symbol"),
            name=data.get("name"),
            period=data.get("period"),
            background=data.get("background"),
            valuation_at_bottom=data.get("valuation_at_bottom"),
            valuation_at_peak=data.get("valuation_at_peak"),
            investment_logic=data.get("investment_logic"),
            outcome=data.get("outcome"),
            lessons=data.get("lessons"),
            content=data.get("content", ""),
        )
        db.add(case)
        count += 1

    db.commit()
    return count


def load_behavioral_cases(db: Session, data_dir: Path) -> int:
    """加载行为金融案例."""
    count = 0
    cases_dir = data_dir / "behavioral_cases"

    for file_path in cases_dir.glob("*.yaml"):
        data = load_yaml_file(file_path)

        existing = db.query(BehavioralCase).filter(
            BehavioralCase.case_id == data["case_id"]
        ).first()
        if existing:
            continue

        case = BehavioralCase(
            case_id=data["case_id"],
            bias_name=data["bias_name"],
            bias_name_cn=data.get("bias_name_cn"),
            category=data.get("category"),
            source_authors=data.get("source_authors"),
            source_year=data.get("source_year"),
            phenomenon=data.get("phenomenon"),
            china_example=data.get("china_example"),
            coping_strategy=data.get("coping_strategy"),
            system_countermeasure=data.get("system_countermeasure"),
            content=data.get("content", ""),
        )
        db.add(case)
        count += 1

    db.commit()
    return count


def load_all_knowledge(db: Session, data_dir: Path | None = None) -> dict[str, int]:
    """加载所有知识库数据.

    Returns:
        {"stock_cases": 20, "allocation_theory": 2, ...}
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent.parent / "data" / "knowledge"

    results = {
        "stock_cases": load_stock_cases(db, data_dir),
        "allocation_theory": load_allocation_theory(db, data_dir),
        "finance_basics": load_finance_basics(db, data_dir),
        "valuation_cases": load_valuation_cases(db, data_dir),
        "behavioral_cases": load_behavioral_cases(db, data_dir),
    }

    return results
