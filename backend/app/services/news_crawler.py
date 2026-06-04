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

# ── 情绪关键词（大幅扩充） ──
POSITIVE_KEYWORDS = [
    # 价格上涨
    "上涨", "大涨", "反弹", "回升", "回暖", "攀升", "腾飞", "冲高", "拉升", "走强",
    "创新高", "突破", "站上", "收复", "企稳", "筑底", "反攻", "逆袭", "翻红",
    # 政策利好
    "利好", "降准", "降息", "宽松", "刺激", "支持", "扶持", "鼓励", "减税", "降费",
    "放水", "流动性", "资金流入", "北向资金", "外资流入", "主力流入", "净流入",
    # 业绩向好
    "增长", "强劲", "超预期", "盈利", "利润增长", "营收增长", "业绩大增",
    "扭亏为盈", "盈利能力", "毛利率提升", "净利率提升",
    # 市场信心
    "牛市", "增持", "买入", "看好", "乐观", "信心", "积极", "正面", "看好后市",
    "目标价上调", "评级上调", "买入评级", "强烈推荐", "推荐",
    # 交易活跃
    "放量", "放量上涨", "量价齐升", "成交活跃", "换手率上升", "资金追捧",
    # 宏观向好
    "经济复苏", "GDP增长", "PMI扩张", "景气度提升", "繁荣", "扩张",
]

NEGATIVE_KEYWORDS = [
    # 价格下跌
    "下跌", "大跌", "暴跌", "重挫", "跳水", "闪崩", "跌停", "崩盘", "腰斩",
    "创新低", "跌破", "失守", "下探", "走低", "走弱", "回落", "回调", "阴跌",
    # 政策利空
    "利空", "加息", "收紧", "缩表", "退市", "监管", "处罚", "调查", "立案",
    "减持", "大股东减持", "限售解禁", "IPO提速", "抽血", "资金流出", "净流出",
    # 业绩恶化
    "下降", "下滑", "亏损", "亏损扩大", "业绩暴雷", "商誉减值", "存货跌价",
    "应收账款", "现金流紧张", "资不抵债", "ST", "*ST", "退市风险",
    # 市场恐慌
    "熊市", "卖出", "看空", "悲观", "恐慌", "踩踏", "抛售", "清仓", "割肉",
    "目标价下调", "评级下调", "卖出评级", "回避", "看空后市",
    # 交易萎缩
    "缩量", "缩量下跌", "量价背离", "成交清淡", "地量", "无人问津",
    # 宏观恶化
    "衰退", "经济下滑", "GDP放缓", "PMI收缩", "通缩", "滞胀", "硬着陆",
    "危机", "风险", "暴雷", "违约", "债务违约", "信用风险", "流动性危机",
    # 地缘政治
    "制裁", "冲突", "战争", "军事打击", "导弹", "空袭", "断交", "驱逐",
]

# ── 地缘政治关键词（大幅扩充） ──
GEOPOLITICAL_KEYWORDS = [
    # 中美关系
    "中美", "中美关系", "中美贸易", "中美博弈", "中美对抗", "脱钩", "去风险",
    "芯片禁令", "技术封锁", "实体清单", "关税", "贸易战", "301调查",
    # 台海
    "台海", "台湾", "台独", "两岸", "军演", "围台", "锁台", "飞越中线",
    # 俄乌
    "俄乌", "俄罗斯", "乌克兰", "普京", "泽连斯基", "北约", "欧盟制裁",
    "能源禁运", "天然气断供", "石油禁运",
    # 中东
    "中东", "以色列", "巴勒斯坦", "加沙", "哈马斯", "真主党", "伊朗",
    "沙特", "也门", "胡塞", "红海", "霍尔木兹", "石油设施", "核设施",
    # 其他地区
    "朝鲜半岛", "朝鲜", "韩国", "金正恩", "核试验", "导弹试射",
    "南海", "菲律宾", "越南", "印度", "中印", "边境冲突",
    "阿富汗", "塔利班", "巴基斯坦", "恐袭",
    # 通用冲突词汇
    "军事冲突", "武装冲突", "战争风险", "军事打击", "空袭", "导弹袭击",
    "制裁", "封锁", "禁运", "断交", "外交危机", "紧张局势", "升级",
    "撤侨", "紧急状态", "战时状态", "动员",
]

# ── 行业关键词（大幅扩充） ──
INDUSTRY_KEYWORDS = {
    "科技": [
        "半导体", "芯片", "集成电路", "晶圆", "光刻", "光刻机", "ASML", "EUV",
        "AI", "人工智能", "大模型", "ChatGPT", "GPT", "OpenAI", "算力", "智算",
        "AIGC", "生成式AI", "机器学习", "深度学习", "神经网络", "Transformer",
        "5G", "6G", "通信", "基站", "光模块", "CPO", "光通信", "光纤",
        "云计算", "数据中心", "IDC", "边缘计算", "量子计算",
        "物联网", "工业互联网", "智能制造", "机器人", "人形机器人", "工业机器人",
        "消费电子", "智能手机", "苹果", "华为", "小米", "特斯拉",
        "软件", "SaaS", "操作系统", "数据库", "中间件",
    ],
    "新能源": [
        "光伏", "太阳能", "储能", "锂电池", "宁德时代", "比亚迪", "磷酸铁锂",
        "固态电池", "钠离子电池", "氢能", "燃料电池", "电解槽",
        "电动车", "新能源汽车", "电动汽车", "充电桩", "换电", "智能驾驶",
        "风电", "海上风电", "陆上风电", "风机", "叶片",
        "电网", "特高压", "智能电网", "虚拟电厂", "电力市场化",
        "ESG", "碳中和", "碳达峰", "绿电", "绿证",
    ],
    "医药": [
        "医药", "生物医药", "创新药", "仿制药", "CXO", "CRO", "CDMO",
        "疫苗", "mRNA", "基因治疗", "细胞治疗", "CAR-T",
        "医疗器械", "医疗耗材", "体外诊断", "IVD", "医学影像",
        "医保", "集采", "带量采购", "医保谈判", "医保目录",
        "中药", "中医药", "配方颗粒",
        "医美", "医疗美容", "玻尿酸", "肉毒素",
        "老龄化", "银发经济", "康复", "护理",
    ],
    "消费": [
        "消费", "消费升级", "消费降级", "新零售", "电商", "直播带货",
        "白酒", "茅台", "五粮液", "泸州老窖", "啤酒", "葡萄酒",
        "餐饮", "火锅", "奶茶", "咖啡", "预制菜",
        "旅游", "酒店", "航空", "免税", "海南免税", "出境游",
        "家电", "白电", "黑电", "小家电", "智能家居",
        "服装", "纺织", "运动品牌", "安踏", "李宁", "耐克",
        "美妆", "化妆品", "护肤品", "珀莱雅", "贝泰妮",
        "宠物", "宠物食品", "宠物医疗",
    ],
    "金融": [
        "银行", "国有大行", "股份制银行", "城商行", "农商行",
        "保险", "寿险", "财险", "健康险", "代理人",
        "券商", "投行", "经纪业务", "财富管理", "资管",
        "地产", "房地产", "房地产开发", "物业管理", "REITs",
        "信托", "AMC", "不良资产",
        "金融科技", "数字人民币", "移动支付", "区块链",
    ],
    "军工": [
        "军工", "国防", "国防预算", "军费", "武器装备",
        "航天", "航空", "卫星", "北斗", "空间站", "载人航天",
        "船舶", "航母", "驱逐舰", "潜艇", "核潜艇",
        "导弹", "雷达", "电子对抗", "隐身", "无人机",
        "军工集团", "中航", "中船", "中兵",
    ],
    "能源": [
        "石油", "原油", "布伦特", "WTI", "OPEC", "欧佩克", "页岩油",
        "天然气", "LNG", "管道气", "储气",
        "煤炭", "动力煤", "焦煤", "焦炭", "煤化工",
        "电力", "火电", "水电", "核电", "风电", "光伏", "储能",
        "电网", "国网", "南网", "特高压",
        "稀土", "锂矿", "钴", "镍", "铜", "铝", "铁矿石",
    ],
    "汽车": [
        "汽车", "整车", "乘用车", "商用车", "SUV", "轿车",
        "新能源汽车", "电动车", "混动车", "插电混动", "增程式",
        "智能驾驶", "自动驾驶", "激光雷达", "毫米波雷达", "高精地图",
        "汽车零部件", "轮胎", "玻璃", "座椅", "车灯",
        "特斯拉", "比亚迪", "蔚来", "小鹏", "理想", "问界", "小米汽车",
    ],
    "传媒": [
        "传媒", "影视", "电影", "票房", "院线", "流媒体", "Netflix",
        "游戏", "手游", "端游", "版号", "王者荣耀", "原神",
        "短视频", "抖音", "快手", "直播", "MCN",
        "广告", "营销", "品牌", "IP", "元宇宙", "VR", "AR",
    ],
    "农业": [
        "农业", "种植业", "粮食", "大豆", "玉米", "小麦", "水稻",
        "猪肉", "生猪", "养殖", "饲料", "动保", "兽药",
        "种业", "转基因", "种子", "化肥", "农药",
        "乡村振兴", "三农",
    ],
}

# ── 社会主题关键词（大幅扩充） ──
SOCIAL_THEMES = {
    "AI革命": [
        "AI", "人工智能", "大模型", "ChatGPT", "GPT-4", "GPT-5", "OpenAI",
        "算力", "智算中心", "AI芯片", "英伟达", "NVIDIA", "黄仁勋",
        "AIGC", "生成式AI", "Sora", "文生视频", "AI绘画", "Midjourney",
        "AI应用", "AI医疗", "AI教育", "AI金融", "AI办公", "Copilot",
        "人形机器人", "具身智能", "Figure", "特斯拉机器人", "Optimus",
        "AI安全", "AI监管", "AI伦理", "深度伪造", "deepfake",
    ],
    "老龄化": [
        "养老", "老龄化", "银发经济", "退休金", "社保基金", "养老金",
        "三胎", "生育", "人口", "出生率", "人口负增长", "少子化",
        "护理", "康复", "医养结合", "养老院", "居家养老",
        "延迟退休", "退休年龄", "社保缺口",
    ],
    "新能源出海": [
        "新能源出海", "光伏出口", "储能出口", "电动车出口", "锂电池出口",
        "一带一路", "海外建厂", "欧洲市场", "东南亚市场", "中东市场",
        "关税壁垒", "贸易保护", "反倾销", "碳关税",
    ],
    "消费降级": [
        "消费降级", "拼多多", "低价", "性价比", "平替", "折扣", "临期",
        "反向消费", "理性消费", "省钱", "抠门经济", "二手经济",
        "蜜雪冰城", "名创优品", "优衣库", "萨莉亚",
        "消费疲软", "消费低迷", "不敢消费", "储蓄率", "预防性储蓄",
    ],
    "国产替代": [
        "国产替代", "自主可控", "卡脖子", "信创", "去美化",
        "鸿蒙", "麒麟芯片", "龙芯", "飞腾", "海光", "兆芯",
        "工业软件", "EDA", "CAD", "CAE", "操作系统", "数据库",
        "供应链安全", "产业链安全", "内循环",
    ],
    "数字经济": [
        "数字经济", "数据要素", "数据资产", "数据交易", "东数西算",
        "数字人民币", "e-CNY", "央行数字货币", "区块链", "Web3",
        "智慧城市", "数字政府", "数字孪生", "工业互联网",
        "平台经济", "反垄断", "数据安全", "个人信息保护",
    ],
    "绿色转型": [
        "碳中和", "碳达峰", "双碳", "ESG", "绿色金融", "碳交易",
        "碳市场", "CCER", "碳汇", "碳捕集", "CCUS",
        "绿色建筑", "新能源汽车", "光伏", "风电",
        "环保", "污染治理", "新能源补贴", "退补",
    ],
    "全球化重构": [
        "全球化", "逆全球化", "供应链重构", "近岸外包", "友岸外包",
        "区域全面经济伙伴关系", "RCEP", "CPTPP", "一带一路",
        "金砖国家", "上合组织", "G7", "G20",
        "中美脱钩", "技术脱钩", "金融脱钩", "制裁", "封锁",
    ],
    "房地产调整": [
        "房地产", "楼市", "房价", "房价下跌", "房价泡沫", "去库存",
        "限购", "限贷", "房贷利率", "首付比例", "认房不认贷",
        "恒大", "碧桂园", "万科", "房企暴雷", "债务违约",
        "保交楼", "烂尾楼", "房产税", "土地财政",
    ],
    "就业压力": [
        "就业", "失业", "失业率", "青年失业", "大学生就业",
        "裁员", "优化", "毕业", "降薪", "灵活就业",
        "考公", "考研", "考编", "体制内", "铁饭碗",
        "招聘", "求职", "简历", "面试", "零工经济",
    ],
    "教育改革": [
        "教育", "教培", "双减", "课外辅导", "补习班", "学区房",
        "高考", "中考", "考研", "留学", "海归",
        "职业教育", "技能培训", "终身学习", "在线教育",
        "教育公平", "教育减负", "素质教育",
    ],
    "医疗改革": [
        "医疗", "医改", "医保", "集采", "带量采购", "医保谈判",
        "看病贵", "看病难", "分级诊疗", "家庭医生",
        "公立医院", "民营医院", "互联网医疗", "远程医疗",
        "药品价格", "医疗器械", "创新药", "仿制药",
    ],
    "共同富裕": [
        "共同富裕", "收入分配", "贫富差距", "基尼系数",
        "三次分配", "慈善", "捐赠", "富豪税",
        "中产阶级", "阶层固化", "向上流动", "社会公平",
        "最低工资标准", "个税改革", "房地产税",
    ],
    "地方债务": [
        "地方债", "城投债", "地方政府债务", "隐性债务",
        "专项债", "化债", "债务置换", "债务风险",
        "财政赤字", "转移支付", "土地财政", "税源",
        "基建投资", "PPP", "政府投资",
    ],
}


# ── 多源爬虫 ──

def _extract_date_from_url(url: str) -> datetime | None:
    """从URL中提取日期（财联社URL格式: .../2026-06-04/...）."""
    import re
    match = re.search(r'/(\d{4})-(\d{2})-(\d{2})/', url)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        # 处理未来日期（akshare可能返回模拟数据）
        from datetime import datetime
        dt = datetime(year, month, day)
        # 如果日期在未来，回退到当前日期
        now = datetime.now()
        if dt > now:
            return now
        return dt
    return None


def _fetch_cls_via_akshare() -> list[dict]:
    """财联社主要新闻（通过akshare，稳定可靠）."""
    from datetime import datetime, timedelta
    try:
        import akshare as ak
        df = ak.stock_news_main_cx()
        if df is None or df.empty:
            return []
        items = []
        cutoff = datetime.now() - timedelta(days=14)  # 两周内
        for _, row in df.head(100).iterrows():
            title = str(row.get("summary", "")).strip()
            url = str(row.get("url", "")).strip()
            if not title or len(title) < 10:
                continue
            # 从URL提取日期并过滤
            pub_date = _extract_date_from_url(url)
            if pub_date and pub_date < cutoff:
                continue  # 跳过两周前的新闻
            items.append({
                "title": title,
                "source": "财联社",
                "trust": SOURCE_TRUST["财联社"],
                "pub_date": pub_date,
            })
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
        return [{"title": t.strip(), "source": "新浪财经", "trust": SOURCE_TRUST["新浪财经"]} for t in titles[:25]]
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
            return [{"title": item.get("title", ""), "source": "财联社", "trust": SOURCE_TRUST["财联社"]} for item in items[:25] if item.get("title")]
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
        return [{"title": item.get("art_title", ""), "source": "东方财富", "trust": SOURCE_TRUST["东方财富"]} for item in items[:25] if item.get("art_title")]
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
        return [{"title": item.get("title", ""), "source": "腾讯财经", "trust": SOURCE_TRUST["腾讯财经"]} for item in items[:25] if item.get("title")]
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
        return [{"title": item.get("post", {}).get("title", ""), "source": "36氪", "trust": SOURCE_TRUST["36氪"]} for item in items[:15] if item.get("post", {}).get("title")]
    except Exception as e:
        print(f"[Crawler] 36kr failed: {e}")
        return []


def _fetch_sina_api() -> list[dict]:
    """新浪财经API（国内+国际新闻）."""
    items = []
    # 国内财经
    urls = [
        ("https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=30", "新浪财经"),
        ("https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2515&num=30", "新浪财经"),
    ]
    for url, source in urls:
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://finance.sina.com.cn/",
            })
            resp.raise_for_status()
            data = resp.json()
            news_list = data.get("result", {}).get("data", [])
            for item in news_list:
                title = item.get("title", "").strip()
                if title and len(title) >= 10:
                    items.append({"title": title, "source": source, "trust": SOURCE_TRUST.get(source, 0.7)})
        except Exception as e:
            print(f"[Crawler] Sina API failed ({url}): {e}")
    return items[:40]


def _fetch_walls_street_cn() -> list[dict]:
    """华尔街见闻（全球财经）."""
    url = "https://api-one.wallstcn.com/apiv1/content/information-flow?limit=30&channel=global"
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://wallstreetcn.com/",
        })
        resp.raise_for_status()
        data = resp.json()
        items = []
        for item in data.get("data", {}).get("items", []):
            content = item.get("resource", {})
            title = content.get("title", "").strip()
            if title and len(title) >= 10:
                items.append({"title": title, "source": "华尔街见闻", "trust": 0.75})
        return items[:30]
    except Exception as e:
        print(f"[Crawler] Wallstreetcn failed: {e}")
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

    recommended = [s for s, sc in heatmap.items() if sc >= 55]  # 门槛55
    avoid = [s for s, sc in heatmap.items() if sc <= 40]  # 回避门槛40
    avg_score = sum(heatmap.values()) / len(heatmap) if heatmap else 50

    return {
        "heatmap": {k: round(v, 1) for k, v in heatmap.items()},
        "recommended": recommended,
        "avoid": avoid,
        "score": round(avg_score, 1),
    }


def _analyze_social_themes(news: list[dict]) -> dict[str, Any]:
    """分析社会实事趋势（加权）."""
    theme_strength = {}
    for theme, kws in SOCIAL_THEMES.items():
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

    major_themes = [t for t, s in theme_strength.items() if s > 5]

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

    # 1. 多源并行抓取（优先级：akshare财联社 > 新浪API > 华尔街见闻 > 直接爬虫）
    sources = [
        _fetch_cls_via_akshare(),   # 最可靠，优先使用
        _fetch_sina_api(),           # 新浪财经API（国内+国际）
        _fetch_walls_street_cn(),    # 华尔街见闻
        _fetch_36kr_tech(),          # 科技趋势
        _fetch_cls_24h(),            # 备选（可能失效）
        _fetch_sina_finance(),       # 备选（可能失效）
        _fetch_eastmoney_kuaixun(),  # 备选
        _fetch_tencent_finance(),    # 备选（可能失效）
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
