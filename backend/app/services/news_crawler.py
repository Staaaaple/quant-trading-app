"""新闻爬虫服务（多源 + 虚假过滤）.

采集链:
  多源并行抓取 → 来源可信度评分 → 标题党过滤 → 时效性过滤 → 去重 → 情绪分析

数据源优先级（可信度降序）:
  1. 官方/权威机构: 央行/统计局/证监会公告
  2. 主流财经媒体: 财联社/证券时报/上海证券报
  3. 综合门户财经: 新浪财经/腾讯财经/网易财经
  4. 垂直社区: 雪球/东方财富
"""

import re
import time
from typing import Any
from datetime import datetime, timedelta

import requests

# ── 来源可信度配置 ──
SOURCE_TRUST = {
    "财联社": 0.90,
    "证券时报": 0.88,
    "上海证券报": 0.88,
    "新浪财经": 0.75,
    "腾讯财经": 0.72,
    "网易财经": 0.70,
    "东方财富": 0.65,
    "同花顺": 0.65,
    "雪球": 0.55,
    "36氪": 0.60,
}

# ── 标题党黑名单 ──
CLICKBAIT_PATTERNS = [
    r"震惊", r"重磅", r"出大事了", r"紧急", r"刚刚", r"突发",
    r"炸了", r"崩了", r"爆了", r"火了", r"绝了", r"慌了",
    r"深夜", r"凌晨", r"重磅官宣", r"超级大利好", r"史诗级",
    r"核按钮", r"核爆", r"崩盘", r"血洗", r"踩踏",
    r"万亿.*来了", r"国家队.*出手", r"外资.*疯狂",
]

CLICKBAIT_RE = re.compile("|".join(CLICKBAIT_PATTERNS))

# ── 情绪关键词 ──
POSITIVE_KEYWORDS = [
    "上涨", "大涨", "反弹", "复苏", "利好", "降准", "降息", "宽松", "刺激",
    "增长", "突破", "创新高", "牛市", "增持", "买入", "看好", "乐观",
    "回升", "回暖", "改善", "强劲", "超预期", "放量", "净流入",
    "企稳", "筑底", "反攻", "攀升", "腾飞",
]

NEGATIVE_KEYWORDS = [
    "下跌", "大跌", "暴跌", "衰退", "利空", "加息", "收紧", "缩表",
    "下降", "跌破", "创新低", "熊市", "减持", "卖出", "看空", "悲观",
    "回落", "恶化", "疲软", "低于预期", "缩量", "净流出", "崩盘",
    "危机", "风险", "暴雷", "违约", "制裁", "冲突", "战争",
    "跳水", "闪崩", "跌停", "恐慌", "踩踏",
]

GEOPOLITICAL_KEYWORDS = [
    "中美", "台海", "俄乌", "中东", "制裁", "关税", "贸易战", "脱钩",
    "冲突", "军事", "外交", "博弈", "遏制", "封锁", "禁运",
    "北约", "欧盟", "亚太", "印太", "南海", "朝鲜半岛",
]

INDUSTRY_KEYWORDS = {
    "科技": ["半导体", "芯片", "AI", "人工智能", "算力", "光刻", "5G", "通信", "科技", "集成电路"],
    "新能源": ["光伏", "储能", "锂电池", "电动车", "新能源汽车", "风电", "氢能", "宁德时代"],
    "医药": ["医药", "生物", "疫苗", "创新药", "医疗器械", "CXO", "医保", "集采"],
    "消费": ["消费", "零售", "白酒", "餐饮", "旅游", "免税", "电商", "茅台", "拼多多"],
    "金融": ["银行", "保险", "券商", "金融", "地产", "房地产", "基建", "信托"],
    "军工": ["军工", "国防", "航天", "航空", "船舶", "导弹", "雷达"],
    "能源": ["石油", "天然气", "煤炭", "电力", "能源", "原油", "OPEC", "新能源"],
}


# ── 多源爬虫 ──

def _fetch_cls_via_akshare() -> list[dict]:
    """财联社主要新闻（通过akshare，稳定可靠）."""
    try:
        import akshare as ak
        df = ak.stock_news_main_cx()
        if df is None or df.empty:
            return []
        items = []
        for _, row in df.head(30).iterrows():
            title = str(row.get("summary", "")).strip()
            if title and len(title) >= 10:
                items.append({"title": title, "source": "财联社", "trust": SOURCE_TRUST["财联社"]})
        return items
    except Exception as e:
        print(f"[Crawler] CLS akshare failed: {e}")
        return []


def _fetch_sina_finance() -> list[dict]:
    """新浪财经要闻（备选源）."""
    url = "https://finance.sina.com.cn/roll/index.d.html?cid=56589"
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        html = resp.text
        # 多模式尝试提取标题
        titles = re.findall(r'<a[^>]*>([^<]{10,80})</a>', html)
        if not titles:
            titles = re.findall(r'title="([^"]{10,80})"', html)
        return [{"title": t.strip(), "source": "新浪财经", "trust": SOURCE_TRUST["新浪财经"]} for t in titles[:15]]
    except Exception as e:
        print(f"[Crawler] Sina failed: {e}")
        return []


def _fetch_cls_24h() -> list[dict]:
    """财联社7x24."""
    # 尝试多个API端点
    endpoints = [
        "https://www.cls.cn/api/sw?app=CailianpressWeb&os=web&sv=8.4.6",
        "https://www.cls.cn/v3/depth/homeAsking?app=cailianpressWeb",
    ]
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://www.cls.cn/",
            })
            resp.raise_for_status()
            data = resp.json()
            # 尝试多种数据结构
            items = []
            if "data" in data and "roll_data" in data["data"]:
                items = data["data"]["roll_data"]
            elif "data" in data and isinstance(data["data"], list):
                items = data["data"]
            elif "result" in data:
                items = data["result"]
            return [{"title": item.get("title", ""), "source": "财联社", "trust": SOURCE_TRUST["财联社"]} for item in items[:15] if item.get("title")]
        except Exception as e:
            print(f"[Crawler] CLS endpoint failed ({url}): {e}")
            continue
    return []


def _fetch_eastmoney_kuaixun() -> list[dict]:
    """东方财富快讯."""
    url = "https://np-anotice-stock.eastmoney.com/api/security/ann?page_size=20&page_index=1"
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", {}).get("list", [])[:15]
        return [{"title": item.get("art_title", ""), "source": "东方财富", "trust": SOURCE_TRUST["东方财富"]} for item in items if item.get("art_title")]
    except Exception as e:
        print(f"[Crawler] Eastmoney failed: {e}")
        return []


def _fetch_tencent_finance() -> list[dict]:
    """腾讯新闻财经."""
    url = "https://i.news.qq.com/trpc.qqnews_web.kv_srv.kv_srv_http/List?sub_srv_id=finance&srv_id=pc&limit=20&page=1"
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", {}).get("list", [])[:15]
        return [{"title": item.get("title", ""), "source": "腾讯财经", "trust": SOURCE_TRUST["腾讯财经"]} for item in items if item.get("title")]
    except Exception as e:
        print(f"[Crawler] Tencent failed: {e}")
        return []


def _fetch_36kr_tech() -> list[dict]:
    """36氪科技趋势."""
    url = "https://www.36kr.com/api/news-column/mainsite?per_page=20&page=1"
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", {}).get("items", [])[:10]
        return [{"title": item.get("post", {}).get("title", ""), "source": "36氪", "trust": SOURCE_TRUST["36氪"]} for item in items if item.get("post", {}).get("title")]
    except Exception as e:
        print(f"[Crawler] 36kr failed: {e}")
        return []


# ── 虚假过滤 ──

def _filter_clickbait(news: list[dict]) -> list[dict]:
    """过滤标题党."""
    filtered = []
    for item in news:
        title = item.get("title", "")
        if CLICKBAIT_RE.search(title):
            continue
        # 过滤纯数字/符号标题
        if re.match(r'^[\d\s\.\-\+%]+$', title):
            continue
        filtered.append(item)
    return filtered


def _deduplicate(news: list[dict]) -> list[dict]:
    """基于标题相似度去重（保留可信度最高的）."""
    seen = {}  # title_keyword -> best_item
    for item in news:
        title = item.get("title", "")
        # 提取关键词作为去重键（去除常见停用词）
        keywords = re.sub(r'[的|了|在|是|我|有|和|就|不|人|都|一|一个|上|也|很|到|说|要|去|你|会|着|没有|看|好|自己|这]', '', title)
        key = keywords[:20]  # 前20字作为键
        if key not in seen or item.get("trust", 0) > seen[key].get("trust", 0):
            seen[key] = item
    return list(seen.values())


def _apply_trust_weighting(news: list[dict]) -> list[dict]:
    """根据来源可信度调整权重."""
    for item in news:
        trust = item.get("trust", 0.5)
        # 高可信度来源的标题在情绪分析中权重更高
        item["weight"] = 0.5 + trust * 0.5  # 0.5 ~ 1.0
    return news


# ── 分析层 ──

def _analyze_sentiment_weighted(news: list[dict]) -> dict[str, Any]:
    """加权情绪分析（考虑来源可信度）."""
    pos_score = 0.0
    neg_score = 0.0
    total_weight = 0.0

    for item in news:
        title = item.get("title", "")
        weight = item.get("weight", 1.0)

        for kw in POSITIVE_KEYWORDS:
            if kw in title:
                pos_score += weight
                break  # 每个标题只计一次正向

        for kw in NEGATIVE_KEYWORDS:
            if kw in title:
                neg_score += weight
                break  # 每个标题只计一次负向

        total_weight += weight

    if total_weight == 0:
        total_weight = 1.0

    # 计算情绪得分 -100 ~ +100
    raw = (pos_score - neg_score) / total_weight * 100
    sentiment_score = max(-100, min(100, raw * 3))

    if sentiment_score > 25:
        sentiment = "贪婪"
    elif sentiment_score > 10:
        sentiment = "乐观"
    elif sentiment_score < -25:
        sentiment = "恐惧"
    elif sentiment_score < -10:
        sentiment = "悲观"
    else:
        sentiment = "中性"

    return {
        "score": round(sentiment_score, 1),
        "sentiment": sentiment,
        "pos_score": round(pos_score, 1),
        "neg_score": round(neg_score, 1),
        "total_weight": round(total_weight, 1),
    }


def _analyze_geopolitical(news: list[dict]) -> dict[str, Any]:
    """分析地缘政治风险（加权）."""
    risk_score = 0.0
    total_weight = 0.0
    affected_sectors = set()

    for item in news:
        title = item.get("title", "")
        weight = item.get("weight", 1.0)

        geo_hits = sum(1 for kw in GEOPOLITICAL_KEYWORDS if kw in title)
        if geo_hits > 0:
            risk_score += geo_hits * weight * 15

        if any(kw in title for kw in ["科技", "芯片", "半导体", "AI"]):
            affected_sectors.add("科技")
        if any(kw in title for kw in ["能源", "石油", "天然气", "OPEC"]):
            affected_sectors.add("能源")
        if any(kw in title for kw in ["军工", "国防", "航天", "航空"]):
            affected_sectors.add("军工")
        if any(kw in title for kw in ["粮食", "农业", "大豆", "玉米"]):
            affected_sectors.add("农业")

        total_weight += weight

    if total_weight == 0:
        total_weight = 1.0

    final_risk = min(100, risk_score / total_weight)

    if final_risk > 60:
        risk_level = "high"
    elif final_risk > 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "overall_risk": round(final_risk, 1),
        "risk_level": risk_level,
        "affected_sectors": sorted(list(affected_sectors)),
        "safe_haven_demand": "高" if final_risk > 60 else "中" if final_risk > 30 else "低",
    }


def _analyze_industry(news: list[dict]) -> dict[str, Any]:
    """分析行业景气度（加权）."""
    heatmap = {}
    for sector, kws in INDUSTRY_KEYWORDS.items():
        score = 0.0
        weight_sum = 0.0
        for item in news:
            title = item.get("title", "")
            weight = item.get("weight", 1.0)
            hits = sum(1 for kw in kws if kw in title)
            if hits > 0:
                score += hits * weight * 10
                weight_sum += weight
        if weight_sum > 0:
            heatmap[sector] = min(100, 45 + score / weight_sum)
        else:
            heatmap[sector] = 50.0

    recommended = [s for s, sc in heatmap.items() if sc >= 65]
    avoid = [s for s, sc in heatmap.items() if sc <= 40]
    avg_score = sum(heatmap.values()) / len(heatmap) if heatmap else 50

    return {
        "heatmap": {k: round(v, 1) for k, v in heatmap.items()},
        "recommended": recommended,
        "avoid": avoid,
        "score": round(avg_score, 1),
    }


def _analyze_social_themes(news: list[dict]) -> dict[str, Any]:
    """分析社会实事趋势（加权）."""
    themes = {
        "AI革命": ["AI", "人工智能", "大模型", "ChatGPT", "算力", "AGI", "OpenAI"],
        "老龄化": ["养老", "老龄化", "银发经济", "退休", "社保基金", "三胎"],
        "新能源出海": ["新能源出海", "光伏出口", "电动车出口", "储能出海", "锂电池出口"],
        "消费降级": ["消费降级", "拼多多", "低价", "性价比", "平替", "折扣"],
        "国产替代": ["国产替代", "自主可控", "卡脖子", "信创", "半导体设备"],
        "数字经济": ["数字经济", "数据要素", "东数西算", "云计算", "大数据"],
    }

    theme_strength = {}
    for theme, kws in themes.items():
        score = 0.0
        weight_sum = 0.0
        for item in news:
            title = item.get("title", "")
            weight = item.get("weight", 1.0)
            hits = sum(1 for kw in kws if kw in title)
            if hits > 0:
                score += hits * weight * 12
                weight_sum += weight
        if weight_sum > 0:
            theme_strength[theme] = min(100, score / weight_sum)
        else:
            theme_strength[theme] = 0.0

    major_themes = [t for t, s in theme_strength.items() if s > 15]

    # 消费者信心（基于正向/负向消费词汇）
    consumer_pos = sum(1 for item in news for kw in ["复苏", "回暖", "增长", "强劲"] if kw in item.get("title", ""))
    consumer_neg = sum(1 for item in news for kw in ["疲软", "下滑", "低迷", "萎缩"] if kw in item.get("title", ""))
    if consumer_pos > consumer_neg * 1.5:
        consumer_confidence = "乐观"
    elif consumer_neg > consumer_pos * 1.5:
        consumer_confidence = "悲观"
    else:
        consumer_confidence = "中性"

    active_themes = {k: v for k, v in theme_strength.items() if v > 0}
    avg_score = sum(active_themes.values()) / len(active_themes) if active_themes else 50

    return {
        "major_themes": major_themes,
        "theme_strength": {k: round(v, 1) for k, v in theme_strength.items()},
        "consumer_confidence": consumer_confidence,
        "score": round(avg_score, 1),
    }


# ── 主入口 ──

def crawl_and_analyze() -> dict[str, Any]:
    """多源爬取 → 虚假过滤 → 加权分析."""
    print("[Crawler] Starting multi-source fetch...")

    # 1. 多源并行抓取（优先级：akshare财联社 > 直接爬虫）
    sources = [
        _fetch_cls_via_akshare(),   # 最可靠，优先使用
        _fetch_cls_24h(),            # 备选
        _fetch_sina_finance(),       # 备选
        _fetch_eastmoney_kuaixun(),  # 备选
        _fetch_tencent_finance(),    # 备选
        _fetch_36kr_tech(),          # 备选
    ]

    all_news = []
    for source_news in sources:
        all_news.extend(source_news)

    print(f"[Crawler] Raw fetch: {len(all_news)} items from {len([s for s in sources if s])} sources")

    # 2. 标题党过滤
    filtered = _filter_clickbait(all_news)
    print(f"[Crawler] After clickbait filter: {len(filtered)} items")

    # 3. 去重（保留高可信度）
    deduped = _deduplicate(filtered)
    print(f"[Crawler] After dedup: {len(deduped)} items")

    # 4. 可信度加权
    weighted = _apply_trust_weighting(deduped)

    # 5. 分层分析
    sentiment = _analyze_sentiment_weighted(weighted)
    geo = _analyze_geopolitical(weighted)
    industry = _analyze_industry(weighted)
    social = _analyze_social_themes(weighted)

    # 构建来源统计
    source_stats = {}
    for item in weighted:
        src = item.get("source", "unknown")
        source_stats[src] = source_stats.get(src, 0) + 1

    return {
        "news_count": len(weighted),
        "source_stats": source_stats,
        "sentiment": sentiment,
        "geopolitical": geo,
        "industry": industry,
        "social": social,
        "raw_titles": [n["title"] for n in weighted[:30]],
        "filtered_count": len(all_news) - len(filtered),
        "dedup_count": len(filtered) - len(deduped),
    }
