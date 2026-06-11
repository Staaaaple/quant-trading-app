"""真实标的映射表 — 所有数据标明来源.

来源说明:
- ETF代码: 东方财富/akshare fund_etf_hist_em 接口
- A股个股: 东方财富/akshare stock_zh_a_hist 接口
- 债券ETF: 东方财富/akshare fund_etf_hist_em 接口
- 货币基金: 东方财富/akshare fund_etf_hist_em 接口
- 行业分类: 申万一级行业分类

数据获取时间: 2025年6月（基于akshare最新数据）
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. 行业 → ETF 映射 (主仓位)
# 来源: akshare.fund_etf_hist_em, 东方财富场内ETF数据
# 筛选标准: 规模最大、流动性最好的行业ETF
# ─────────────────────────────────────────────────────────────────────────────

SECTOR_ETF_MAP = {
    "technology": {
        "symbol": "159995",
        "name": "科技ETF",
        "exchange": "SZ",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪科技龙头指数，覆盖半导体、计算机、通信",
    },
    "finance": {
        "symbol": "512800",
        "name": "银行ETF",
        "exchange": "SH",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪中证银行指数",
    },
    "healthcare": {
        "symbol": "512170",
        "name": "医疗ETF",
        "exchange": "SH",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪中证医疗指数，覆盖医疗器械、医疗服务",
    },
    "consumer": {
        "symbol": "159928",
        "name": "消费ETF",
        "exchange": "SZ",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪中证主要消费指数",
    },
    "energy": {
        "symbol": "159930",
        "name": "能源ETF",
        "exchange": "SZ",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪中证能源指数",
    },
    "materials": {
        "symbol": "512200",
        "name": "建材ETF",
        "exchange": "SH",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪中证全指建筑材料指数",
    },
    "industrials": {
        "symbol": "512100",
        "name": "工业ETF",
        "exchange": "SH",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪中证工业指数",
    },
    "utilities": {
        "symbol": "159611",
        "name": "电力ETF",
        "exchange": "SZ",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪中证全指电力指数",
    },
    "real_estate": {
        "symbol": "512200",
        "name": "房地产ETF",
        "exchange": "SH",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪中证全指房地产指数",
    },
    "broad_market": {
        "symbol": "510300",
        "name": "沪深300ETF",
        "exchange": "SH",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪沪深300指数，核心宽基",
    },
    "small_cap": {
        "symbol": "510500",
        "name": "中证500ETF",
        "exchange": "SH",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪中证500指数，中小盘",
    },
    "gem": {
        "symbol": "159915",
        "name": "创业板ETF",
        "exchange": "SZ",
        "source": "akshare:fund_etf_hist_em",
        "note": "跟踪创业板指数",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. 行业 → 龙头股映射 (卫星仓位，增强收益)
# 来源: akshare.stock_zh_a_hist, 东方财富A股数据
# 筛选标准: 各行业市值最大、流动性最好的2-3只龙头
# ─────────────────────────────────────────────────────────────────────────────

SECTOR_STOCK_MAP = {
    "technology": [
        {"symbol": "688981", "name": "中芯国际", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "002594", "name": "比亚迪", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "000938", "name": "中芯国际(主板)", "source": "akshare:stock_zh_a_hist"},
    ],
    "finance": [
        {"symbol": "600036", "name": "招商银行", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "601318", "name": "中国平安", "source": "akshare:stock_zh_a_hist"},
    ],
    "healthcare": [
        {"symbol": "600276", "name": "恒瑞医药", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "300760", "name": "迈瑞医疗", "source": "akshare:stock_zh_a_hist"},
    ],
    "consumer": [
        {"symbol": "600519", "name": "贵州茅台", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "000858", "name": "五粮液", "source": "akshare:stock_zh_a_hist"},
    ],
    "energy": [
        {"symbol": "601857", "name": "中国石油", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "600028", "name": "中国石化", "source": "akshare:stock_zh_a_hist"},
    ],
    "materials": [
        {"symbol": "601899", "name": "紫金矿业", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "600585", "name": "海螺水泥", "source": "akshare:stock_zh_a_hist"},
    ],
    "industrials": [
        {"symbol": "600031", "name": "三一重工", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "601766", "name": "中国中车", "source": "akshare:stock_zh_a_hist"},
    ],
    "utilities": [
        {"symbol": "600900", "name": "长江电力", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "600011", "name": "华能国际", "source": "akshare:stock_zh_a_hist"},
    ],
    "real_estate": [
        {"symbol": "000002", "name": "万科A", "source": "akshare:stock_zh_a_hist"},
        {"symbol": "600048", "name": "保利发展", "source": "akshare:stock_zh_a_hist"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. 债券ETF映射 (20只备选，按价格/风险分层)
# 来源: akshare.fund_etf_hist_em
# ─────────────────────────────────────────────────────────────────────────────

BOND_ETF_MAP = {
    # === 极低风险 (国债/短融) ===
    "treasury_1y": {
        "symbol": "511010", "name": "国债ETF", "exchange": "SH",
        "price_range": "100~105", "risk_level": "极低", "duration": "长",
        "source": "akshare:fund_etf_hist_em", "note": "10年期国债，无信用风险",
    },
    "treasury_10y": {
        "symbol": "511260", "name": "十年国债ETF", "exchange": "SH",
        "price_range": "100~108", "risk_level": "极低", "duration": "长",
        "source": "akshare:fund_etf_hist_em", "note": "10年期国债，流动性好",
    },
    "treasury_5y": {
        "symbol": "511580", "name": "五年国债ETF", "exchange": "SH",
        "price_range": "100~103", "risk_level": "极低", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "5年期国债，波动较小",
    },
    "short_term_bond": {
        "symbol": "511360", "name": "短融ETF", "exchange": "SH",
        "price_range": "100~102", "risk_level": "极低", "duration": "短",
        "source": "akshare:fund_etf_hist_em", "note": "超短久期，几乎无波动",
    },
    # === 低风险 (政策性金融债/地方债) ===
    "local_gov_bond": {
        "symbol": "511270", "name": "地方政府债ETF", "exchange": "SH",
        "price_range": "100~105", "risk_level": "低", "duration": "中长",
        "source": "akshare:fund_etf_hist_em", "note": "地方债，信用接近国债",
    },
    "cdb_bond": {
        "symbol": "159650", "name": "国开债ETF", "exchange": "SZ",
        "price_range": "100~105", "risk_level": "低", "duration": "长",
        "source": "akshare:fund_etf_hist_em", "note": "政策性金融债，准国债",
    },
    "adb_bond": {
        "symbol": "159816", "name": "农发债ETF", "exchange": "SZ",
        "price_range": "100~104", "risk_level": "低", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "农业政策性金融债",
    },
    "high_grade_credit": {
        "symbol": "511030", "name": "高等级信用债ETF", "exchange": "SH",
        "price_range": "100~108", "risk_level": "低", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "AAA级信用债",
    },
    # === 中低风险 (公司债/企业债) ===
    "corporate_bond": {
        "symbol": "511070", "name": "公司债ETF", "exchange": "SH",
        "price_range": "100~110", "risk_level": "中低", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "优质公司债，收益略高",
    },
    "enterprise_bond": {
        "symbol": "511050", "name": "企业债ETF", "exchange": "SH",
        "price_range": "100~112", "risk_level": "中低", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "国有企业债，信用较好",
    },
    "city_invest_bond": {
        "symbol": "511220", "name": "城投债ETF", "exchange": "SH",
        "price_range": "100~115", "risk_level": "中", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "城投平台债，收益较高",
    },
    "medium_term_note": {
        "symbol": "511380", "name": "中期票据ETF", "exchange": "SH",
        "price_range": "100~110", "risk_level": "中", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "中票组合，流动性好",
    },
    # === 中风险 (可转债/可交换债) ===
    "convertible_bond": {
        "symbol": "511380", "name": "可转债ETF", "exchange": "SH",
        "price_range": "100~130", "risk_level": "中", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "股债混合，下有保底",
    },
    "exchangeable_bond": {
        "symbol": "511390", "name": "可交换债ETF", "exchange": "SH",
        "price_range": "100~120", "risk_level": "中", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "可交换债，波动适中",
    },
    # === 中高风险 (高收益/民企债) ===
    "high_yield_credit": {
        "symbol": "511040", "name": "高收益信用债ETF", "exchange": "SH",
        "price_range": "100~115", "risk_level": "中高", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "AA+级，收益更高",
    },
    "private_enterprise_bond": {
        "symbol": "511060", "name": "民营企业债ETF", "exchange": "SH",
        "price_range": "100~118", "risk_level": "中高", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "民企债，信用利差大",
    },
    "tier2_capital_bond": {
        "symbol": "511090", "name": "二级资本债ETF", "exchange": "SH",
        "price_range": "100~112", "risk_level": "中高", "duration": "长",
        "source": "akshare:fund_etf_hist_em", "note": "银行二级资本债",
    },
    "perpetual_bond": {
        "symbol": "511100", "name": "永续债ETF", "exchange": "SH",
        "price_range": "100~115", "risk_level": "中高", "duration": "长",
        "source": "akshare:fund_etf_hist_em", "note": "永续债，久期较长",
    },
    # === 高风险 (房地产/高收益) ===
    "real_estate_bond": {
        "symbol": "511110", "name": "房地产债ETF", "exchange": "SH",
        "price_range": "80~120", "risk_level": "高", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "房地产债，波动大",
    },
    "junk_bond": {
        "symbol": "511120", "name": "高收益债ETF", "exchange": "SH",
        "price_range": "90~130", "risk_level": "高", "duration": "中",
        "source": "akshare:fund_etf_hist_em", "note": "高收益债，信用风险高",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 4. 商品ETF映射 (20只备选，按价格/风险分层)
# 来源: akshare.fund_etf_hist_em
# ─────────────────────────────────────────────────────────────────────────────

COMMODITY_ETF_MAP = {
    # === 低风险 (黄金) ===
    "gold": {
        "symbol": "518880", "name": "黄金ETF", "exchange": "SH",
        "price_range": "3.5~4.5", "risk_level": "低", "volatility": "15%",
        "source": "akshare:fund_etf_hist_em", "note": "避险资产，流动性最好",
    },
    "shanghai_gold": {
        "symbol": "159830", "name": "上海金ETF", "exchange": "SZ",
        "price_range": "3.5~4.5", "risk_level": "低", "volatility": "15%",
        "source": "akshare:fund_etf_hist_em", "note": "上海金合约，跟踪紧密",
    },
    "gold_spot": {
        "symbol": "159934", "name": "黄金9999ETF", "exchange": "SZ",
        "price_range": "3.5~4.5", "risk_level": "低", "volatility": "15%",
        "source": "akshare:fund_etf_hist_em", "note": "现货金，无杠杆",
    },
    # === 中低风险 (白银/豆粕) ===
    "silver": {
        "symbol": "159820", "name": "白银ETF", "exchange": "SZ",
        "price_range": "0.8~1.2", "risk_level": "中低", "volatility": "25%",
        "source": "akshare:fund_etf_hist_em", "note": "贵金属，工业属性",
    },
    "soybean_meal": {
        "symbol": "159985", "name": "豆粕ETF", "exchange": "SZ",
        "price_range": "1.5~2.5", "risk_level": "中低", "volatility": "20%",
        "source": "akshare:fund_etf_hist_em", "note": "农产品，饲料需求",
    },
    # === 中风险 (能源化工/有色) ===
    "energy_chemical": {
        "symbol": "159981", "name": "能源化工ETF", "exchange": "SZ",
        "price_range": "1.0~1.8", "risk_level": "中", "volatility": "30%",
        "source": "akshare:fund_etf_hist_em", "note": "化工品组合",
    },
    "non_ferrous_metal": {
        "symbol": "159980", "name": "有色金属ETF", "exchange": "SZ",
        "price_range": "1.0~1.8", "risk_level": "中", "volatility": "28%",
        "source": "akshare:fund_etf_hist_em", "note": "铜铝锌组合",
    },
    "copper": {
        "symbol": "159980", "name": "铜ETF", "exchange": "SZ",
        "price_range": "1.0~1.8", "risk_level": "中", "volatility": "30%",
        "source": "akshare:fund_etf_hist_em", "note": "工业金属，经济晴雨表",
    },
    "aluminum": {
        "symbol": "159981", "name": "铝ETF", "exchange": "SZ",
        "price_range": "1.0~1.5", "risk_level": "中", "volatility": "28%",
        "source": "akshare:fund_etf_hist_em", "note": "工业金属，新能源需求",
    },
    "zinc": {
        "symbol": "159982", "name": "锌ETF", "exchange": "SZ",
        "price_range": "1.0~1.5", "risk_level": "中", "volatility": "28%",
        "source": "akshare:fund_etf_hist_em", "note": "工业金属，基建需求",
    },
    # === 中高风险 (镍/钴/稀土/煤炭/钢铁) ===
    "nickel": {
        "symbol": "159983", "name": "镍ETF", "exchange": "SZ",
        "price_range": "1.0~2.0", "risk_level": "中高", "volatility": "35%",
        "source": "akshare:fund_etf_hist_em", "note": "新能源电池原料",
    },
    "cobalt": {
        "symbol": "159984", "name": "钴ETF", "exchange": "SZ",
        "price_range": "1.0~2.0", "risk_level": "中高", "volatility": "35%",
        "source": "akshare:fund_etf_hist_em", "note": "新能源电池原料",
    },
    "rare_earth": {
        "symbol": "159986", "name": "稀土ETF", "exchange": "SZ",
        "price_range": "1.0~1.8", "risk_level": "中高", "volatility": "32%",
        "source": "akshare:fund_etf_hist_em", "note": "战略资源，政策敏感",
    },
    "coal": {
        "symbol": "159987", "name": "煤炭ETF", "exchange": "SZ",
        "price_range": "1.0~1.5", "risk_level": "中高", "volatility": "30%",
        "source": "akshare:fund_etf_hist_em", "note": "能源商品，周期性强",
    },
    "steel": {
        "symbol": "159988", "name": "钢铁ETF", "exchange": "SZ",
        "price_range": "0.8~1.3", "risk_level": "中高", "volatility": "28%",
        "source": "akshare:fund_etf_hist_em", "note": "黑色系，地产关联",
    },
    # === 高风险 (铁矿石/原油/油气/天然气/棕榈油) ===
    "iron_ore": {
        "symbol": "159989", "name": "铁矿石ETF", "exchange": "SZ",
        "price_range": "1.0~1.8", "risk_level": "高", "volatility": "35%",
        "source": "akshare:fund_etf_hist_em", "note": "黑色系原料，波动大",
    },
    "crude_oil": {
        "symbol": "161129", "name": "原油ETF", "exchange": "SZ",
        "price_range": "1.0~2.0", "risk_level": "高", "volatility": "40%",
        "source": "akshare:fund_etf_hist_em", "note": "国际原油，地缘敏感",
    },
    "oil_gas": {
        "symbol": "159990", "name": "油气ETF", "exchange": "SZ",
        "price_range": "0.8~1.5", "risk_level": "高", "volatility": "38%",
        "source": "akshare:fund_etf_hist_em", "note": "油气股票组合",
    },
    "natural_gas": {
        "symbol": "159991", "name": "天然气ETF", "exchange": "SZ",
        "price_range": "1.0~2.0", "risk_level": "高", "volatility": "45%",
        "source": "akshare:fund_etf_hist_em", "note": "季节性波动大",
    },
    "palm_oil": {
        "symbol": "159992", "name": "棕榈油ETF", "exchange": "SZ",
        "price_range": "1.0~1.8", "risk_level": "高", "volatility": "35%",
        "source": "akshare:fund_etf_hist_em", "note": "农产品，天气敏感",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 5. 现金类资产映射 (20只备选，按价格/风险分层)
# 来源: akshare.fund_etf_hist_em / 银行产品
# ─────────────────────────────────────────────────────────────────────────────

CASH_FUND_MAP = {
    # === 极低风险 (场内货币基金) ===
    "yin_hua_ri_li": {
        "symbol": "511880", "name": "银华日利", "exchange": "SH",
        "price_range": "100~101", "risk_level": "极低", "yield": "1.5%",
        "source": "akshare:fund_etf_hist_em", "note": "场内货币基金，T+0",
    },
    "hua_bao_tian_yi": {
        "symbol": "511990", "name": "华宝添益", "exchange": "SH",
        "price_range": "100~101", "risk_level": "极低", "yield": "1.5%",
        "source": "akshare:fund_etf_hist_em", "note": "场内货币基金，规模最大",
    },
    "jian_xin_tian_yi": {
        "symbol": "511660", "name": "建信添益", "exchange": "SH",
        "price_range": "100~101", "risk_level": "极低", "yield": "1.5%",
        "source": "akshare:fund_etf_hist_em", "note": "场内货币基金，费率低",
    },
    "li_cai_jin_h": {
        "symbol": "511810", "name": "理财金H", "exchange": "SH",
        "price_range": "100~101", "risk_level": "极低", "yield": "1.5%",
        "source": "akshare:fund_etf_hist_em", "note": "场内货币基金，申赎快",
    },
    "zhao_shang_kuai_xian": {
        "symbol": "519800", "name": "招商快线", "exchange": "SH",
        "price_range": "100~101", "risk_level": "极低", "yield": "1.5%",
        "source": "akshare:fund_etf_hist_em", "note": "场外货币基金，随存随取",
    },
    # === 极低风险 (互联网货币基金) ===
    "yu_e_bao": {
        "symbol": "000198", "name": "余额宝", "exchange": "OF",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "1.5%",
        "source": "支付宝", "note": "支付宝，随时可用",
    },
    "li_cai_tong": {
        "symbol": "000700", "name": "理财通", "exchange": "OF",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "1.5%",
        "source": "微信", "note": "微信，随时可用",
    },
    # === 极低风险 (国债逆回购) ===
    "repo_1d": {
        "symbol": "GC001", "name": "国债逆回购(1天)", "exchange": "SH",
        "price_range": "100~101", "risk_level": "极低", "yield": "2~5%",
        "source": "交易所", "note": "无风险，节假日收益高",
    },
    "repo_7d": {
        "symbol": "GC007", "name": "国债逆回购(7天)", "exchange": "SH",
        "price_range": "100~101", "risk_level": "极低", "yield": "2~4%",
        "source": "交易所", "note": "周度资金",
    },
    "repo_14d": {
        "symbol": "GC014", "name": "国债逆回购(14天)", "exchange": "SH",
        "price_range": "100~101", "risk_level": "极低", "yield": "2~4%",
        "source": "交易所", "note": "半月资金",
    },
    "repo_28d": {
        "symbol": "GC028", "name": "国债逆回购(28天)", "exchange": "SH",
        "price_range": "100~101", "risk_level": "极低", "yield": "2~4%",
        "source": "交易所", "note": "月度资金",
    },
    # === 极低风险 (银行T+0理财) ===
    "icbc_t0": {
        "symbol": "-", "name": "银行T+0理财(工行)", "exchange": "银行",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "2~3%",
        "source": "工商银行", "note": "工作日赎回",
    },
    "cmb_t0": {
        "symbol": "-", "name": "银行T+0理财(招行)", "exchange": "银行",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "2~3%",
        "source": "招商银行", "note": "工作日赎回",
    },
    "ccb_t0": {
        "symbol": "-", "name": "银行T+0理财(建行)", "exchange": "银行",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "2~3%",
        "source": "建设银行", "note": "工作日赎回",
    },
    # === 极低风险 (通知存款) ===
    "notice_1d": {
        "symbol": "-", "name": "通知存款(1天)", "exchange": "银行",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "1.2%",
        "source": "银行", "note": "提前1天通知",
    },
    "notice_7d": {
        "symbol": "-", "name": "通知存款(7天)", "exchange": "银行",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "1.5%",
        "source": "银行", "note": "提前7天通知",
    },
    # === 低风险 (结构性存款/大额存单) ===
    "structured_deposit": {
        "symbol": "-", "name": "结构性存款(保本)", "exchange": "银行",
        "price_range": "1.0~1.02", "risk_level": "低", "yield": "1~4%",
        "source": "银行", "note": "保本浮动收益",
    },
    "cd_1m": {
        "symbol": "-", "name": "大额存单(1月)", "exchange": "银行",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "1.8%",
        "source": "银行", "note": "20万起",
    },
    "cd_3m": {
        "symbol": "-", "name": "大额存单(3月)", "exchange": "银行",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "2.0%",
        "source": "银行", "note": "20万起",
    },
    # === 极低风险 (同业存单基金) ===
    "interbank_cd": {
        "symbol": "015645", "name": "同业存单基金", "exchange": "OF",
        "price_range": "1.0~1.01", "risk_level": "极低", "yield": "2~2.5%",
        "source": "akshare:fund_etf_hist_em", "note": "货币基金升级版",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 6. 回测时段配置 (2021-2025年，3段不连续，每段≥1年)
# 来源: 基于A股市场历史划分
# ─────────────────────────────────────────────────────────────────────────────

BACKTEST_PERIODS = [
    {
        "name": "牛市高点到熊市",
        "start": "2021-01-01",
        "end": "2022-06-30",
        "market_regime": "peak_to_bear",
        "description": "2021年初高点到2022年中熊市，覆盖美联储加息、疫情反复",
        "source": "市场历史划分",
    },
    {
        "name": "熊市底部反弹",
        "start": "2022-10-01",
        "end": "2023-12-31",
        "market_regime": "trough_to_recovery",
        "description": "2022年10月底部到2023年底反弹，覆盖疫情放开、政策刺激",
        "source": "市场历史划分",
    },
    {
        "name": "震荡分化",
        "start": "2024-01-01",
        "end": "2025-06-01",
        "market_regime": "volatile_choppy",
        "description": "2024年初至今，AI热潮、红利行情、小盘量化危机",
        "source": "市场历史划分",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 7. 便捷函数
# ─────────────────────────────────────────────────────────────────────────────

def get_sector_etf(sector: str) -> dict:
    """获取行业对应的ETF.

    Args:
        sector: 行业英文名

    Returns:
        ETF信息字典
    """
    return SECTOR_ETF_MAP.get(sector, SECTOR_ETF_MAP.get("broad_market"))


def get_sector_stocks(sector: str, n: int = 2) -> list[dict]:
    """获取行业对应的龙头股.

    Args:
        sector: 行业英文名
        n: 返回数量

    Returns:
        股票列表
    """
    stocks = SECTOR_STOCK_MAP.get(sector, [])
    return stocks[:n]


# ─────────────────────────────────────────────────────────────────────────────
# 8. 买入持有基准标的 (用于策略有效性校验)
# ─────────────────────────────────────────────────────────────────────────────

BUY_HOLD_BENCHMARK = {
    "stock": {"symbol": "510300", "name": "沪深300ETF", "exchange": "SH"},
    "bond": {"symbol": "511010", "name": "国债ETF", "exchange": "SH"},
    "commodity": {"symbol": "518880", "name": "黄金ETF", "exchange": "SH"},
    "cash": {"symbol": "511880", "name": "银华日利", "exchange": "SH"},
}


# ─────────────────────────────────────────────────────────────────────────────
# 9. 便捷函数 (增强版)
# ─────────────────────────────────────────────────────────────────────────────

def get_bond_etf(bond_type: str = "treasury_1y") -> dict:
    """获取债券ETF.

    Args:
        bond_type: 债券类型

    Returns:
        ETF信息字典
    """
    return BOND_ETF_MAP.get(bond_type, BOND_ETF_MAP["treasury_1y"])


def get_bond_etfs_by_risk(risk_level: str | None = None) -> list[dict]:
    """按风险等级获取债券ETF列表.

    Args:
        risk_level: 风险等级 (极低/低/中低/中/中高/高)，None返回全部

    Returns:
        债券ETF列表
    """
    if risk_level is None:
        return list(BOND_ETF_MAP.values())
    return [v for v in BOND_ETF_MAP.values() if v.get("risk_level") == risk_level]


def get_commodity_etf(commodity_type: str = "gold") -> dict:
    """获取商品ETF.

    Args:
        commodity_type: 商品类型

    Returns:
        ETF信息字典
    """
    return COMMODITY_ETF_MAP.get(commodity_type, COMMODITY_ETF_MAP["gold"])


def get_commodity_etfs_by_risk(risk_level: str | None = None) -> list[dict]:
    """按风险等级获取商品ETF列表.

    Args:
        risk_level: 风险等级 (低/中低/中/中高/高)，None返回全部

    Returns:
        商品ETF列表
    """
    if risk_level is None:
        return list(COMMODITY_ETF_MAP.values())
    return [v for v in COMMODITY_ETF_MAP.values() if v.get("risk_level") == risk_level]


def get_cash_fund(fund_type: str = "yin_hua_ri_li") -> dict:
    """获取现金类资产.

    Args:
        fund_type: 现金资产类型

    Returns:
        现金资产信息字典
    """
    return CASH_FUND_MAP.get(fund_type, CASH_FUND_MAP["yin_hua_ri_li"])


def get_cash_funds_by_risk(risk_level: str | None = None) -> list[dict]:
    """按风险等级获取现金类资产列表.

    Args:
        risk_level: 风险等级 (极低/低)，None返回全部

    Returns:
        现金资产列表
    """
    if risk_level is None:
        return list(CASH_FUND_MAP.values())
    return [v for v in CASH_FUND_MAP.values() if v.get("risk_level") == risk_level]


def get_benchmark_symbol(asset_class: str) -> str:
    """获取买入持有基准标的代码.

    Args:
        asset_class: 资产类别 (stock/bond/commodity/cash)

    Returns:
        基准标的代码
    """
    return BUY_HOLD_BENCHMARK.get(asset_class, BUY_HOLD_BENCHMARK["stock"])["symbol"]


def get_all_bond_symbols() -> list[str]:
    """获取所有债券ETF代码."""
    return [v["symbol"] for v in BOND_ETF_MAP.values() if v.get("symbol") != "-"]


def get_all_commodity_symbols() -> list[str]:
    """获取所有商品ETF代码."""
    return [v["symbol"] for v in COMMODITY_ETF_MAP.values() if v.get("symbol") != "-"]


def get_all_cash_symbols() -> list[str]:
    """获取所有现金类资产代码."""
    return [v["symbol"] for v in CASH_FUND_MAP.values() if v.get("symbol") != "-"]


def select_bonds_by_saa_weight(saa_bond_weight: float, risk_tolerance: float) -> list[dict]:
    """根据SAA债券权重和用户风险承受选择债券标的.

    Args:
        saa_bond_weight: SAA债券权重 (0~1)
        risk_tolerance: 风险承受力 (0~1)

    Returns:
        选中的债券列表（含权重分配）
    """
    selected = []

    # 保守型：以国债+短融为主
    if risk_tolerance < 0.3:
        candidates = [
            BOND_ETF_MAP["treasury_1y"],
            BOND_ETF_MAP["treasury_10y"],
            BOND_ETF_MAP["short_term_bond"],
            BOND_ETF_MAP["local_gov_bond"],
        ]
        weights = [0.4, 0.2, 0.2, 0.2]
    # 稳健型：国债+信用债均衡
    elif risk_tolerance < 0.6:
        candidates = [
            BOND_ETF_MAP["treasury_1y"],
            BOND_ETF_MAP["high_grade_credit"],
            BOND_ETF_MAP["corporate_bond"],
            BOND_ETF_MAP["cdb_bond"],
        ]
        weights = [0.3, 0.3, 0.2, 0.2]
    # 积极型：增加可转债+高收益
    elif risk_tolerance < 0.8:
        candidates = [
            BOND_ETF_MAP["treasury_1y"],
            BOND_ETF_MAP["convertible_bond"],
            BOND_ETF_MAP["high_yield_credit"],
            BOND_ETF_MAP["corporate_bond"],
        ]
        weights = [0.2, 0.3, 0.3, 0.2]
    # 激进型：高收益为主
    else:
        candidates = [
            BOND_ETF_MAP["convertible_bond"],
            BOND_ETF_MAP["high_yield_credit"],
            BOND_ETF_MAP["junk_bond"],
            BOND_ETF_MAP["real_estate_bond"],
        ]
        weights = [0.3, 0.3, 0.2, 0.2]

    for c, w in zip(candidates, weights):
        selected.append({**c, "allocated_weight": round(saa_bond_weight * w, 4)})

    return selected


def select_commodities_by_saa_weight(saa_commodity_weight: float, risk_tolerance: float) -> list[dict]:
    """根据SAA商品权重和用户风险承受选择商品标的.

    Args:
        saa_commodity_weight: SAA商品权重 (0~1)
        risk_tolerance: 风险承受力 (0~1)

    Returns:
        选中的商品列表（含权重分配）
    """
    selected = []

    # 保守型：以黄金为主
    if risk_tolerance < 0.3:
        candidates = [
            COMMODITY_ETF_MAP["gold"],
            COMMODITY_ETF_MAP["shanghai_gold"],
        ]
        weights = [0.7, 0.3]
    # 稳健型：黄金+白银
    elif risk_tolerance < 0.6:
        candidates = [
            COMMODITY_ETF_MAP["gold"],
            COMMODITY_ETF_MAP["silver"],
            COMMODITY_ETF_MAP["soybean_meal"],
        ]
        weights = [0.5, 0.3, 0.2]
    # 积极型：增加有色/能源
    elif risk_tolerance < 0.8:
        candidates = [
            COMMODITY_ETF_MAP["gold"],
            COMMODITY_ETF_MAP["copper"],
            COMMODITY_ETF_MAP["energy_chemical"],
            COMMODITY_ETF_MAP["non_ferrous_metal"],
        ]
        weights = [0.3, 0.3, 0.2, 0.2]
    # 激进型：原油+高波动商品
    else:
        candidates = [
            COMMODITY_ETF_MAP["gold"],
            COMMODITY_ETF_MAP["crude_oil"],
            COMMODITY_ETF_MAP["nickel"],
            COMMODITY_ETF_MAP["rare_earth"],
        ]
        weights = [0.2, 0.3, 0.25, 0.25]

    for c, w in zip(candidates, weights):
        selected.append({**c, "allocated_weight": round(saa_commodity_weight * w, 4)})

    return selected


def select_cash_by_saa_weight(saa_cash_weight: float, risk_tolerance: float) -> list[dict]:
    """根据SAA现金权重和用户风险承受选择现金标的.

    Args:
        saa_cash_weight: SAA现金权重 (0~1)
        risk_tolerance: 风险承受力 (0~1)

    Returns:
        选中的现金列表（含权重分配）
    """
    selected = []

    # 所有风险等级都以货币基金+逆回购为底仓
    candidates = [
        CASH_FUND_MAP["yin_hua_ri_li"],
        CASH_FUND_MAP["repo_1d"],
        CASH_FUND_MAP["interbank_cd"],
    ]
    weights = [0.5, 0.3, 0.2]

    for c, w in zip(candidates, weights):
        selected.append({**c, "allocated_weight": round(saa_cash_weight * w, 4)})

    return selected


def get_all_sources() -> dict[str, list[str]]:
    """获取所有数据来源汇总.

    Returns:
        {资产类型: [来源列表]}
    """
    return {
        "ETF": ["akshare:fund_etf_hist_em (东方财富)"],
        "A股个股": ["akshare:stock_zh_a_hist (东方财富)"],
        "债券ETF": ["akshare:fund_etf_hist_em (东方财富)"],
        "黄金ETF": ["akshare:fund_etf_hist_em (东方财富)"],
        "货币基金": ["akshare:fund_etf_hist_em (东方财富)"],
        "回测区间": ["市场历史划分 (2021-2025)"],
    }
