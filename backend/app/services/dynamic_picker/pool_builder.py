"""标的池构建器 (Pool Builder).

根据信号仪表盘的Top行业、市场周期等信息，
实时爬取板块成分股、筛选相关ETF、补充热门股，
构建候选标的池。

数据源:
- 板块成分股: akshare.stock_board_industry_cons_em / stock_board_concept_cons_em
- ETF列表: akshare.fund_etf_category_sina / fund_etf_hist_em
- 热门股: akshare.stock_lhb_detail_daily_sina / stock_zt_pool_em
"""

import asyncio
import logging
from typing import Optional

import akshare as ak
import pandas as pd

from .models import StockCandidate

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 行业 → 东方财富板块名称 映射
# ─────────────────────────────────────────────────────────────────────────────

SECTOR_TO_BOARD_MAP = {
    "technology": ["半导体", "软件服务", "通信设备", "电子元件", "人工智能"],
    "finance": ["银行", "证券", "保险", "多元金融"],
    "healthcare": ["医疗器械", "生物制品", "化学制药", "中药", "医疗服务"],
    "consumer": ["白酒", "食品饮料", "家电行业", "旅游酒店", "商贸百货"],
    "energy": ["电力行业", "煤炭行业", "石油行业", "燃气", "新能源"],
    "materials": ["有色金属", "钢铁行业", "化工行业", "建材", "新材料"],
    "industrials": ["汽车零部件", "工程机械", "航天航空", "船舶制造", "专用设备"],
    "utilities": ["电力行业", "燃气", "水务", "环保行业"],
    "real_estate": ["房地产开发", "房地产服务", "装修建材", "水泥建材"],
}

# 行业 → ETF关键词 映射
SECTOR_TO_ETF_KEYWORDS = {
    "technology": ["科技", "半导体", "芯片", "5G", "AI", "人工智能", "通信", "计算机"],
    "finance": ["银行", "金融", "证券", "保险", "地产", "港股通金融"],
    "healthcare": ["医疗", "医药", "生物科技", "健康", "创新药", "医疗器械"],
    "consumer": ["消费", "白酒", "食品", "家电", "旅游", "传媒", "娱乐"],
    "energy": ["能源", "电力", "煤炭", "石油", "新能源", "光伏", "风电"],
    "materials": ["材料", "有色", "钢铁", "化工", "建材", "稀土", "锂"],
    "industrials": ["工业", "制造", "机械", "汽车", "军工", "航空", "船舶"],
    "utilities": ["电力", "公用", "水务", "环保", "燃气", "基础设施"],
    "real_estate": ["房地产", "地产", "建材", "家居", "物业"],
}


class PoolBuilder:
    """标的池构建器.

    根据Top行业实时构建候选标的池，包含:
    1. 板块成分股（按行业爬取）
    2. 行业相关ETF（按规模和流动性筛选）
    3. 热门股补充（龙虎榜等）
    """

    def __init__(self, pool_size: int = 200):
        self.pool_size = pool_size

    async def build_pool(
        self,
        top_sectors: list[dict],
        market_cycle: Optional[str] = None,
    ) -> list[StockCandidate]:
        """构建候选标的池.

        Args:
            top_sectors: TAA输出的Top行业列表，如 [{"sector": "technology", "weight": 0.25}]
            market_cycle: 市场周期，用于调整筛选标准

        Returns:
            list[StockCandidate]: 候选标的列表（按流动性排序，截取前pool_size）
        """
        logger.info(f"开始构建标的池，Top行业: {[s['sector'] for s in top_sectors]}")

        # 并行获取股票标的（不再获取ETF）
        tasks = [
            self._fetch_sector_stocks(top_sectors),
            self._fetch_hot_stocks(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        candidates = []

        # 处理板块成分股
        if isinstance(results[0], list):
            candidates.extend(results[0])
            logger.info(f"板块成分股: {len(results[0])}只")
        else:
            logger.warning(f"板块成分股获取失败: {results[0]}")

        # 处理热门股（去重）
        if isinstance(results[1], list):
            existing_symbols = {c.symbol for c in candidates}
            for hot in results[1]:
                if hot.symbol not in existing_symbols:
                    candidates.append(hot)
            logger.info(f"热门股补充: {len([h for h in results[1] if h.symbol not in existing_symbols])}只")
        else:
            logger.warning(f"热门股获取失败: {results[1]}")

        # 按流动性排序，截取前pool_size
        candidates.sort(key=lambda c: c.daily_volume or 0, reverse=True)
        final_pool = candidates[: self.pool_size]

        logger.info(f"标的池构建完成: {len(final_pool)}只候选标的")
        return final_pool

    # ──────────────────────────────────────────────────────────────────────────
    # 1. 板块成分股爬取
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_sector_stocks(self, top_sectors: list[dict]) -> list[StockCandidate]:
        """根据Top行业爬取板块成分股."""
        all_stocks = []
        seen_symbols = set()

        for sector_info in top_sectors:
            sector = sector_info["sector"]
            board_names = SECTOR_TO_BOARD_MAP.get(sector, [sector])

            for board_name in board_names:
                try:
                    stocks = await self._fetch_board_stocks(board_name, sector)
                    for stock in stocks:
                        if stock.symbol not in seen_symbols:
                            seen_symbols.add(stock.symbol)
                            all_stocks.append(stock)
                except Exception as e:
                    logger.debug(f"板块 '{board_name}' 成分股获取失败: {e}")
                    continue

        return all_stocks

    # 各行业龙头股备用列表（当实时行情接口失效时使用）
    _FALLBACK_STOCKS = {
        "半导体": [
            {"symbol": "688981", "name": "中芯国际"},
            {"symbol": "603501", "name": "韦尔股份"},
            {"symbol": "002371", "name": "北方华创"},
            {"symbol": "688012", "name": "中微公司"},
            {"symbol": "600584", "name": "长电科技"},
        ],
        "软件服务": [
            {"symbol": "600536", "name": "中国软件"},
            {"symbol": "300033", "name": "同花顺"},
            {"symbol": "688111", "name": "金山办公"},
            {"symbol": "600570", "name": "恒生电子"},
            {"symbol": "300496", "name": "中科创达"},
        ],
        "通信设备": [
            {"symbol": "000063", "name": "中兴通讯"},
            {"symbol": "600487", "name": "亨通光电"},
            {"symbol": "300502", "name": "新易盛"},
            {"symbol": "300308", "name": "中际旭创"},
            {"symbol": "600498", "name": "烽火通信"},
        ],
        "电子元件": [
            {"symbol": "002475", "name": "立讯精密"},
            {"symbol": "000725", "name": "京东方A"},
            {"symbol": "002241", "name": "歌尔股份"},
            {"symbol": "603290", "name": "斯达半导"},
            {"symbol": "300408", "name": "三环集团"},
        ],
        "人工智能": [
            {"symbol": "002230", "name": "科大讯飞"},
            {"symbol": "688256", "name": "寒武纪"},
            {"symbol": "300418", "name": "昆仑万维"},
            {"symbol": "603000", "name": "人民网"},
            {"symbol": "300364", "name": "中文在线"},
        ],
        "银行": [
            {"symbol": "600036", "name": "招商银行"},
            {"symbol": "601398", "name": "工商银行"},
            {"symbol": "601288", "name": "农业银行"},
            {"symbol": "601939", "name": "建设银行"},
            {"symbol": "601988", "name": "中国银行"},
        ],
        "证券": [
            {"symbol": "600030", "name": "中信证券"},
            {"symbol": "601688", "name": "华泰证券"},
            {"symbol": "600837", "name": "海通证券"},
            {"symbol": "601211", "name": "国泰君安"},
            {"symbol": "000776", "name": "广发证券"},
        ],
        "保险": [
            {"symbol": "601318", "name": "中国平安"},
            {"symbol": "601628", "name": "中国人寿"},
            {"symbol": "601336", "name": "新华保险"},
            {"symbol": "601601", "name": "中国太保"},
            {"symbol": "600291", "name": "天茂集团"},
        ],
        "医疗器械": [
            {"symbol": "300760", "name": "迈瑞医疗"},
            {"symbol": "688271", "name": "联影医疗"},
            {"symbol": "300003", "name": "乐普医疗"},
            {"symbol": "688617", "name": "惠泰医疗"},
            {"symbol": "300832", "name": "新产业"},
        ],
        "生物制品": [
            {"symbol": "600276", "name": "恒瑞医药"},
            {"symbol": "000661", "name": "长春高新"},
            {"symbol": "300122", "name": "智飞生物"},
            {"symbol": "688180", "name": "君实生物"},
            {"symbol": "300142", "name": "沃森生物"},
        ],
        "化学制药": [
            {"symbol": "600276", "name": "恒瑞医药"},
            {"symbol": "000963", "name": "华东医药"},
            {"symbol": "002422", "name": "科伦药业"},
            {"symbol": "600079", "name": "人福医药"},
            {"symbol": "603259", "name": "药明康德"},
        ],
        "中药": [
            {"symbol": "000538", "name": "云南白药"},
            {"symbol": "600436", "name": "片仔癀"},
            {"symbol": "600332", "name": "白云山"},
            {"symbol": "000999", "name": "华润三九"},
            {"symbol": "600085", "name": "同仁堂"},
        ],
        "白酒": [
            {"symbol": "600519", "name": "贵州茅台"},
            {"symbol": "000858", "name": "五粮液"},
            {"symbol": "000568", "name": "泸州老窖"},
            {"symbol": "600809", "name": "山西汾酒"},
            {"symbol": "002304", "name": "洋河股份"},
        ],
        "食品饮料": [
            {"symbol": "600887", "name": "伊利股份"},
            {"symbol": "603288", "name": "海天味业"},
            {"symbol": "000895", "name": "双汇发展"},
            {"symbol": "600132", "name": "重庆啤酒"},
            {"symbol": "603517", "name": "绝味食品"},
        ],
        "家电行业": [
            {"symbol": "000333", "name": "美的集团"},
            {"symbol": "600690", "name": "海尔智家"},
            {"symbol": "000651", "name": "格力电器"},
            {"symbol": "002032", "name": "苏泊尔"},
            {"symbol": "603486", "name": "科沃斯"},
        ],
        "旅游酒店": [
            {"symbol": "601888", "name": "中国中免"},
            {"symbol": "600754", "name": "锦江酒店"},
            {"symbol": "600009", "name": "上海机场"},
            {"symbol": "002707", "name": "众信旅游"},
            {"symbol": "600258", "name": "首旅酒店"},
        ],
        "商贸百货": [
            {"symbol": "600729", "name": "重庆百货"},
            {"symbol": "002419", "name": "天虹股份"},
            {"symbol": "600697", "name": "欧亚集团"},
            {"symbol": "000501", "name": "武商集团"},
            {"symbol": "601366", "name": "利群股份"},
        ],
        "电力行业": [
            {"symbol": "600900", "name": "长江电力"},
            {"symbol": "600011", "name": "华能国际"},
            {"symbol": "600886", "name": "国投电力"},
            {"symbol": "601985", "name": "中国核电"},
            {"symbol": "600795", "name": "国电电力"},
        ],
        "煤炭行业": [
            {"symbol": "601088", "name": "中国神华"},
            {"symbol": "601225", "name": "陕西煤业"},
            {"symbol": "600188", "name": "兖矿能源"},
            {"symbol": "601699", "name": "潞安环能"},
            {"symbol": "600546", "name": "山煤国际"},
        ],
        "石油行业": [
            {"symbol": "601857", "name": "中国石油"},
            {"symbol": "600028", "name": "中国石化"},
            {"symbol": "600938", "name": "中国海油"},
            {"symbol": "002493", "name": "荣盛石化"},
            {"symbol": "000059", "name": "华锦股份"},
        ],
        "新能源": [
            {"symbol": "300750", "name": "宁德时代"},
            {"symbol": "002594", "name": "比亚迪"},
            {"symbol": "601012", "name": "隆基绿能"},
            {"symbol": "300274", "name": "阳光电源"},
            {"symbol": "002460", "name": "赣锋锂业"},
        ],
        "有色金属": [
            {"symbol": "601899", "name": "紫金矿业"},
            {"symbol": "603993", "name": "洛阳钼业"},
            {"symbol": "600362", "name": "江西铜业"},
            {"symbol": "000807", "name": "云铝股份"},
            {"symbol": "601600", "name": "中国铝业"},
        ],
        "钢铁行业": [
            {"symbol": "600019", "name": "宝钢股份"},
            {"symbol": "000932", "name": "华菱钢铁"},
            {"symbol": "600507", "name": "方大特钢"},
            {"symbol": "002110", "name": "三钢闽光"},
            {"symbol": "600808", "name": "马钢股份"},
        ],
        "化工行业": [
            {"symbol": "600309", "name": "万华化学"},
            {"symbol": "002648", "name": "卫星化学"},
            {"symbol": "600426", "name": "华鲁恒升"},
            {"symbol": "002001", "name": "新和成"},
            {"symbol": "600486", "name": "扬农化工"},
        ],
        "建材": [
            {"symbol": "600585", "name": "海螺水泥"},
            {"symbol": "000877", "name": "天山股份"},
            {"symbol": "600801", "name": "华新水泥"},
            {"symbol": "000786", "name": "北新建材"},
            {"symbol": "002791", "name": "坚朗五金"},
        ],
        "新材料": [
            {"symbol": "600143", "name": "金发科技"},
            {"symbol": "300769", "name": "德方纳米"},
            {"symbol": "603260", "name": "合盛硅业"},
            {"symbol": "300073", "name": "当升科技"},
            {"symbol": "002709", "name": "天赐材料"},
        ],
        "汽车零部件": [
            {"symbol": "600660", "name": "福耀玻璃"},
            {"symbol": "000338", "name": "潍柴动力"},
            {"symbol": "601799", "name": "星宇股份"},
            {"symbol": "603596", "name": "伯特利"},
            {"symbol": "002920", "name": "德赛西威"},
        ],
        "工程机械": [
            {"symbol": "600031", "name": "三一重工"},
            {"symbol": "000425", "name": "徐工机械"},
            {"symbol": "000157", "name": "中联重科"},
            {"symbol": "603338", "name": "浙江鼎力"},
            {"symbol": "600761", "name": "安徽合力"},
        ],
        "航天航空": [
            {"symbol": "600893", "name": "航发动力"},
            {"symbol": "600372", "name": "中航机载"},
            {"symbol": "000768", "name": "中航西飞"},
            {"symbol": "600760", "name": "中航沈飞"},
            {"symbol": "002179", "name": "中航光电"},
        ],
        "船舶制造": [
            {"symbol": "600150", "name": "中国船舶"},
            {"symbol": "601989", "name": "中国重工"},
            {"symbol": "600685", "name": "中船防务"},
            {"symbol": "601890", "name": "亚星锚链"},
            {"symbol": "300008", "name": "天海防务"},
        ],
        "专用设备": [
            {"symbol": "601766", "name": "中国中车"},
            {"symbol": "600835", "name": "上海机电"},
            {"symbol": "002008", "name": "大族激光"},
            {"symbol": "300450", "name": "先导智能"},
            {"symbol": "688188", "name": "柏楚电子"},
        ],
        "燃气": [
            {"symbol": "600635", "name": "大众公用"},
            {"symbol": "000669", "name": "ST金鸿"},
            {"symbol": "600333", "name": "长春燃气"},
            {"symbol": "601139", "name": "深圳燃气"},
            {"symbol": "600917", "name": "重庆燃气"},
        ],
        "水务": [
            {"symbol": "600008", "name": "首创环保"},
            {"symbol": "601158", "name": "重庆水务"},
            {"symbol": "600168", "name": "武汉控股"},
            {"symbol": "000544", "name": "中原环保"},
            {"symbol": "600283", "name": "钱江水利"},
        ],
        "环保行业": [
            {"symbol": "600388", "name": "龙净环保"},
            {"symbol": "002573", "name": "清新环境"},
            {"symbol": "300070", "name": "碧水源"},
            {"symbol": "000598", "name": "兴蓉环境"},
            {"symbol": "600323", "name": "瀚蓝环境"},
        ],
        "房地产开发": [
            {"symbol": "000002", "name": "万科A"},
            {"symbol": "600048", "name": "保利发展"},
            {"symbol": "001979", "name": "招商蛇口"},
            {"symbol": "600606", "name": "绿地控股"},
            {"symbol": "000069", "name": "华侨城A"},
        ],
        "房地产服务": [
            {"symbol": "001914", "name": "招商积余"},
            {"symbol": "002968", "name": "新大正"},
            {"symbol": "600658", "name": "电子城"},
            {"symbol": "002285", "name": "世联行"},
            {"symbol": "603506", "name": "南都物业"},
        ],
        "装修建材": [
            {"symbol": "002271", "name": "东方雨虹"},
            {"symbol": "000786", "name": "北新建材"},
            {"symbol": "603801", "name": "志邦家居"},
            {"symbol": "002572", "name": "索菲亚"},
            {"symbol": "603208", "name": "江山欧派"},
        ],
        "水泥建材": [
            {"symbol": "600585", "name": "海螺水泥"},
            {"symbol": "000877", "name": "天山股份"},
            {"symbol": "600801", "name": "华新水泥"},
            {"symbol": "600449", "name": "宁夏建材"},
            {"symbol": "000401", "name": "冀东水泥"},
        ],
    }

    async def _fetch_board_stocks(self, board_name: str, sector: str) -> list[StockCandidate]:
        """获取单个板块的成分股.

        原接口 stock_board_industry_cons_em（东方财富）已失效，
        改用同花顺板块指数接口 + 实时行情过滤近似获取成分股。
        当实时行情不可用时，回退到备用龙头股列表。
        """
        loop = asyncio.get_event_loop()

        try:
            # 1. 获取同花顺行业板块列表，找到板块代码
            board_list = await loop.run_in_executor(
                None,
                lambda: ak.stock_board_industry_name_ths()
            )
            if board_list is None or board_list.empty:
                # 回退到备用列表
                return self._get_fallback_stocks(board_name, sector)

            matched = board_list[board_list["name"] == board_name]
            if matched.empty:
                # 名称不完全匹配，尝试模糊匹配
                matched = board_list[board_list["name"].str.contains(board_name, na=False)]
            if matched.empty:
                logger.debug(f"未找到同花顺板块: {board_name}")
                return self._get_fallback_stocks(board_name, sector)

            board_code = str(matched.iloc[0]["code"]).strip()

            # 2. 获取板块指数数据（用于确认板块有效）
            board_index = await loop.run_in_executor(
                None,
                lambda: ak.stock_board_industry_index_ths(symbol=board_name)
            )
            if board_index is None or board_index.empty:
                return self._get_fallback_stocks(board_name, sector)

            # 3. 使用全市场实时行情，按板块关键词过滤作为成分股近似
            spot_df = await loop.run_in_executor(None, lambda: ak.stock_zh_a_spot())
            if spot_df is None or spot_df.empty:
                return self._get_fallback_stocks(board_name, sector)

            # 清洗代码（适配多种格式：sh600519/sz000001/bj920000/600519）
            spot_df["代码"] = spot_df["代码"].astype(str).str.replace(r"^(sh|sz|bj)", "", regex=True)
            # 过滤ST/退市/北交所（bj开头）/新股
            spot_df = spot_df[~spot_df["名称"].str.contains("ST|退", na=False)]
            spot_df = spot_df[~spot_df["代码"].str.startswith("8")]  # 北交所代码以8开头
            spot_df = spot_df[~spot_df["代码"].str.startswith("4")]  # 新三板
            spot_df = spot_df[~spot_df["名称"].str.contains("^N|^C", regex=True, na=False)]  # 新股

            # 按板块名称关键词过滤
            keywords = [board_name]
            # 部分常见板块增加同义词
            synonym_map = {
                "半导体": ["半导体", "芯片", "集成电路"],
                "软件服务": ["软件", "服务", "IT", "互联网"],
                "通信设备": ["通信", "设备", "5G", "光模块"],
                "电子元件": ["电子", "元件", "元器件", "被动元件"],
                "人工智能": ["人工智能", "AI", "大模型", "算力"],
                "银行": ["银行", "农商行", "城商行"],
                "证券": ["证券", "券商", "投行"],
                "保险": ["保险", "寿险", "财险"],
                "医疗器械": ["医疗器械", "医疗", "设备"],
                "生物制品": ["生物", "疫苗", "血制品"],
                "化学制药": ["化学", "制药", "原料药", "制剂"],
                "中药": ["中药", "中成药", "药材"],
                "白酒": ["白酒", "酿酒", "酒类"],
                "食品饮料": ["食品", "饮料", "零食", "乳品"],
                "家电行业": ["家电", "电器", "空调", "冰箱"],
                "旅游酒店": ["旅游", "酒店", "景区", "航空"],
                "商贸百货": ["商贸", "百货", "零售", "超市"],
                "电力行业": ["电力", "火电", "水电", "核电", "风电", "光伏"],
                "煤炭行业": ["煤炭", "焦煤", "动力煤"],
                "石油行业": ["石油", "石化", "油气"],
                "新能源": ["新能源", "光伏", "风电", "储能", "锂电"],
                "有色金属": ["有色", "铜", "铝", "锌", "稀土"],
                "钢铁行业": ["钢铁", "特钢", "普钢"],
                "化工行业": ["化工", "化学", "塑料", "橡胶"],
                "建材": ["建材", "水泥", "玻璃", "管材"],
                "新材料": ["新材料", "碳纤维", "石墨烯"],
                "汽车零部件": ["汽车", "零部件", "轮胎", "座椅"],
                "工程机械": ["机械", "工程", "挖掘机", "起重机"],
                "航天航空": ["航天", "航空", "飞机", "卫星"],
                "船舶制造": ["船舶", "造船", "海军"],
                "专用设备": ["设备", "机床", "机器人"],
                "燃气": ["燃气", "天然气"],
                "水务": ["水务", "供水", "污水"],
                "环保行业": ["环保", "环境", "固废", "水处理"],
                "房地产开发": ["房地产", "地产", "开发"],
                "房地产服务": ["物业", "服务"],
                "装修建材": ["装修", "建材", "装饰"],
                "水泥建材": ["水泥", "建材"],
            }
            if board_name in synonym_map:
                keywords = synonym_map[board_name]

            mask = spot_df["名称"].apply(
                lambda x: any(kw in str(x) for kw in keywords)
            )
            filtered = spot_df[mask].copy()

            candidates = []
            for _, row in filtered.iterrows():
                try:
                    symbol = str(row.get("代码", "")).strip()
                    name = str(row.get("名称", "")).strip()
                    if not symbol or not name:
                        continue

                    # 尝试获取成交额
                    volume = None
                    for col in ["成交额", "成交金额", "amount", "成交量"]:
                        if col in row:
                            try:
                                volume = float(row[col])
                                break
                            except (ValueError, TypeError):
                                continue

                    candidates.append(
                        StockCandidate(
                            symbol=symbol,
                            name=name,
                            sector=sector,
                            asset_class="stock",
                            source=f"板块:{board_name}",
                            daily_volume=volume,
                        )
                    )
                except Exception as e:
                    logger.debug(f"处理板块成分股行失败: {e}")
                    continue

            return candidates
        except Exception as e:
            logger.debug(f"板块 '{board_name}' 成分股获取失败: {e}")
            return self._get_fallback_stocks(board_name, sector)

    def _get_fallback_stocks(self, board_name: str, sector: str) -> list[StockCandidate]:
        """从备用列表获取龙头股."""
        stocks = self._FALLBACK_STOCKS.get(board_name, [])
        return [
            StockCandidate(
                symbol=s["symbol"],
                name=s["name"],
                sector=sector,
                asset_class="stock",
                source=f"备用列表:{board_name}",
            )
            for s in stocks
        ]

    # ──────────────────────────────────────────────────────────────────────────
    # 2. ETF筛选
    # ──────────────────────────────────────────────────────────────────────────

    # 常用ETF备用列表（当akshare接口失效时使用）
    _FALLBACK_ETF_LIST = [
        {"symbol": "510300", "name": "沪深300ETF"},
        {"symbol": "510500", "name": "中证500ETF"},
        {"symbol": "512000", "name": "券商ETF"},
        {"symbol": "512480", "name": "半导体ETF"},
        {"symbol": "512760", "name": "芯片ETF"},
        {"symbol": "515030", "name": "科技ETF"},
        {"symbol": "515050", "name": "5GETF"},
        {"symbol": "512800", "name": "银行ETF"},
        {"symbol": "512200", "name": "地产ETF"},
        {"symbol": "512010", "name": "医药ETF"},
        {"symbol": "512170", "name": "医疗ETF"},
        {"symbol": "159928", "name": "消费ETF"},
        {"symbol": "159995", "name": "芯片ETF"},
        {"symbol": "515170", "name": "食品饮料ETF"},
        {"symbol": "515790", "name": "光伏ETF"},
        {"symbol": "516160", "name": "新能源ETF"},
        {"symbol": "510880", "name": "红利ETF"},
        {"symbol": "518880", "name": "黄金ETF"},
        {"symbol": "511380", "name": "转债ETF"},
        {"symbol": "511010", "name": "国债ETF"},
    ]

    async def _fetch_sector_etfs(self, top_sectors: list[dict]) -> list[StockCandidate]:
        """筛选与Top行业相关的ETF."""
        etf_list = None
        try:
            # 获取ETF列表
            loop = asyncio.get_event_loop()
            etf_list = await loop.run_in_executor(
                None,
                lambda: ak.fund_etf_category_sina(symbol="ETF基金")
            )
        except Exception as e:
            logger.warning(f"ETF列表获取失败，使用备用列表: {e}")

        if etf_list is None or etf_list.empty:
            # 使用备用ETF列表
            etf_list = pd.DataFrame(self._FALLBACK_ETF_LIST)

        # 收集所有需要匹配的关键词
        all_keywords = set()
        for sector_info in top_sectors:
            sector = sector_info["sector"]
            keywords = SECTOR_TO_ETF_KEYWORDS.get(sector, [sector])
            all_keywords.update(keywords)

        matched_etfs = []
        seen_symbols = set()

        for _, etf in etf_list.iterrows():
            try:
                etf_name = str(etf.get("名称", ""))
                symbol = str(etf.get("代码", "")).strip()

                if not symbol or not etf_name:
                    continue
                if symbol in seen_symbols:
                    continue

                # 关键词匹配
                if any(kw in etf_name for kw in all_keywords):
                    # TODO: 获取ETF规模和流动性进行筛选
                    # 目前先按名称匹配，后续可添加规模/流动性过滤
                    seen_symbols.add(symbol)
                    matched_etfs.append(
                        StockCandidate(
                            symbol=symbol,
                            name=etf_name,
                            sector=self._infer_sector_from_etf_name(etf_name, top_sectors),
                            asset_class="ETF",
                            source="ETF筛选",
                        )
                    )
            except Exception as e:
                logger.debug(f"处理ETF行失败: {e}")
                continue

        return matched_etfs

    def _infer_sector_from_etf_name(self, etf_name: str, top_sectors: list[dict]) -> str:
        """根据ETF名称推断所属行业."""
        for sector_info in top_sectors:
            sector = sector_info["sector"]
            keywords = SECTOR_TO_ETF_KEYWORDS.get(sector, [])
            if any(kw in etf_name for kw in keywords):
                return sector
        return "mixed"

    # ──────────────────────────────────────────────────────────────────────────
    # 3. 热门股补充
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_hot_stocks(self) -> list[StockCandidate]:
        """获取热门股补充（龙虎榜等）."""
        hot_stocks = []

        # 龙虎榜
        try:
            lhb_stocks = await self._fetch_lhb_stocks()
            hot_stocks.extend(lhb_stocks)
        except Exception as e:
            logger.debug(f"龙虎榜获取失败: {e}")

        # 资金流向排行
        try:
            flow_stocks = await self._fetch_fund_flow_stocks()
            hot_stocks.extend(flow_stocks)
        except Exception as e:
            logger.debug(f"资金流向获取失败: {e}")

        return hot_stocks

    async def _fetch_lhb_stocks(self) -> list[StockCandidate]:
        """获取龙虎榜股票."""
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: ak.stock_lhb_detail_daily_sina()
        )

        if df is None or df.empty:
            return []

        candidates = []
        for _, row in df.head(20).iterrows():
            try:
                symbol = str(row.get("代码", "")).strip()
                name = str(row.get("名称", "")).strip()
                if symbol and name:
                    candidates.append(
                        StockCandidate(
                            symbol=symbol,
                            name=name,
                            sector="hot",
                            asset_class="stock",
                            source="龙虎榜",
                        )
                    )
            except Exception:
                continue

        return candidates

    async def _fetch_fund_flow_stocks(self) -> list[StockCandidate]:
        """获取主力资金流入排行股票.

        原接口 stock_individual_fund_flow_rank 已失效，
        改用 stock_fund_flow_individual 获取当日个股资金流向排行。
        """
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_fund_flow_individual()
            )
        except Exception:
            return []

        if df is None or df.empty:
            return []

        candidates = []
        for _, row in df.head(20).iterrows():
            try:
                symbol = str(row.get("代码", "")).strip()
                name = str(row.get("名称", "")).strip()
                if symbol and name:
                    candidates.append(
                        StockCandidate(
                            symbol=symbol,
                            name=name,
                            sector="hot",
                            asset_class="stock",
                            source="资金流向",
                        )
                    )
            except Exception:
                continue

        return candidates
