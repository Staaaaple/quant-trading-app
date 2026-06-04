"""投资者画像计算服务.

18题问卷 → 18维profile_vector (1-10 连续值).
"""
from typing import Any

from sqlalchemy.orm import Session

from app.models.investor_profile import InvestorProfile


# ── 问卷定义 ──
# 每题: {id, question, options: [{label, scores: {dim: val}}]}
# scores 中每个维度可贡献 0-10 的分值，最终取平均并 clamp 到 1-10
# 设计原则:
#   - risk_tolerance 不再每题都出现，仅在与风险直接相关的题中出现
#   - 每个指标至少覆盖2题
#   - 新增 diversification_preference, stop_loss_discipline, emotional_stability

QUESTIONS = [
    # ===== Step 1: 基本信息 (6题) =====
    {
        "id": "q1_capital",
        "category": "basic",
        "question": "你的投资资金规模是多少？",
        "options": [
            {"label": "小于5万", "scores": {"capital_tier": 2}},
            {"label": "5万-20万", "scores": {"capital_tier": 4}},
            {"label": "20万-100万", "scores": {"capital_tier": 6}},
            {"label": "大于100万", "scores": {"capital_tier": 9}},
        ],
    },
    {
        "id": "q2_age",
        "category": "basic",
        "question": "你的年龄区间？",
        "options": [
            {"label": "18-25岁", "scores": {"time_horizon_score": 9}},
            {"label": "26-35岁", "scores": {"time_horizon_score": 8}},
            {"label": "36-45岁", "scores": {"time_horizon_score": 6}},
            {"label": "46-55岁", "scores": {"time_horizon_score": 4}},
            {"label": "55岁以上", "scores": {"time_horizon_score": 2}},
        ],
    },
    {
        "id": "q3_experience",
        "category": "basic",
        "question": "你买过哪些投资产品？（可多选）",
        "multi": True,
        "options": [
            {"label": "银行理财/余额宝", "scores": {"experience_level": 2, "risk_tolerance": 3}},
            {"label": "基金", "scores": {"experience_level": 4, "risk_tolerance": 4}},
            {"label": "股票", "scores": {"experience_level": 6, "risk_tolerance": 6}},
            {"label": "期货/期权/加密货币", "scores": {"experience_level": 9, "risk_tolerance": 8}},
        ],
    },
    {
        "id": "q4_income_stability",
        "category": "basic",
        "question": "你的月收入稳定性如何？",
        "options": [
            {"label": "自由职业/不稳定", "scores": {"income_stability": 2}},
            {"label": "一般，偶尔波动", "scores": {"income_stability": 4}},
            {"label": "较稳定，偶有奖金", "scores": {"income_stability": 6}},
            {"label": "非常稳定（公务员/大厂等）", "scores": {"income_stability": 9}},
        ],
    },
    {
        "id": "q5_debt_pressure",
        "category": "basic",
        "question": "每月还贷/负债占收入的比例？",
        "options": [
            {"label": "无负债", "scores": {"debt_pressure": 1, "security_need": 3}},
            {"label": "10%以下", "scores": {"debt_pressure": 2, "security_need": 4}},
            {"label": "10%-30%", "scores": {"debt_pressure": 5, "security_need": 6}},
            {"label": "30%-50%", "scores": {"debt_pressure": 7, "security_need": 8}},
            {"label": "50%以上", "scores": {"debt_pressure": 9, "security_need": 9}},
        ],
    },
    {
        "id": "q6_diversification",
        "category": "basic",
        "question": "你倾向于如何配置投资？",
        "options": [
            {"label": "只买一种（如只存银行或只买股票）", "scores": {"diversification_preference": 1}},
            {"label": "2-3种（如银行理财+基金）", "scores": {"diversification_preference": 4}},
            {"label": "4-5种（股票+债券+基金+黄金等）", "scores": {"diversification_preference": 7}},
            {"label": "全球多元配置（跨市场跨资产）", "scores": {"diversification_preference": 9}},
        ],
    },
    # ===== Step 2: 风险偏好 (6题) =====
    {
        "id": "q7_risk_tolerance",
        "category": "risk",
        "question": "你能接受的最大单年亏损是多少？",
        "options": [
            {"label": "不能亏，保本第一", "scores": {"risk_tolerance": 1, "loss_aversion": 9}},
            {"label": "5%以内", "scores": {"risk_tolerance": 3, "loss_aversion": 7}},
            {"label": "10%-20%", "scores": {"risk_tolerance": 6, "loss_aversion": 4}},
            {"label": "20%-30%", "scores": {"risk_tolerance": 8, "loss_aversion": 2}},
            {"label": "30%以上，能扛住", "scores": {"risk_tolerance": 9, "loss_aversion": 1}},
        ],
    },
    {
        "id": "q8_stop_loss",
        "category": "risk",
        "question": "买入前是否会设定止损点（如跌10%就卖）？",
        "options": [
            {"label": "从不设止损", "scores": {"stop_loss_discipline": 1, "emotional_stability": 3}},
            {"label": "想过但没执行过", "scores": {"stop_loss_discipline": 3, "emotional_stability": 4}},
            {"label": "偶尔执行", "scores": {"stop_loss_discipline": 6, "emotional_stability": 6}},
            {"label": "严格执行，触达就卖", "scores": {"stop_loss_discipline": 9, "emotional_stability": 8}},
        ],
    },
    {
        "id": "q9_loss_scenario",
        "category": "risk",
        "question": "持仓跌20%后，你的第一反应是？",
        "options": [
            {"label": "立刻全部清仓", "scores": {"loss_aversion": 9, "emergency_response": 9, "emotional_stability": 2}},
            {"label": "减仓一半", "scores": {"loss_aversion": 6, "emergency_response": 6, "emotional_stability": 4}},
            {"label": "不动，等反弹", "scores": {"loss_aversion": 4, "emergency_response": 3, "emotional_stability": 5}},
            {"label": "加仓摊低成本", "scores": {"loss_aversion": 2, "emergency_response": 1, "emotional_stability": 6}},
            {"label": "检查基本面，再决定", "scores": {"loss_aversion": 3, "emergency_response": 2, "information_processing": 7, "emotional_stability": 8}},
        ],
    },
    {
        "id": "q10_anchoring",
        "category": "risk",
        "question": "10元买入跌到7元，涨回9元，你会？",
        "options": [
            {"label": "解套就卖，再也不碰", "scores": {"anchoring_effect": 9, "loss_aversion": 8}},
            {"label": "等涨回10元再卖", "scores": {"anchoring_effect": 7, "loss_aversion": 5}},
            {"label": "看趋势决定，不纠结成本", "scores": {"anchoring_effect": 2, "loss_aversion": 2, "information_processing": 6}},
            {"label": "该加仓，便宜了", "scores": {"anchoring_effect": 1, "loss_aversion": 1, "risk_tolerance": 8}},
        ],
    },
    {
        "id": "q11_time_horizon",
        "category": "risk",
        "question": "你能接受多久看不到明显收益？",
        "options": [
            {"label": "1个月", "scores": {"time_horizon_score": 2, "delayed_gratification": 2}},
            {"label": "3个月", "scores": {"time_horizon_score": 4, "delayed_gratification": 4}},
            {"label": "1年", "scores": {"time_horizon_score": 7, "delayed_gratification": 6}},
            {"label": "3年以上", "scores": {"time_horizon_score": 9, "delayed_gratification": 9}},
        ],
    },
    {
        "id": "q12_security_need",
        "category": "risk",
        "question": "急用3万时，你的投资账户能否立刻拿出？",
        "options": [
            {"label": "完全没问题，随时可取", "scores": {"security_need": 2, "capital_tier": 8}},
            {"label": "要卖一部分投资", "scores": {"security_need": 5, "capital_tier": 5}},
            {"label": "凑不齐，大部分都在投资里", "scores": {"security_need": 8, "capital_tier": 3}},
            {"label": "没想过这问题", "scores": {"security_need": 6, "capital_tier": 4}},
        ],
    },
    # ===== Step 3: 行为特征 (6题) =====
    {
        "id": "q13_herding",
        "category": "behavior",
        "question": "朋友说某股票涨了30%，你的反应是？",
        "options": [
            {"label": "马上跟买，怕错过", "scores": {"herding_tendency": 9, "information_processing": 2, "overconfidence": 5}},
            {"label": "先研究一下再决定", "scores": {"herding_tendency": 4, "information_processing": 7, "overconfidence": 4}},
            {"label": "不为所动，有自己的判断", "scores": {"herding_tendency": 2, "information_processing": 8, "overconfidence": 3}},
            {"label": "觉得涨多了该卖了，不会追高", "scores": {"herding_tendency": 5, "information_processing": 6, "overconfidence": 4}},
        ],
    },
    {
        "id": "q14_overconfidence",
        "category": "behavior",
        "question": "连续3个月盈利20%，你觉得主要原因是？",
        "options": [
            {"label": "我眼光好，有天赋", "scores": {"overconfidence": 9, "information_processing": 2}},
            {"label": "我做了研究，方法对", "scores": {"overconfidence": 6, "information_processing": 6}},
            {"label": "市场好，运气好", "scores": {"overconfidence": 2, "information_processing": 7}},
            {"label": "样本太小，不能说明什么", "scores": {"overconfidence": 1, "information_processing": 9}},
        ],
    },
    {
        "id": "q15_info_processing",
        "category": "behavior",
        "question": "看到一条投资相关新闻，你会？",
        "options": [
            {"label": "立刻据此操作", "scores": {"information_processing": 1, "herding_tendency": 7, "overconfidence": 6}},
            {"label": "查一下消息来源是否可靠", "scores": {"information_processing": 5, "herding_tendency": 4, "overconfidence": 4}},
            {"label": "结合多个来源交叉验证", "scores": {"information_processing": 8, "herding_tendency": 2, "overconfidence": 3}},
            {"label": "忽略，等市场消化后再看", "scores": {"information_processing": 7, "herding_tendency": 2, "overconfidence": 2}},
        ],
    },
    {
        "id": "q16_delayed_gratification",
        "category": "behavior",
        "question": "投资盈利10%后，你会？",
        "options": [
            {"label": "立刻卖出落袋为安", "scores": {"delayed_gratification": 2, "anchoring_effect": 7}},
            {"label": "卖出一半，留一半", "scores": {"delayed_gratification": 4, "anchoring_effect": 4}},
            {"label": "继续持有，等更高收益", "scores": {"delayed_gratification": 7, "anchoring_effect": 2}},
            {"label": "用利润再投入", "scores": {"delayed_gratification": 9, "anchoring_effect": 1}},
        ],
    },
    {
        "id": "q17_social_pressure",
        "category": "behavior",
        "question": "家人/朋友反对你的投资决策，你会？",
        "options": [
            {"label": "立刻停止，听他们的", "scores": {"social_pressure": 9, "herding_tendency": 7}},
            {"label": "减少投入，缓和矛盾", "scores": {"social_pressure": 6, "herding_tendency": 5}},
            {"label": "不受影响，按自己节奏", "scores": {"social_pressure": 2, "herding_tendency": 2}},
            {"label": "用数据和收益说服他们", "scores": {"social_pressure": 3, "herding_tendency": 2, "information_processing": 5}},
        ],
    },
    {
        "id": "q18_emotional_stability",
        "category": "behavior",
        "question": "连续3天亏损，累计跌15%，你会？",
        "options": [
            {"label": "恐慌清仓，再也不投", "scores": {"emotional_stability": 1, "emergency_response": 9, "loss_aversion": 9}},
            {"label": "焦虑但不动，不知道怎么办", "scores": {"emotional_stability": 3, "emergency_response": 5, "loss_aversion": 6}},
            {"label": "暂停交易，冷静分析原因", "scores": {"emotional_stability": 7, "emergency_response": 3, "information_processing": 6}},
            {"label": "按计划执行，情绪不影响决策", "scores": {"emotional_stability": 9, "emergency_response": 1, "stop_loss_discipline": 8}},
        ],
    },
]

# 所有维度名 (18维)
DIMENSIONS = [
    "risk_tolerance", "loss_aversion", "herding_tendency",
    "overconfidence", "delayed_gratification", "security_need",
    "time_horizon_score", "experience_level", "capital_tier",
    "income_stability", "debt_pressure", "information_processing",
    "social_pressure", "emergency_response", "anchoring_effect",
    # NEW v2
    "diversification_preference", "stop_loss_discipline", "emotional_stability",
]


def _get_question_by_id(qid: str) -> dict[str, Any] | None:
    for q in QUESTIONS:
        if q["id"] == qid:
            return q
    return None


def _clamp(value: float, lo: float = 1.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def compute_profile_vector(answers: dict[str, Any]) -> dict[str, float]:
    """从问卷答案计算18维profile_vector.

    answers: {question_id: option_label | list[option_label]}
    单选题为字符串，多选题为字符串列表
    返回: {dimension: score(1-10)}
    """
    accumulators: dict[str, list[float]] = {d: [] for d in DIMENSIONS}

    for qid, selected in answers.items():
        q = _get_question_by_id(qid)
        if q is None:
            continue

        is_multi = q.get("multi", False)
        selected_labels = selected if is_multi and isinstance(selected, list) else [selected]

        # 多选题：累加所有选中选项的分数，然后取平均
        # 单选题：直接累加
        for label in selected_labels:
            selected_option = None
            for opt in q["options"]:
                if opt["label"] == label:
                    selected_option = opt
                    break

            if selected_option is None:
                continue

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
