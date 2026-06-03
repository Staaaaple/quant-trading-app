"""投资者画像计算服务.

15题问卷 → 15维profile_vector (1-10 连续值).
"""
from typing import Any

from sqlalchemy.orm import Session

from app.models.investor_profile import InvestorProfile


# ── 问卷定义 ──
# 每题: {id, question, options: [{label, scores: {dim: val}}]}
# scores 中每个维度可贡献 0-10 的分值，最终取平均并 clamp 到 1-10

QUESTIONS = [
    {
        "id": "q1_capital",
        "category": "basic",
        "question": "你的投资资金规模是多少？",
        "options": [
            {"label": "小于5万", "scores": {"capital_tier": 2, "risk_tolerance": 3}},
            {"label": "5万-20万", "scores": {"capital_tier": 4, "risk_tolerance": 4}},
            {"label": "20万-100万", "scores": {"capital_tier": 6, "risk_tolerance": 6}},
            {"label": "大于100万", "scores": {"capital_tier": 9, "risk_tolerance": 7}},
        ],
    },
    {
        "id": "q2_age",
        "category": "basic",
        "question": "你的年龄区间？",
        "options": [
            {"label": "18-25岁", "scores": {"time_horizon_score": 9, "risk_tolerance": 7}},
            {"label": "26-35岁", "scores": {"time_horizon_score": 8, "risk_tolerance": 6}},
            {"label": "36-45岁", "scores": {"time_horizon_score": 6, "risk_tolerance": 5}},
            {"label": "46-55岁", "scores": {"time_horizon_score": 4, "risk_tolerance": 4}},
            {"label": "55岁以上", "scores": {"time_horizon_score": 2, "risk_tolerance": 3}},
        ],
    },
    {
        "id": "q3_experience",
        "category": "basic",
        "question": "你买过哪些投资产品？（可多选）",
        "options": [
            {"label": "都没买过", "scores": {"experience_level": 1, "risk_tolerance": 3}},
            {"label": "银行理财", "scores": {"experience_level": 2, "risk_tolerance": 4}},
            {"label": "基金", "scores": {"experience_level": 4, "risk_tolerance": 5}},
            {"label": "股票", "scores": {"experience_level": 6, "risk_tolerance": 6}},
            {"label": "期货/期权", "scores": {"experience_level": 9, "risk_tolerance": 8}},
        ],
    },
    {
        "id": "q4_income_ratio",
        "category": "basic",
        "question": "月度可支配收入中，用于投资的比例？",
        "options": [
            {"label": "小于10%", "scores": {"income_stability": 3, "risk_tolerance": 3}},
            {"label": "10%-30%", "scores": {"income_stability": 5, "risk_tolerance": 5}},
            {"label": "30%-50%", "scores": {"income_stability": 7, "risk_tolerance": 6}},
            {"label": "大于50%", "scores": {"income_stability": 9, "risk_tolerance": 7}},
        ],
    },
    {
        "id": "q5_debt",
        "category": "basic",
        "question": "你目前是否有大额负债？",
        "options": [
            {"label": "有，压力大", "scores": {"debt_pressure": 9, "risk_tolerance": 2, "security_need": 8}},
            {"label": "有，能承受", "scores": {"debt_pressure": 5, "risk_tolerance": 5, "security_need": 5}},
            {"label": "无负债", "scores": {"debt_pressure": 2, "risk_tolerance": 7, "security_need": 3}},
        ],
    },
    {
        "id": "q6_loss_aversion",
        "category": "psychology",
        "question": "1万基金跌到8000，你会？",
        "options": [
            {"label": "立刻全卖", "scores": {"loss_aversion": 9, "risk_tolerance": 2, "emergency_response": 9}},
            {"label": "卖一半", "scores": {"loss_aversion": 6, "risk_tolerance": 4, "emergency_response": 6}},
            {"label": "不动，等回本", "scores": {"loss_aversion": 4, "risk_tolerance": 5, "emergency_response": 4}},
            {"label": "加仓摊低成本", "scores": {"loss_aversion": 2, "risk_tolerance": 8, "emergency_response": 2}},
        ],
    },
    {
        "id": "q7_herding",
        "category": "psychology",
        "question": "朋友说某股票涨了30%，你会？",
        "options": [
            {"label": "马上跟买", "scores": {"herding_tendency": 9, "risk_tolerance": 6, "information_processing": 2}},
            {"label": "研究后决定", "scores": {"herding_tendency": 4, "risk_tolerance": 5, "information_processing": 7}},
            {"label": "不为所动", "scores": {"herding_tendency": 2, "risk_tolerance": 4, "information_processing": 8}},
            {"label": "觉得该卖了", "scores": {"herding_tendency": 5, "risk_tolerance": 3, "information_processing": 6}},
        ],
    },
    {
        "id": "q8_overconfidence",
        "category": "psychology",
        "question": "连涨3个月赚20%，你觉得主要原因是？",
        "options": [
            {"label": "我眼光好", "scores": {"overconfidence": 9, "risk_tolerance": 7, "information_processing": 2}},
            {"label": "我研究了", "scores": {"overconfidence": 6, "risk_tolerance": 6, "information_processing": 6}},
            {"label": "市场好", "scores": {"overconfidence": 3, "risk_tolerance": 4, "information_processing": 7}},
            {"label": "运气", "scores": {"overconfidence": 1, "risk_tolerance": 3, "information_processing": 8}},
        ],
    },
    {
        "id": "q9_delayed_gratification",
        "category": "psychology",
        "question": "突然收到2万奖金，你会？",
        "options": [
            {"label": "全存银行", "scores": {"delayed_gratification": 2, "risk_tolerance": 1, "security_need": 9}},
            {"label": "大部分存，小部分投", "scores": {"delayed_gratification": 4, "risk_tolerance": 3, "security_need": 6}},
            {"label": "一半投一半消费", "scores": {"delayed_gratification": 6, "risk_tolerance": 6, "security_need": 4}},
            {"label": "全投高风险", "scores": {"delayed_gratification": 9, "risk_tolerance": 9, "security_need": 1}},
        ],
    },
    {
        "id": "q10_anchoring",
        "category": "psychology",
        "question": "10元买入跌到7元，涨回9元，你会？",
        "options": [
            {"label": "解套就卖", "scores": {"anchoring_effect": 9, "loss_aversion": 7, "risk_tolerance": 2}},
            {"label": "等10元再卖", "scores": {"anchoring_effect": 7, "loss_aversion": 5, "risk_tolerance": 3}},
            {"label": "看趋势决定", "scores": {"anchoring_effect": 3, "loss_aversion": 3, "risk_tolerance": 6}},
            {"label": "该加仓", "scores": {"anchoring_effect": 1, "loss_aversion": 1, "risk_tolerance": 8}},
        ],
    },
    {
        "id": "q11_security",
        "category": "psychology",
        "question": "明天突然需要3万急用，能立刻拿出来吗？",
        "options": [
            {"label": "完全没问题", "scores": {"security_need": 2, "risk_tolerance": 7, "capital_tier": 8}},
            {"label": "要卖投资", "scores": {"security_need": 6, "risk_tolerance": 4, "capital_tier": 4}},
            {"label": "凑不齐", "scores": {"security_need": 9, "risk_tolerance": 1, "capital_tier": 2}},
            {"label": "没想过", "scores": {"security_need": 5, "risk_tolerance": 3, "capital_tier": 4}},
        ],
    },
    {
        "id": "q12_time_horizon",
        "category": "psychology",
        "question": "能接受多久看不到明显收益？",
        "options": [
            {"label": "1个月", "scores": {"time_horizon_score": 2, "risk_tolerance": 3, "delayed_gratification": 2}},
            {"label": "3个月", "scores": {"time_horizon_score": 4, "risk_tolerance": 4, "delayed_gratification": 4}},
            {"label": "1年", "scores": {"time_horizon_score": 7, "risk_tolerance": 6, "delayed_gratification": 6}},
            {"label": "3年以上", "scores": {"time_horizon_score": 9, "risk_tolerance": 7, "delayed_gratification": 9}},
        ],
    },
    {
        "id": "q13_info_processing",
        "category": "psychology",
        "question": "央行宣布降准，你的第一反应是？",
        "options": [
            {"label": "立刻加仓", "scores": {"information_processing": 2, "risk_tolerance": 7, "overconfidence": 7}},
            {"label": "研究对哪些板块有影响", "scores": {"information_processing": 7, "risk_tolerance": 5, "overconfidence": 4}},
            {"label": "等市场反应再看", "scores": {"information_processing": 5, "risk_tolerance": 4, "overconfidence": 3}},
            {"label": "不知道什么意思", "scores": {"information_processing": 1, "risk_tolerance": 2, "experience_level": 1}},
        ],
    },
    {
        "id": "q14_social_pressure",
        "category": "psychology",
        "question": "家人反对你买股票，你会？",
        "options": [
            {"label": "立刻停止", "scores": {"social_pressure": 9, "risk_tolerance": 2, "herding_tendency": 7}},
            {"label": "减少投入", "scores": {"social_pressure": 6, "risk_tolerance": 4, "herding_tendency": 5}},
            {"label": "不听，按自己节奏", "scores": {"social_pressure": 2, "risk_tolerance": 7, "herding_tendency": 2}},
            {"label": "用收益说服他们", "scores": {"social_pressure": 3, "risk_tolerance": 6, "overconfidence": 6}},
        ],
    },
    {
        "id": "q15_emergency",
        "category": "psychology",
        "question": "持仓一周跌20%，你会？",
        "options": [
            {"label": "全部清仓", "scores": {"emergency_response": 9, "loss_aversion": 9, "risk_tolerance": 1}},
            {"label": "减仓一半", "scores": {"emergency_response": 6, "loss_aversion": 6, "risk_tolerance": 3}},
            {"label": "不动，看后续", "scores": {"emergency_response": 3, "loss_aversion": 3, "risk_tolerance": 6}},
            {"label": "加仓，摊薄成本", "scores": {"emergency_response": 1, "loss_aversion": 1, "risk_tolerance": 9}},
        ],
    },
]

# 所有维度名
DIMENSIONS = [
    "risk_tolerance", "loss_aversion", "herding_tendency",
    "overconfidence", "delayed_gratification", "security_need",
    "time_horizon_score", "experience_level", "capital_tier",
    "income_stability", "debt_pressure", "information_processing",
    "social_pressure", "emergency_response", "anchoring_effect",
]


def _get_question_by_id(qid: str) -> dict[str, Any] | None:
    for q in QUESTIONS:
        if q["id"] == qid:
            return q
    return None


def _clamp(value: float, lo: float = 1.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def compute_profile_vector(answers: dict[str, Any]) -> dict[str, float]:
    """从问卷答案计算15维profile_vector.

    answers: {question_id: option_label}
    返回: {dimension: score(1-10)}
    """
    accumulators: dict[str, list[float]] = {d: [] for d in DIMENSIONS}

    for qid, selected_label in answers.items():
        q = _get_question_by_id(qid)
        if q is None:
            continue

        # 找到选中的选项
        selected_option = None
        for opt in q["options"]:
            if opt["label"] == selected_label:
                selected_option = opt
                break

        if selected_option is None:
            continue

        # 累加各维度分值
        for dim, val in selected_option["scores"].items():
            if dim in accumulators:
                accumulators[dim].append(float(val))

    # 取平均并 clamp
    result: dict[str, float] = {}
    for dim in DIMENSIONS:
        vals = accumulators[dim]
        if vals:
            result[dim] = _clamp(sum(vals) / len(vals))
        else:
            result[dim] = 5.0  # 默认值

    return result


def derive_labels(vector: dict[str, float]) -> dict[str, str]:
    """从profile_vector派生标签."""
    risk = vector["risk_tolerance"]
    if risk <= 3.5:
        risk_label = "保守型"
    elif risk <= 5.5:
        risk_label = "稳健型"
    elif risk <= 7.5:
        risk_label = "积极型"
    else:
        risk_label = "激进型"

    time = vector["time_horizon_score"]
    if time <= 3.5:
        time_label = "短期"
    elif time <= 6.5:
        time_label = "中期"
    else:
        time_label = "长期"

    exp = vector["experience_level"]
    if exp <= 2.5:
        exp_label = "小白"
    elif exp <= 4.5:
        exp_label = "新手"
    elif exp <= 7.5:
        exp_label = "熟手"
    else:
        exp_label = "高手"

    return {
        "risk_label": risk_label,
        "time_horizon_label": time_label,
        "experience_label": exp_label,
    }


def create_profile(db: Session, user_id: int, answers: dict[str, Any]) -> InvestorProfile:
    """创建投资者画像."""
    vector = compute_profile_vector(answers)
    labels = derive_labels(vector)

    profile = InvestorProfile(
        user_id=user_id,
        answers_json=answers,
        **vector,
        **labels,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_profile_by_user(db: Session, user_id: int) -> InvestorProfile | None:
    return (
        db.query(InvestorProfile)
        .filter(InvestorProfile.user_id == user_id, InvestorProfile.is_active == True)
        .order_by(InvestorProfile.created_at.desc())
        .first()
    )


def update_profile(db: Session, profile_id: int, answers: dict[str, Any]) -> InvestorProfile | None:
    profile = db.query(InvestorProfile).filter(InvestorProfile.id == profile_id).first()
    if profile is None:
        return None

    vector = compute_profile_vector(answers)
    labels = derive_labels(vector)

    profile.answers_json = answers
    for dim in DIMENSIONS:
        setattr(profile, dim, vector[dim])
    for k, v in labels.items():
        setattr(profile, k, v)

    db.commit()
    db.refresh(profile)
    return profile
