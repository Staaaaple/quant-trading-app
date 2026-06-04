"""多模型经济周期判断引擎（中国特供版）.

针对当前中国经济实际校准：
- 潜在GDP增速已降至4-5%，阈值相应下调
- PPI比CPI更能反映当前通缩压力（CPI受食品扰动大）
- 社融是信用环境的核心指标，必须纳入
- 房地产数据作为先行指标

融合三大模型：
1. 美林时钟（修正版）— GDP + CPI + PPI
2. 货币信用周期 — M2 + 社融 + 利率 + 房地产
3. 库存周期 — PMI + 工业企业利润 + PPI

输出：融合周期阶段 + 各模型独立判断 + 置信度
"""

from typing import Any


# ── 模型1：美林时钟（中国修正版）──

def merrill_lunch_clock(gdp_yoy: float, cpi_yoy: float, ppi_yoy: float | None = None) -> dict[str, Any]:
    """美林时钟修正版：基于经济增长和物价水平的四象限判断.

    中国特供调整：
      - GDP阈值：潜在增速4-5%，>4.5算高，<3.5算低
      - 纳入PPI：工业通缩比CPI更能反映实体经济
      - CPI阈值下调：当前低通胀环境，>2算高，<0算低
    """
    # 阈值（基于中国当前潜在增速和通缩现实调整）
    # 当前中国潜在增速已降至 4-5%，GDP>5.5 才算高，<4.0 算低
    GDP_HIGH = 5.5
    GDP_LOW = 4.0
    CPI_HIGH = 2.5
    CPI_LOW = 0.5  # CPI<0.5%算低通胀/通缩边缘

    # 综合通胀指标：CPI为主，PPI为辅（但PPI权重降低，避免工业短期波动干扰）
    inflation = cpi_yoy
    if ppi_yoy is not None:
        # PPI权重降低至30%，CPI更能反映消费端真实通胀
        inflation = cpi_yoy * 0.7 + ppi_yoy * 0.3

    if gdp_yoy >= GDP_HIGH and inflation >= CPI_LOW and inflation < CPI_HIGH:
        phase = "复苏"
        desc = "经济增速回升，通胀温和，企业盈利改善"
        asset_pref = "股票 > 债券 > 现金 > 商品"
        score = 75
    elif gdp_yoy >= GDP_HIGH and inflation >= CPI_HIGH:
        phase = "过热"
        desc = "经济偏热，通胀上行，需警惕政策收紧"
        asset_pref = "商品 > 股票 > 现金 > 债券"
        score = 55
    elif gdp_yoy < GDP_LOW and inflation >= CPI_HIGH:
        phase = "滞胀"
        desc = "经济放缓但通胀仍高，最痛苦的阶段"
        asset_pref = "现金 > 商品 > 债券 > 股票"
        score = 35
    elif gdp_yoy < GDP_LOW and inflation < CPI_LOW:
        phase = "衰退"
        desc = "经济下行+通缩，等待政策发力"
        asset_pref = "债券 > 现金 > 股票 > 商品"
        score = 35
    else:
        # GDP在4.0-5.5之间，通胀低迷 — 当前中国经济最可能的状态：弱复苏/衰退边缘
        phase = "弱复苏/衰退边缘"
        desc = "经济增速尚可但通胀低迷，复苏基础不牢"
        asset_pref = "债券 > 现金 > 股票 > 商品"
        score = 45

    return {
        "model": "美林时钟",
        "phase": phase,
        "description": desc,
        "asset_preference": asset_pref,
        "score": score,
        "inputs": {"gdp_yoy": gdp_yoy, "cpi_yoy": cpi_yoy, "ppi_yoy": ppi_yoy},
    }


# ── 模型2：货币信用周期（中国特供版）──

def monetary_credit_cycle(
    m2_yoy: float,
    social_financing_yoy: float | None,
    lpr_1y: float | None,
    lpr_prev: float | None,
    real_estate_investment_yoy: float | None = None,
) -> dict[str, Any]:
    """货币信用周期：基于货币政策和信用环境的四象限判断.

    中国特供调整：
      - 社融是核心指标，权重最高
      - 房地产投资作为信用环境的先行指标
      - 当前M2>8%即算宽松（过去标准是10%）
    """
    # 货币松紧判断（考虑实际利率，M2>8%算宽松，<7%算收紧）
    money_loose = m2_yoy >= 8.0
    if lpr_1y is not None and lpr_prev is not None:
        money_loose = money_loose or (lpr_1y < lpr_prev - 0.05)

    # 信用松紧判断（社融为核心，阈值调整）
    credit_loose = False
    credit_desc = ""

    if social_financing_yoy is not None:
        # 社融增速 > 10% 算信用扩张，< 0% 算信用收缩（负增长是强烈信号）
        if social_financing_yoy >= 10.0:
            credit_loose = True
        elif social_financing_yoy < 0.0:
            credit_loose = False  # 负增长 = 信用收缩
        elif social_financing_yoy < 5.0:
            credit_loose = False  # 低增长也算紧信用
        else:
            # 5-10% 灰色地带，看M2
            credit_loose = m2_yoy >= 9.0
        credit_desc = f"社融增速{social_financing_yoy}%"
    else:
        # 无社融数据时，用M2 proxy
        credit_loose = m2_yoy >= 9.0
        credit_desc = "M2替代指标"

    # 房地产作为信用环境的验证
    if real_estate_investment_yoy is not None:
        if real_estate_investment_yoy < -5:
            credit_desc += "，房地产投资负增长"
            # 房地产深度负增长时，信用环境实际偏紧
            if real_estate_investment_yoy < -10:
                credit_loose = False
        elif real_estate_investment_yoy > 5:
            credit_desc += "，房地产投资企稳"

    if money_loose and credit_loose:
        phase = "宽货币宽信用"
        desc = f"货币宽松+信用扩张，{credit_desc}，利好风险资产"
        asset_pref = "股票 > 债券 > 商品 > 现金"
        score = 80
    elif money_loose and not credit_loose:
        phase = "宽货币紧信用"
        desc = f"货币已宽松但信用传导不畅，{credit_desc}，政策效果待观察"
        asset_pref = "债券 > 现金 > 股票 > 商品"
        score = 45  # 信用收缩时降低评分
    elif not money_loose and credit_loose:
        phase = "紧货币宽信用"
        desc = f"信用仍扩张但货币边际收紧，{credit_desc}，警惕拐点"
        asset_pref = "商品 > 股票 > 现金 > 债券"
        score = 55
    else:
        phase = "紧货币紧信用"
        desc = f"双紧环境，{credit_desc}，防御为主"
        asset_pref = "现金 > 债券 > 商品 > 股票"
        score = 30  # 双紧时进一步降低评分

    return {
        "model": "货币信用周期",
        "phase": phase,
        "description": desc,
        "asset_preference": asset_pref,
        "score": score,
        "inputs": {
            "m2_yoy": m2_yoy,
            "social_financing_yoy": social_financing_yoy,
            "lpr_1y": lpr_1y,
            "real_estate_investment_yoy": real_estate_investment_yoy,
        },
    }


# ── 模型3：库存周期（中国特供版）──

def inventory_cycle(
    pmi: float | None,
    profit_yoy: float | None,
    ppi_yoy: float | None = None,
) -> dict[str, Any]:
    """库存周期：基于 PMI、工业企业利润和 PPI 的四阶段判断.

    中国特供调整：
      - 纳入PPI：价格信号比库存本身更领先
      - PMI>49.5算扩张（不是50，因为中国PMI长期偏低）
      - 利润负增长是常态，>-5%就算改善
    """
    # 默认：数据不足
    phase = "观察期"
    desc = "库存数据不足，建议结合其他模型判断"
    asset_pref = "均衡配置"
    score = 50

    # 有利润数据时的判断
    if profit_yoy is not None:
        # 利润判断阈值下调：当前环境下>-5%就算改善
        profit_growing = profit_yoy > -5.0

        # PMI判断阈值下调至49.5
        if pmi is not None:
            inventory_building = pmi >= 49.5

            # 纳入PPI：PPI回升通常领先库存周期1-2个季度
            ppi_rising = None
            if ppi_yoy is not None:
                ppi_rising = ppi_yoy > -2.0  # PPI>-2%算价格企稳

            if inventory_building and profit_growing:
                if ppi_rising is True:
                    phase = "主动补库"
                    desc = "企业主动补库，PPI回升，需求+价格双改善，经济上行"
                    asset_pref = "股票 > 商品 > 债券 > 现金"
                    score = 85
                else:
                    phase = "补库初期"
                    desc = "库存回升但价格仍弱，复苏尚不稳固"
                    asset_pref = "股票 > 债券 > 现金 > 商品"
                    score = 60
            elif inventory_building and not profit_growing:
                phase = "被动补库"
                desc = "需求放缓但库存仍在增加，警惕库存积压风险"
                asset_pref = "现金 > 债券 > 商品 > 股票"
                score = 35
            elif not inventory_building and not profit_growing:
                if ppi_rising is False:
                    phase = "主动去库"
                    desc = "企业主动去库存，PPI低迷，经济下行期"
                    asset_pref = "债券 > 现金 > 股票 > 商品"
                    score = 30
                else:
                    phase = "去库后期"
                    desc = "库存去化中，PPI已企稳，接近拐点"
                    asset_pref = "债券 > 股票 > 现金 > 商品"
                    score = 50
            else:
                # 不补库但利润改善 = 被动去库/复苏前夜
                if ppi_rising is True:
                    phase = "被动去库"
                    desc = "需求回升+价格企稳，库存仍低，复苏前夜"
                    asset_pref = "股票 > 债券 > 现金 > 商品"
                    score = 75
                else:
                    phase = "利润修复"
                    desc = "利润边际改善但价格仍弱，复苏初期"
                    asset_pref = "股票 > 债券 > 现金 > 商品"
                    score = 55
        else:
            # 只有利润数据
            if profit_growing:
                phase = "利润改善"
                desc = "企业盈利边际改善，经济有企稳迹象"
                asset_pref = "股票 > 债券 > 现金 > 商品"
                score = 55
            else:
                phase = "利润承压"
                desc = "企业盈利仍承压，经济尚未企稳"
                asset_pref = "债券 > 现金 > 股票 > 商品"
                score = 35

    return {
        "model": "库存周期",
        "phase": phase,
        "description": desc,
        "asset_preference": asset_pref,
        "score": score,
        "inputs": {
            "pmi": pmi,
            "profit_yoy": profit_yoy,
            "ppi_yoy": ppi_yoy,
        },
    }


# ── 融合引擎（中国特供版）──

# 周期阶段映射到统一坐标系
_PHASE_MAP = {
    # 美林时钟
    "复苏": {"growth": 0.8, "inflation": -0.5, "liquidity": 0.5, "confidence": 0.7},
    "过热": {"growth": 1, "inflation": 1, "liquidity": -0.5, "confidence": 0.6},
    "滞胀": {"growth": -0.5, "inflation": 0.8, "liquidity": -1, "confidence": 0.2},
    "衰退": {"growth": -0.8, "inflation": -0.8, "liquidity": 0, "confidence": 0.4},
    "弱复苏/衰退边缘": {"growth": 0, "inflation": -0.5, "liquidity": 0, "confidence": 0.3},
    # 货币信用周期
    "宽货币宽信用": {"growth": 0.8, "inflation": 0, "liquidity": 1, "confidence": 0.9},
    "宽货币紧信用": {"growth": -0.3, "inflation": -0.5, "liquidity": -0.3, "confidence": 0.4},
    "紧货币宽信用": {"growth": 0.5, "inflation": 0.3, "liquidity": -0.3, "confidence": 0.5},
    "紧货币紧信用": {"growth": -0.8, "inflation": -0.5, "liquidity": -1, "confidence": 0.1},
    # 库存周期
    "主动补库": {"growth": 1, "inflation": 0.5, "liquidity": 0.5, "confidence": 0.9},
    "补库初期": {"growth": 0.5, "inflation": -0.3, "liquidity": 0.3, "confidence": 0.5},
    "被动补库": {"growth": -0.3, "inflation": 0, "liquidity": -0.3, "confidence": 0.3},
    "主动去库": {"growth": -0.8, "inflation": -0.5, "liquidity": -0.5, "confidence": 0.2},
    "去库后期": {"growth": -0.3, "inflation": -0.3, "liquidity": 0, "confidence": 0.4},
    "被动去库": {"growth": 0.5, "inflation": -0.3, "liquidity": 0.3, "confidence": 0.7},
    "利润修复": {"growth": 0.3, "inflation": -0.5, "liquidity": 0, "confidence": 0.5},
    "利润改善": {"growth": 0.3, "inflation": -0.3, "liquidity": 0, "confidence": 0.5},
    "利润承压": {"growth": -0.5, "inflation": -0.5, "liquidity": -0.3, "confidence": 0.3},
    "观察期": {"growth": 0, "inflation": 0, "liquidity": 0, "confidence": 0.3},
}

# 模型权重（当前环境下货币信用周期权重更高）
_MODEL_WEIGHTS = {
    "美林时钟": 0.25,
    "货币信用周期": 0.45,
    "库存周期": 0.30,
}


def fuse_cycle_phases(results: list[dict[str, Any]]) -> dict[str, Any]:
    """融合三大模型输出，得出最终周期判断.

    中国特供调整：
      - 货币信用周期权重提升至45%（当前信用环境是核心矛盾）
      - 衰退/复苏早期阈值放宽（当前经济处于弱复苏/衰退后期）
      - 输出更细分的阶段判断
    """
    # 加权求和
    total_weight = 0.0
    fused = {"growth": 0.0, "inflation": 0.0, "liquidity": 0.0, "confidence": 0.0}

    for r in results:
        model_name = r["model"]
        phase = r["phase"]
        weight = _MODEL_WEIGHTS.get(model_name, 0.33)
        coords = _PHASE_MAP.get(phase, _PHASE_MAP["观察期"])

        for dim in fused:
            fused[dim] += coords[dim] * weight
        total_weight += weight

    # 归一化
    if total_weight > 0:
        for dim in fused:
            fused[dim] /= total_weight

    # 根据融合坐标判断最接近的周期阶段
    growth = fused["growth"]
    inflation = fused["inflation"]
    liquidity = fused["liquidity"]

    # 更细分的阶段判断（阈值调整，贴合中国当前实际）
    # 优先级：衰退信号优先于复苏信号
    # 当信用大幅收缩（liquidity < -0.1）且增长疲软时，判定为衰退
    if growth < 0 and inflation < 0 and liquidity < -0.1:
        final_phase = "深度衰退"
        final_desc = "经济下行+通缩+信用收缩，债券和现金优先"
        final_asset = "债券 > 现金 > 商品 > 股票"
    elif growth < 0.2 and inflation < 0 and liquidity < -0.1:
        final_phase = "衰退"
        final_desc = "经济疲软+信用收缩，等待政策发力"
        final_asset = "债券 > 现金 > 股票 > 商品"
    elif growth < 0 and inflation < 0 and liquidity >= 0:
        final_phase = "衰退后期"
        final_desc = "经济仍弱但货币已宽松，关注政策效果"
        final_asset = "债券 > 现金 > 股票 > 商品"
    elif growth < 0 and inflation >= 0:
        final_phase = "滞胀"
        final_desc = "经济放缓但通胀仍高，防御为主"
        final_asset = "现金 > 商品 > 债券 > 股票"
    elif growth < 0.2 and inflation < 0 and liquidity > 0:
        final_phase = "衰退向复苏过渡"
        final_desc = "经济筑底中，货币已宽松，等待信用扩张"
        final_asset = "债券 > 股票 > 现金 > 商品"
    elif growth >= 0.5 and inflation >= 0.2:
        final_phase = "过热"
        final_desc = "经济偏热，通胀上行，需警惕政策收紧"
        final_asset = "商品 > 股票 > 现金 > 债券"
    elif growth >= 0.3 and inflation < 0 and liquidity > 0.3:
        final_phase = "复苏"
        final_desc = "经济复苏，流动性充裕，适合增配股票"
        final_asset = "股票 > 债券 > 现金 > 商品"
    elif growth >= 0 and inflation < 0 and liquidity > 0:
        final_phase = "弱复苏"
        final_desc = "复苏迹象初现但不稳固，逐步增加风险资产"
        final_asset = "股票 > 债券 > 现金 > 商品"
    else:
        final_phase = "周期底部"
        final_desc = "多重信号交织，周期方向待确认，均衡配置"
        final_asset = "均衡配置"

    # 置信度 = 模型一致性 × 数据完整度
    model_scores = [r["score"] for r in results]
    score_variance = max(model_scores) - min(model_scores)
    consistency = max(0, 1 - score_variance / 100)
    data_completeness = len([r for r in results if r["phase"] != "观察期"]) / len(results)
    confidence = round(consistency * data_completeness * 100, 1)

    return {
        "final_phase": final_phase,
        "final_description": final_desc,
        "final_asset_preference": final_asset,
        "confidence": confidence,
        "fused_coordinates": {k: round(v, 2) for k, v in fused.items()},
        "model_results": results,
        "consistency": round(consistency * 100, 1),
        "data_completeness": round(data_completeness * 100, 1),
    }
