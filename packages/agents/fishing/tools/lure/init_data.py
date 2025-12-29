"""
初始化测试数据

包含常见路亚对象鱼、钓组和示例装备数据。
"""

import json
from .database import get_db


def init_fish_data():
    """初始化鱼类数据"""
    db = get_db()

    fish_data = [
        # 淡水鱼类
        {
            "name_cn": "大嘴鲈",
            "name_en": "Largemouth Bass",
            "aliases": json.dumps(["黑鲈", "大嘴黑鲈", "加州鲈"], ensure_ascii=False),
            "category": "淡水",
            "habitat": "中上层",
            "active_temp_min": 15,
            "active_temp_max": 28,
            "optimal_temp_min": 20,
            "optimal_temp_max": 25,
            "active_seasons": json.dumps(["春", "夏", "秋"], ensure_ascii=False),
            "feeding_habits": "肉食",
            "lure_difficulty": "新手",
            "fight_intensity": "中等",
            "recommended_lures": json.dumps(["软虫", "米诺", "摇滚", "VIB", "铅头钩"], ensure_ascii=False),
            "recommended_rigs": json.dumps(["德州钓组", "无铅钓组", "卡罗莱纳钓组", "倒吊钓组"], ensure_ascii=False),
            "recommended_rod_power": json.dumps(["ML", "M", "MH"], ensure_ascii=False),
            "recommended_line_lb_min": 8,
            "recommended_line_lb_max": 20,
        },
        {
            "name_cn": "翘嘴鲌",
            "name_en": "Topmouth Culter",
            "aliases": json.dumps(["翘嘴", "翘嘴白", "白条"], ensure_ascii=False),
            "category": "淡水",
            "habitat": "中上层",
            "active_temp_min": 10,
            "active_temp_max": 30,
            "optimal_temp_min": 18,
            "optimal_temp_max": 26,
            "active_seasons": json.dumps(["春", "夏", "秋", "冬"], ensure_ascii=False),
            "feeding_habits": "肉食",
            "lure_difficulty": "新手",
            "fight_intensity": "中等",
            "recommended_lures": json.dumps(["米诺", "VIB", "亮片", "波爬"], ensure_ascii=False),
            "recommended_rigs": json.dumps(["直接连接", "前导线钓组"], ensure_ascii=False),
            "recommended_rod_power": json.dumps(["L", "ML", "M"], ensure_ascii=False),
            "recommended_line_lb_min": 6,
            "recommended_line_lb_max": 15,
        },
        {
            "name_cn": "鳜鱼",
            "name_en": "Mandarin Fish",
            "aliases": json.dumps(["桂鱼", "季花鱼", "花鲫"], ensure_ascii=False),
            "category": "淡水",
            "habitat": "底层",
            "active_temp_min": 15,
            "active_temp_max": 30,
            "optimal_temp_min": 20,
            "optimal_temp_max": 28,
            "active_seasons": json.dumps(["春", "夏", "秋"], ensure_ascii=False),
            "feeding_habits": "肉食",
            "lure_difficulty": "进阶",
            "fight_intensity": "激烈",
            "recommended_lures": json.dumps(["软虫", "卷尾蛆", "T尾", "铅头钩"], ensure_ascii=False),
            "recommended_rigs": json.dumps(["德州钓组", "铅头钩钓组", "倒吊钓组"], ensure_ascii=False),
            "recommended_rod_power": json.dumps(["M", "MH", "H"], ensure_ascii=False),
            "recommended_line_lb_min": 10,
            "recommended_line_lb_max": 25,
        },
        {
            "name_cn": "黑鱼",
            "name_en": "Snakehead",
            "aliases": json.dumps(["乌鱼", "乌棒", "蛇头鱼"], ensure_ascii=False),
            "category": "淡水",
            "habitat": "全水层",
            "active_temp_min": 15,
            "active_temp_max": 35,
            "optimal_temp_min": 22,
            "optimal_temp_max": 30,
            "active_seasons": json.dumps(["春", "夏", "秋"], ensure_ascii=False),
            "feeding_habits": "肉食",
            "lure_difficulty": "新手",
            "fight_intensity": "激烈",
            "recommended_lures": json.dumps(["雷蛙", "软饵", "米诺", "VIB"], ensure_ascii=False),
            "recommended_rigs": json.dumps(["雷蛙钓组", "德州钓组", "无铅钓组"], ensure_ascii=False),
            "recommended_rod_power": json.dumps(["MH", "H", "XH"], ensure_ascii=False),
            "recommended_line_lb_min": 20,
            "recommended_line_lb_max": 50,
        },
        {
            "name_cn": "鲶鱼",
            "name_en": "Catfish",
            "aliases": json.dumps(["塘鲺", "胡子鲶"], ensure_ascii=False),
            "category": "淡水",
            "habitat": "底层",
            "active_temp_min": 12,
            "active_temp_max": 32,
            "optimal_temp_min": 18,
            "optimal_temp_max": 28,
            "active_seasons": json.dumps(["春", "夏", "秋"], ensure_ascii=False),
            "feeding_habits": "杂食",
            "lure_difficulty": "新手",
            "fight_intensity": "中等",
            "recommended_lures": json.dumps(["软虫", "卷尾蛆", "铅头钩", "VIB"], ensure_ascii=False),
            "recommended_rigs": json.dumps(["德州钓组", "卡罗莱纳钓组", "铅头钩钓组"], ensure_ascii=False),
            "recommended_rod_power": json.dumps(["M", "MH"], ensure_ascii=False),
            "recommended_line_lb_min": 12,
            "recommended_line_lb_max": 30,
        },
        {
            "name_cn": "马口鱼",
            "name_en": "Chinese Minnow",
            "aliases": json.dumps(["马口", "桃花鱼"], ensure_ascii=False),
            "category": "淡水",
            "habitat": "中上层",
            "active_temp_min": 10,
            "active_temp_max": 25,
            "optimal_temp_min": 15,
            "optimal_temp_max": 22,
            "active_seasons": json.dumps(["春", "夏", "秋"], ensure_ascii=False),
            "feeding_habits": "杂食",
            "lure_difficulty": "新手",
            "fight_intensity": "温和",
            "recommended_lures": json.dumps(["微型米诺", "微型亮片", "飞蝇"], ensure_ascii=False),
            "recommended_rigs": json.dumps(["直接连接", "马口专用钓组"], ensure_ascii=False),
            "recommended_rod_power": json.dumps(["UL", "L"], ensure_ascii=False),
            "recommended_line_lb_min": 2,
            "recommended_line_lb_max": 6,
        },
    ]

    # 检查是否已有数据
    existing = db.execute("SELECT COUNT(*) as cnt FROM fish_species")
    if existing[0]['cnt'] > 0:
        print(f"Fish data already exists ({existing[0]['cnt']} records)")
        return

    for fish in fish_data:
        columns = ', '.join(fish.keys())
        placeholders = ', '.join(['?'] * len(fish))
        query = f"INSERT INTO fish_species ({columns}) VALUES ({placeholders})"
        db.execute_write(query, tuple(fish.values()))

    print(f"Inserted {len(fish_data)} fish records")


def init_rig_data():
    """初始化钓组数据"""
    db = get_db()

    rig_types = [
        {
            "name_cn": "德州钓组",
            "name_en": "Texas Rig",
            "category": "经典软饵钓组",
            "description": "最经典的软饵钓组，子弹铅在前，鱼钩埋入软饵中，防挂性能极强",
            "difficulty": "新手",
            "anti_snag_rating": 5,
            "sensitivity_rating": 3,
            "versatility_rating": 5,
        },
        {
            "name_cn": "无铅钓组",
            "name_en": "Weightless Rig",
            "category": "经典软饵钓组",
            "description": "不使用配重的软饵钓组，软饵自然下沉，适合高活性鱼",
            "difficulty": "新手",
            "anti_snag_rating": 5,
            "sensitivity_rating": 5,
            "versatility_rating": 4,
        },
        {
            "name_cn": "卡罗莱纳钓组",
            "name_en": "Carolina Rig",
            "category": "经典软饵钓组",
            "description": "铅坠与软饵分离，软饵悬浮在底部上方，适合搜索大范围水域",
            "difficulty": "进阶",
            "anti_snag_rating": 3,
            "sensitivity_rating": 4,
            "versatility_rating": 4,
        },
        {
            "name_cn": "倒吊钓组",
            "name_en": "Drop Shot Rig",
            "category": "经典软饵钓组",
            "description": "铅坠在最下方，软饵悬浮在水中，适合精细作钓和被动鱼",
            "difficulty": "进阶",
            "anti_snag_rating": 2,
            "sensitivity_rating": 5,
            "versatility_rating": 3,
        },
        {
            "name_cn": "铅头钩钓组",
            "name_en": "Jig Head Rig",
            "category": "铅头钩钓组",
            "description": "铅头与鱼钩一体，简单直接，适合各种软饵",
            "difficulty": "新手",
            "anti_snag_rating": 2,
            "sensitivity_rating": 4,
            "versatility_rating": 5,
        },
        {
            "name_cn": "雷蛙钓组",
            "name_en": "Frog Rig",
            "category": "特殊钓组",
            "description": "专门用于雷蛙的钓组，适合水草密集区打黑",
            "difficulty": "新手",
            "anti_snag_rating": 5,
            "sensitivity_rating": 2,
            "versatility_rating": 2,
        },
    ]

    # 检查是否已有数据
    existing = db.execute("SELECT COUNT(*) as cnt FROM rig_types")
    if existing[0]['cnt'] > 0:
        print(f"Rig data already exists ({existing[0]['cnt']} records)")
        return

    for rig in rig_types:
        columns = ', '.join(rig.keys())
        placeholders = ', '.join(['?'] * len(rig))
        query = f"INSERT INTO rig_types ({columns}) VALUES ({placeholders})"
        db.execute_write(query, tuple(rig.values()))

    print(f"Inserted {len(rig_types)} rig type records")


def init_brand_data():
    """初始化品牌数据"""
    db = get_db()

    brands = [
        {"name_cn": "禧玛诺", "name_en": "Shimano", "country": "日本", "tier": "高端"},
        {"name_cn": "达亿瓦", "name_en": "Daiwa", "country": "日本", "tier": "高端"},
        {"name_cn": "阿布", "name_en": "Abu Garcia", "country": "瑞典", "tier": "中高端"},
        {"name_cn": "美国纯钓", "name_en": "Pure Fishing", "country": "美国", "tier": "中高端"},
        {"name_cn": "渔猎人", "name_en": "Fishman", "country": "日本", "tier": "高端"},
        {"name_cn": "宝飞龙", "name_en": "Megabass", "country": "日本", "tier": "高端"},
        {"name_cn": "路亚之", "name_en": "Jackall", "country": "日本", "tier": "中高端"},
        {"name_cn": "光威", "name_en": "GW", "country": "中国", "tier": "中端"},
        {"name_cn": "迪佳", "name_en": "Tica", "country": "中国台湾", "tier": "中端"},
        {"name_cn": "汉鼎", "name_en": "Handing", "country": "中国", "tier": "入门"},
    ]

    # 检查是否已有数据
    existing = db.execute("SELECT COUNT(*) as cnt FROM brands")
    if existing[0]['cnt'] > 0:
        print(f"Brand data already exists ({existing[0]['cnt']} records)")
        return

    for brand in brands:
        columns = ', '.join(brand.keys())
        placeholders = ', '.join(['?'] * len(brand))
        query = f"INSERT INTO brands ({columns}) VALUES ({placeholders})"
        db.execute_write(query, tuple(brand.values()))

    print(f"Inserted {len(brands)} brand records")


def init_fish_knowledge():
    """初始化鱼类知识"""
    db = get_db()

    # 获取鱼类ID
    bass = db.execute("SELECT id FROM fish_species WHERE name_cn = '大嘴鲈'")
    if not bass:
        print("No fish data found, skipping knowledge init")
        return

    bass_id = bass[0]['id']

    knowledge_data = [
        {
            "species_id": bass_id,
            "knowledge_type": "behavior",
            "title": "大嘴鲈的捕食行为",
            "content": """## 捕食特点

大嘴鲈是典型的**伏击型掠食者**，具有以下捕食特点：

### 1. 伏击策略
- 喜欢躲藏在水草、倒木、岩石等掩体附近
- 等待猎物经过时突然出击
- 攻击速度极快，通常一击必中

### 2. 视觉依赖
- 主要依靠视觉发现猎物
- 对移动的物体特别敏感
- 水质清澈时更加活跃

### 3. 领地意识
- 成年鲈鱼有明显的领地意识
- 会攻击进入领地的任何物体
- 这也是反应饵能钓到鲈鱼的原因

## 路亚启示

理解这些习性后，我们可以：
1. **找准标点**：水草边缘、倒木旁、码头下
2. **精准抛投**：将饵送到掩体附近
3. **控制速度**：适当停顿，给鲈鱼攻击时间""",
            "tags": json.dumps(["习性", "捕食", "伏击", "标点"], ensure_ascii=False),
        },
        {
            "species_id": bass_id,
            "knowledge_type": "season",
            "title": "春季鲈鱼钓法详解",
            "content": """## 春季鲈鱼特点

春季（3-5月）是钓鲈鱼的黄金季节，主要原因：

### 产卵前期（Pre-spawn）
- 水温10-15℃时开始向浅水区移动
- 觅食欲望强烈，为产卵储备能量
- **最佳拟饵**：米诺、摇滚、软虫

### 产卵期（Spawn）
- 水温15-20℃时开始筑巢产卵
- 雄鱼护巢，领地意识极强
- **最佳拟饵**：软虫慢拖、反应饵

### 产卵后期（Post-spawn）
- 雌鱼恢复期，活动范围大
- 雄鱼继续护巢直到鱼苗独立
- **最佳拟饵**：各类拟饵均可

## 春季钓点选择

1. **浅滩区**：水深1-3米的浅水区
2. **水草区**：新生水草边缘
3. **硬底区**：沙质或砾石底""",
            "tags": json.dumps(["春季", "产卵", "浅水", "水草"], ensure_ascii=False),
        },
        {
            "species_id": None,
            "knowledge_type": "technique",
            "title": "德州钓组完全指南",
            "content": """## 什么是德州钓组

德州钓组（Texas Rig）是最经典的软饵钓组之一，特点是：
- 鱼钩尖埋入软饵中，极强的防挂性能
- 子弹铅在前，软饵在后
- 适合在障碍区作钓

## 组装方法

### 所需配件
1. 子弹铅（3.5g-14g）
2. 曲柄钩（2/0-5/0）
3. 软饵（卷尾蛆、蜥蜴、蠕虫等）
4. 挡珠（可选）

### 组装步骤
1. 将子弹铅穿入主线
2. 绑上曲柄钩
3. 将软饵头部穿入钩眼
4. 沿软饵身体穿出
5. 将钩尖轻轻埋入软饵背部

## 操作技巧

### 基本操作
1. 抛投到标点
2. 等待沉底
3. 轻轻抖动竿尖
4. 慢慢拖动
5. 重复以上动作

### 中鱼技巧
- 感觉到"咚"的吃口后
- 稍微送线
- 大力扬竿刺鱼""",
            "tags": json.dumps(["德州钓组", "软饵", "组装", "技巧"], ensure_ascii=False),
        },
    ]

    # 检查是否已有数据
    existing = db.execute("SELECT COUNT(*) as cnt FROM fish_knowledge")
    if existing[0]['cnt'] > 0:
        print(f"Knowledge data already exists ({existing[0]['cnt']} records)")
        return

    for knowledge in knowledge_data:
        columns = ', '.join(knowledge.keys())
        placeholders = ', '.join(['?'] * len(knowledge))
        query = f"INSERT INTO fish_knowledge ({columns}) VALUES ({placeholders})"
        db.execute_write(query, tuple(knowledge.values()))

    print(f"Inserted {len(knowledge_data)} knowledge records")


def init_equipment_data():
    """初始化装备数据"""
    db = get_db()

    # 获取品牌ID
    brands = db.execute("SELECT id, name_cn FROM brands")
    brand_map = {b['name_cn']: b['id'] for b in brands}

    equipment_data = [
        # 鱼竿
        {
            "name": "禧玛诺ZODIAS 264ML",
            "category": "鱼竿",
            "brand_id": brand_map.get("禧玛诺"),
            "model": "264ML",
            "price_min": 680,
            "price_max": 680,
            "description": "经典入门级路亚竿，ML硬度适合新手操控，长度适中岸钓船钓通用",
            "features": "富士K导环,软木握把,高碳素",
            "target_fish": "鲈鱼,翘嘴",
            "user_level": "入门",
        },
        {
            "name": "达亿瓦BASS X 662ML",
            "category": "鱼竿",
            "brand_id": brand_map.get("达亿瓦"),
            "model": "662ML",
            "price_min": 450,
            "price_max": 450,
            "description": "性价比极高的入门路亚竿，适合预算有限的新手",
            "features": "EVA握把,富士导环",
            "target_fish": "鲈鱼,翘嘴,鳜鱼",
            "user_level": "入门",
        },
        {
            "name": "光威 路亚竿M调",
            "category": "鱼竿",
            "brand_id": brand_map.get("光威"),
            "model": "LY-M-2.1",
            "price_min": 180,
            "price_max": 220,
            "description": "国产高性价比路亚竿，适合预算有限的钓友",
            "features": "碳素材质,不锈钢导环",
            "target_fish": "鲈鱼,翘嘴",
            "user_level": "入门",
        },
        # 渔轮
        {
            "name": "禧玛诺NASCI 2500",
            "category": "渔轮",
            "brand_id": brand_map.get("禧玛诺"),
            "model": "NASCI 2500",
            "price_min": 580,
            "price_max": 580,
            "description": "中端纺车轮，顺滑度高，适合路亚使用",
            "features": "5+1轴承,速比5.0:1,最大刹车4kg",
            "target_fish": "鲈鱼,翘嘴",
            "user_level": "入门",
        },
        {
            "name": "达亿瓦 REVROS 2500",
            "category": "渔轮",
            "brand_id": brand_map.get("达亿瓦"),
            "model": "REVROS 2500",
            "price_min": 280,
            "price_max": 280,
            "description": "入门级纺车轮，性价比高",
            "features": "4轴承,速比5.3:1",
            "target_fish": "鲈鱼,翘嘴",
            "user_level": "入门",
        },
        # 拟饵
        {
            "name": "Megabass Vision 110",
            "category": "拟饵",
            "brand_id": brand_map.get("宝飞龙"),
            "model": "Vision 110",
            "price_min": 158,
            "price_max": 168,
            "description": "经典米诺，泳姿优美，远投性能出色",
            "features": "悬浮型,110mm,14g",
            "target_fish": "鲈鱼,翘嘴",
            "user_level": "进阶",
        },
        {
            "name": "OSP BENT MINNOW 106F",
            "category": "拟饵",
            "brand_id": brand_map.get("路亚之"),
            "model": "BENT MINNOW 106F",
            "price_min": 120,
            "price_max": 130,
            "description": "弯曲米诺，独特泳姿，适合钓翘嘴",
            "features": "浮水型,106mm,10g",
            "target_fish": "翘嘴,鲈鱼",
            "user_level": "进阶",
        },
    ]

    # 检查是否已有数据
    existing = db.execute("SELECT COUNT(*) as cnt FROM equipment")
    if existing[0]['cnt'] > 0:
        print(f"Equipment data already exists ({existing[0]['cnt']} records)")
        return

    for eq in equipment_data:
        columns = ', '.join(eq.keys())
        placeholders = ', '.join(['?'] * len(eq))
        query = f"INSERT INTO equipment ({columns}) VALUES ({placeholders})"
        db.execute_write(query, tuple(eq.values()))

    print(f"Inserted {len(equipment_data)} equipment records")


def init_all_data():
    """初始化所有数据"""
    print("Initializing lure equipment data...")
    init_brand_data()
    init_fish_data()
    init_rig_data()
    init_equipment_data()
    init_fish_knowledge()
    print("Data initialization complete!")


if __name__ == "__main__":
    init_all_data()
