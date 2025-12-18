#!/usr/bin/env python3
"""
智能钓鱼助手调试脚本
支持多种运行模式和模型提供商切换
新增：爬虫调试和管理功能
"""

import os
import sys
import time
import warnings
import json
import sqlite3
from typing import Optional, Dict, Any

# 抑制警告
warnings.filterwarnings("ignore", message="LangSmith now uses UUID v7")

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")

    required_keys = {
        'DASHSCOPE_API_KEY': '通义千问 API',
        'CAIYUN_API_KEY': '彩云天气 API',
        'AMAP_API_KEY': '高德地图 API'
    }

    # 可选的爬虫配置
    optional_keys = {
        'DB_PATH': '数据库路径',
        'JWT_SECRET_KEY': 'JWT密钥'
    }

    missing_keys = []
    for key, name in required_keys.items():
        if os.getenv(key):
            print(f"✅ {name}: 已配置")
        else:
            print(f"❌ {name}: 未配置")
            missing_keys.append(key)

    # 检查可选配置
    for key, name in optional_keys.items():
        if os.getenv(key):
            print(f"✅ {name}: 已配置 (可选)")
        else:
            print(f"⚠️  {name}: 未配置 (可选)")

    if missing_keys:
        print(f"\n⚠️  缺少必需的API密钥: {', '.join(missing_keys)}")
        print("请检查 .env 文件配置")
        return False

    print("✅ 环境配置检查通过")
    return True

def test_agent_creation(model_provider: str = "qwen") -> bool:
    """测试Agent创建"""
    print(f"\n🤖 测试 {model_provider} Agent 创建...")

    try:
        from packages.agent_fishing import create_agent, ModelFactory

        # 检查模型提供商可用性
        available_providers = ModelFactory.list_providers()
        print(f"📋 可用模型提供商: {list(available_providers.keys())}")

        if model_provider not in available_providers:
            print(f"❌ 不支持的模型提供商: {model_provider}")
            return False

        # 创建Agent
        agent = create_agent(
            model_provider=model_provider,
            enable_logging=True,
            timeout=60
        )

        print(f"✅ {model_provider} Agent 创建成功")
        print(f"🛠️  工具数量: {len(agent.tools)}")
        print(f"📊 模型: {agent.model_provider}")

        return True

    except Exception as e:
        print(f"❌ Agent 创建失败: {str(e)}")
        return False

def test_single_query(agent, query: str) -> bool:
    """测试单个查询"""
    print(f"\n📝 测试查询: {query}")
    print("🤔 正在思考...")

    try:
        start_time = time.time()
        response = agent.run(query)
        end_time = time.time()

        print(f"⏱️  响应时间: {end_time - start_time:.2f}秒")
        print(f"📄 响应长度: {len(response)}字符")
        print(f"\n🎯 回答:\n{response}")

        return True

    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        return False

def debug_weather_api_calls():
    """调试天气API调用和温度数据"""
    print("\n" + "="*60)
    print("🔍 调试天气API调用和温度数据")
    print("="*60)

    try:
        from packages.agent_fishing.tools.fishing.weather_api import get_weather_data as _get_weather_data
        from packages.agent_fishing.utils.coordinate import get_coordinates

        # 1. 测试地理编码
        print("📍 测试地理编码...")
        coords = get_coordinates("杭州")
        print(f"✅ 杭州坐标: {coords}")

        # 2. 测试天气数据获取
        print("\n🌤️ 测试天气数据获取...")
        from datetime import datetime
        target_date = datetime.now()
        weather_data = _get_weather_data("杭州", target_date)
        print(f"✅ 天气数据原始结构: {list(weather_data.keys())}")

        # 3. 检查温度字段
        print(f"\n🌡️ 检查温度相关字段:")
        temp_fields = {}
        for key, value in weather_data.items():
            if any(temp_keyword in key.lower() for temp_keyword in ['temp', 'temperature']):
                temp_fields[key] = value
                print(f"  {key}: {value} (类型: {type(value).__name__})")

        # 4. 检查小时温度数据
        hourly_temps = weather_data.get('hourly_temps', [])
        if hourly_temps:
            print(f"\n📊 小时温度数据: {len(hourly_temps)}个数据点")
            print(f"  温度范围: {min(hourly_temps):.1f}°C - {max(hourly_temps):.1f}°C")
            print(f"  平均温度: {sum(hourly_temps)/len(hourly_temps):.1f}°C")
        else:
            print(f"\n❌ 缺少小时温度数据")

        # 5. 检查数据质量
        data_quality = weather_data.get('data_quality', 'unknown')
        print(f"\n📈 数据质量: {data_quality}")

        return weather_data, coords

    except Exception as e:
        print(f"❌ 天气API调试失败: {str(e)}")
        import traceback
        print("\n📋 详细错误信息:")
        traceback.print_exc()
        return None, None

def direct_query_mode(agent, query: str):
    """直接查询模式 - 无需手动输入"""
    print("\n" + "="*60)
    print(f"🎣 智能钓鱼助手 - 直接查询模式")
    print("="*60)
    print(f"📝 查询内容: {query}")
    print("="*60)

    try:
        print("🤔 通义千问正在分析...")
        start_time = time.time()
        response = agent.run(query)
        end_time = time.time()

        print(f"\n⏱️  响应时间: {end_time - start_time:.2f}秒")
        print(f"📄 响应长度: {len(response)}字符")
        print(f"\n🎯 智能回答:\n{'='*60}")
        print(response)
        print(f"{'='*60}")

    except KeyboardInterrupt:
        print("\n\n⏹️  查询已取消")
    except Exception as e:
        print(f"\n❌ 处理请求时出错: {str(e)}")
        print("💡 请检查网络连接和API密钥配置")

def interactive_mode(agent):
    """交互模式"""
    print("\n" + "="*60)
    print("🎣 智能钓鱼助手 - 交互模式")
    print("="*60)
    print("💡 示例查询:")
    print("  - 明天杭州钓鱼怎么样？")
    print("  - 北京今天天气如何？")
    print("  - 推荐一些钓鱼装备")
    print("  - 现在几点了？")
    print("  - 今天白天上海钓鱼好吗？")
    print("\n输入 'quit', 'exit' 或 '退出' 结束对话")
    print("="*60)

    try:
        while True:
            user_input = input("\n🎣 请输入您的问题: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 感谢使用智能钓鱼助手！")
                break

            if not user_input:
                continue

            print(f"\n📝 您的问题: {user_input}")
            print("🤔 正在思考...")

            try:
                start_time = time.time()
                response = agent.run(user_input)
                end_time = time.time()

                print(f"\n🎯 回答 ({end_time - start_time:.2f}秒):")
                print(response)

            except KeyboardInterrupt:
                print("\n\n⏹️  查询已取消")
                continue
            except Exception as e:
                print(f"\n❌ 处理请求时出错: {str(e)}")
                print("💡 请检查网络连接和API密钥配置")

    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")

def batch_test_mode(agent):
    """批量测试模式"""
    print("\n" + "="*60)
    print("🧪 批量测试模式")
    print("="*60)

    test_queries = [
        "现在几点了？",
        "北京今天天气如何？",
        "明天杭州钓鱼怎么样？",
        "推荐一些钓鱼装备",
        "今天白天上海钓鱼好吗？",
        "这个周末适合钓鱼吗？"
    ]

    success_count = 0
    total_time = 0

    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 测试 {i}/{len(test_queries)}: {query}")

        try:
            start_time = time.time()
            response = agent.run(query)
            end_time = time.time()

            query_time = end_time - start_time
            total_time += query_time

            print(f"✅ 成功 ({query_time:.2f}秒, {len(response)}字符)")
            success_count += 1

            # 显示响应摘要
            response_preview = response[:100] + "..." if len(response) > 100 else response
            print(f"📄 摘要: {response_preview}")

        except Exception as e:
            print(f"❌ 失败: {str(e)}")

    print(f"\n📊 测试结果:")
    print(f"✅ 成功: {success_count}/{len(test_queries)}")
    print(f"⏱️  总耗时: {total_time:.2f}秒")
    print(f"📈 平均耗时: {total_time/len(test_queries):.2f}秒")
    print(f"🎯 成功率: {success_count/len(test_queries)*100:.1f}%")

def show_agent_stats(agent):
    """显示Agent统计信息"""
    print("\n📊 Agent 统计信息:")
    print("="*40)

    try:
        stats = agent.get_stats()
        llm_stats = agent.get_llm_stats()

        print(f"🤖 模型提供商: {stats.get('model_provider', 'Unknown')}")
        print(f"🛠️  工具数量: {stats.get('tools_count', 0)}")
        print(f"⏱️  超时设置: {stats.get('timeout', 0)}秒")
        print(f"🏗️  架构: {stats.get('architecture', 'Unknown')}")

        print(f"\n📈 LLM 调用统计:")
        print(f"  总调用次数: {llm_stats.get('total_model_calls', 0)}")
        print(f"  总错误次数: {llm_stats.get('total_errors', 0)}")
        print(f"  成功率: {llm_stats.get('success_rate', 0):.1f}%")
        print(f"  总Token数: {llm_stats.get('total_tokens', 0)}")

    except Exception as e:
        print(f"❌ 获取统计信息失败: {str(e)}")

def check_database():
    """检查数据库连接和状态"""
    print("\n🔍 检查数据库连接...")

    # 获取数据库路径
    db_path = os.getenv("DB_PATH", "packages/agent_fishing/tools/lure/data/equipment.db")

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查爬虫相关表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'crawler_%'")
        tables = cursor.fetchall()

        if not tables:
            print("⚠️  未找到爬虫相关表，可能需要初始化数据库")
        else:
            print(f"✅ 找到爬虫相关表: {[t[0] for t in tables]}")

            # 检查任务数量
            cursor.execute("SELECT COUNT(*) FROM crawler_tasks")
            task_count = cursor.fetchone()[0]
            print(f"📊 当前爬虫任务数: {task_count}")

            # 检查最新任务
            cursor.execute("SELECT id, task_name, status, created_at FROM crawler_tasks ORDER BY created_at DESC LIMIT 5")
            recent_tasks = cursor.fetchall()
            if recent_tasks:
                print("\n📋 最近的任务:")
                for task in recent_tasks:
                    print(f"  ID {task[0]}: {task[1]} [{task[2]}] - {task[3]}")

        conn.close()
        print("✅ 数据库连接正常")
        return True

    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False

def create_crawler_task(task_type: str = "taobao", keywords: list = None, max_pages: int = 5, shop_url: str = None):
    """创建爬虫任务"""
    print(f"\n🕷️ 创建{task_type}爬虫任务...")

    try:
        from packages.scraper.models import CrawlerTask
        from packages.agent_fishing.tools.lure.orm.session import get_db_session
        from datetime import datetime

        # 默认关键词
        if not keywords:
            keywords = ["路亚竿"]

        # 创建任务配置
        task_config = {
            "keywords": keywords,
            "max_pages": max_pages,
            "proxy": None,
            "rpa_mode": True,  # 标记为RPA模式
            "browser": {
                "headless": os.getenv("RPA_HEADLESS", "true").lower() == "true",
                "timeout": int(os.getenv("RPA_TIMEOUT", "30000"))
            },
            "anti_detection": {
                "enable_stealth": os.getenv("RPA_STEALTH", "true").lower() == "true",
                "simulate_human": os.getenv("RPA_HUMAN", "true").lower() == "true"
            }
        }

        # 如果是店铺URL，添加到配置
        if shop_url:
            task_config["shop_url"] = shop_url

        # 创建任务
        task = CrawlerTask(
            task_type=task_type,
            task_name=f"{task_type}RPA爬虫 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
            config=json.dumps(task_config)
        )

        with get_db_session() as session:
            session.add(task)
            session.commit()
            task_id = task.id

        print(f"✅ 成功创建RPA爬虫任务，ID: {task_id}")
        print(f"📝 任务配置:")
        print(f"  - 关键词: {keywords}")
        print(f"  - 最大页数: {max_pages}")
        print(f"  - 平台: {task_type}")
        print(f"  - 模式: RPA (Playwright)")
        if shop_url:
            print(f"  - 店铺URL: {shop_url}")

        return task_id

    except Exception as e:
        print(f"❌ 创建爬虫任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def execute_crawler_task(task_id: int):
    """执行爬虫任务"""
    print(f"\n🚀 执行爬虫任务 {task_id}...")

    try:
        from packages.scraper.executor.task_queue import CrawlerTaskQueue
        from packages.agent_fishing.tools.lure.orm.session import get_db_session
        from packages.scraper.models import CrawlerTask, TaskStatus

        # 获取任务
        with get_db_session() as session:
            task = session.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()

            if not task:
                print(f"❌ 任务不存在: {task_id}")
                return False

            # 更新状态为运行中
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.utcnow()
            session.commit()

        print(f"✅ 任务 {task_id} 状态已更新为运行中")

        # TODO: 这里可以添加实际的爬虫执行逻辑
        # 目前只是模拟执行
        print("⚠️  注意：当前仅为演示模式，未执行真实爬虫")
        print("💡 要执行真实爬虫，请确保爬虫服务正在运行")

        return True

    except Exception as e:
        print(f"❌ 执行爬虫任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def monitor_crawler_task(task_id: int, timeout: int = 60):
    """监控爬虫任务状态"""
    print(f"\n👀 监控爬虫任务 {task_id} (超时: {timeout}秒)...")

    from packages.agent_fishing.tools.lure.orm.session import get_db_session
    from packages.scraper.models import CrawlerTask, TaskStatus
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with get_db_session() as session:
                task = session.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()

                if not task:
                    print(f"❌ 任务不存在: {task_id}")
                    return False

                # 显示当前状态
                print(f"\r📊 任务状态: {task.status.value} | "
                      f"总计: {task.total_items} | "
                      f"成功: {task.success_items} | "
                      f"失败: {task.failed_items} | "
                      f"耗时: {int(time.time() - start_time)}秒", end="")

                # 检查是否完成
                if task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED]:
                    print(f"\n\n✅ 任务完成！")
                    print(f"📋 最终状态: {task.status.value}")
                    print(f"📊 处理结果: 成功 {task.success_items}/{task.total_items}")
                    if task.error_message:
                        print(f"❌ 错误信息: {task.error_message}")
                    return True

                time.sleep(2)

        except Exception as e:
            print(f"\n❌ 监控失败: {str(e)}")
            return False

    print(f"\n\n⏰ 监控超时")
    return False

def list_crawler_tasks(limit: int = 10):
    """列出爬虫任务"""
    print(f"\n📋 最近 {limit} 个爬虫任务:")
    print("-"*80)

    try:
        from packages.agent_fishing.tools.lure.orm.session import get_db_session
        from packages.scraper.models import CrawlerTask

        with get_db_session() as session:
            tasks = session.query(CrawlerTask).order_by(CrawlerTask.created_at.desc()).limit(limit).all()

            if not tasks:
                print("📭 暂无爬虫任务")
                return

            print(f"{'ID':<5} {'类型':<8} {'状态':<10} {'进度':<20} {'任务名称':<30} {'创建时间'}")
            print("-"*80)

            for task in tasks:
                progress = f"{task.success_items}/{task.total_items}"
                if task.total_items == 0:
                    progress = "0/0"

                created_at = task.created_at.strftime("%m-%d %H:%M") if task.created_at else "N/A"
                print(f"{task.id:<5} {task.task_type:<8} {task.status.value:<10} "
                      f"{progress:<20} {task.task_name[:30]:<30} {created_at}")

    except Exception as e:
        print(f"❌ 获取任务列表失败: {str(e)}")

def clean_crawler_tasks(status: str = None, days: int = 7):
    """清理旧的爬虫任务"""
    print(f"\n🧹 清理爬虫任务...")

    try:
        from packages.agent_fishing.tools.lure.orm.session import get_db_session
        from packages.scraper.models import CrawlerTask, TaskStatus
        from datetime import datetime, timedelta

        with get_db_session() as session:
            query = session.query(CrawlerTask)

            # 按状态过滤
            if status:
                status_map = {
                    'success': TaskStatus.SUCCESS,
                    'failed': TaskStatus.FAILED,
                    'pending': TaskStatus.PENDING,
                    'running': TaskStatus.RUNNING
                }
                if status.lower() in status_map:
                    query = query.filter(CrawlerTask.status == status_map[status.lower()])

            # 按时间过滤
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(CrawlerTask.created_at < cutoff_date)

            # 获取要删除的任务数量
            count = query.count()

            if count == 0:
                print("✅ 没有需要清理的任务")
                return

            # 确认删除
            print(f"⚠️  将删除 {count} 个 {days} 天前的任务")
            if status:
                print(f"   状态过滤: {status}")

            # 执行删除
            query.delete()
            session.commit()

            print(f"✅ 成功清理 {count} 个旧任务")

    except Exception as e:
        print(f"❌ 清理任务失败: {str(e)}")

def check_rpa_environment():
    """检查RPA环境配置"""
    print("\n🔍 检查RPA环境配置...")

    # 检查Playwright是否安装
    try:
        import playwright
        print(f"✅ Playwright已安装: v{playwright.__version__}")
    except ImportError:
        print("❌ Playwright未安装，请运行: playwright install")
        return False

    # 检查浏览器
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browsers = []
            if p.chromium:
                browsers.append("Chromium")
            if p.firefox:
                browsers.append("Firefox")
            if p.webkit:
                browsers.append("WebKit")
            print(f"✅ 可用浏览器: {', '.join(browsers)}")
    except Exception as e:
        print(f"❌ 浏览器检查失败: {str(e)}")
        return False

    # 检查Cookie目录
    cookie_path = os.path.join("shared", "data", "cookies")
    if os.path.exists(cookie_path):
        print(f"✅ Cookie目录存在: {cookie_path}")
        # 检查是否有淘宝的cookie文件
        taobao_cookies = [f for f in os.listdir(cookie_path) if "taobao" in f.lower()]
        if taobao_cookies:
            print(f"✅ 找到淘宝Cookie文件: {taobao_cookies}")
        else:
            print("⚠️  未找到淘宝Cookie文件，可能需要重新登录")
    else:
        print(f"⚠️  Cookie目录不存在，将创建: {cookie_path}")
        os.makedirs(cookie_path, exist_ok=True)

    # 检查RPA环境变量
    rpa_env_vars = {
        "RPA_HEADLESS": "无头模式",
        "RPA_TIMEOUT": "超时时间(ms)",
        "RPA_STEALTH": "反检测模式",
        "RPA_HUMAN": "模拟人类行为"
    }

    for var, desc in rpa_env_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {desc}({var}): {value}")
        else:
            print(f"⚠️  {desc}({var}): 未设置，将使用默认值")

    return True

def execute_rpa_crawler(task_id: int):
    """执行RPA爬虫任务"""
    print(f"\n🤖 执行RPA爬虫任务 {task_id}...")

    try:
        from packages.agent_fishing.tools.lure.orm.session import get_db_session
        from packages.scraper.models import CrawlerTask, TaskStatus
        from datetime import datetime

        # 获取任务
        with get_db_session() as session:
            task = session.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()

            if not task:
                print(f"❌ 任务不存在: {task_id}")
                return False

            # 解析任务配置
            config = json.loads(task.config) if task.config else {}
            is_rpa_mode = config.get("rpa_mode", False)

            if not is_rpa_mode:
                print("⚠️  任务未配置为RPA模式")
                return False

            # 更新状态为运行中
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.utcnow()
            session.commit()

        print(f"✅ 任务 {task_id} 状态已更新为运行中")
        print(f"📋 RPA配置:")
        print(f"  - 浏览器: {'无头模式' if config.get('browser', {}).get('headless') else '有头模式'}")
        print(f"  - 超时: {config.get('browser', {}).get('timeout', 30000)}ms")
        print(f"  - 反检测: {'启用' if config.get('anti_detection', {}).get('enable_stealth') else '禁用'}")

        # 检查是否有店铺URL
        shop_url = config.get("shop_url")
        keywords = config.get("keywords", [])

        # 模拟RPA执行（真实执行需要完整的RPA环境）
        print("\n⚠️  注意：当前为演示模式")
        if shop_url:
            print(f"📌 目标店铺: {shop_url}")
        if keywords:
            print(f"🔍 搜索关键词: {', '.join(keywords)}")

        print("\n💡 要执行真实的RPA爬虫，需要:")
        print("  1. 有效的淘宝登录状态")
        print("  2. 安装并配置Playwright浏览器")
        print("  3. 确保网络连接正常")

        # 更新任务状态为完成（演示用）
        with get_db_session() as session:
            task = session.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
            task.status = TaskStatus.SUCCESS
            task.end_time = datetime.utcnow()
            task.total_items = 50  # 模拟数据
            task.success_items = 45
            task.failed_items = 5
            session.commit()

        return True

    except Exception as e:
        print(f"❌ 执行RPA爬虫任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_rpa_login():
    """测试RPA登录状态"""
    print("\n🔐 测试RPA登录状态...")

    try:
        from packages.scraper.rpa.login_manager import LoginManager
        from packages.scraper.rpa.config import RPAConfig

        # 加载配置
        config = RPAConfig.from_env()
        login_manager = LoginManager(config)

        # 检查登录状态
        if login_manager.is_logged_in():
            print("✅ 已登录淘宝")
            return True
        else:
            print("❌ 未登录淘宝")
            print("\n💡 登录选项:")
            print("1. 手动登录: python -m tools.crawler.rpa.taobao_rpa --login")
            print("2. 使用Cookie文件")
            print("3. 二维码登录")
            return False

    except Exception as e:
        print(f"❌ 检查登录状态失败: {str(e)}")
        print("\n💡 可能的解决方案:")
        print("1. 安装依赖: playwright install")
        print("2. 检查Cookie文件路径")
        return False

def take_screenshot(url: str, save_path: str = "screenshot.png"):
    """截取网页截图（调试用）"""
    print(f"\n📸 截取网页截图: {url}")

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # 非无头模式便于调试
            page = browser.new_page()

            # 设置视窗大小
            page.set_viewport_size({"width": 1920, "height": 1080})

            # 访问页面
            print(f"🌐 正在访问: {url}")
            page.goto(url, timeout=30000)

            # 等待页面加载
            page.wait_for_load_state("networkidle")

            # 截图
            screenshot_path = os.path.join("shared", "data", "screenshots", save_path)
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ 截图已保存: {screenshot_path}")

            browser.close()
            return screenshot_path

    except Exception as e:
        print(f"❌ 截图失败: {str(e)}")
        return None

def crawler_test_mode():
    """爬虫测试模式"""
    print("\n"+"="*60)
    print("🕷️ 爬虫测试模式 (RPA)")
    print("="*60)

    # 1. 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，无法进行爬虫测试")
        return

    # 2. 检查RPA环境
    if not check_rpa_environment():
        print("\n❌ RPA环境检查失败，无法进行RPA爬虫测试")
        return

    # 3. 检查登录状态
    print("\n📌 步骤1: 检查淘宝登录状态...")
    if not test_rpa_login():
        print("\n⚠️  未登录淘宝，但继续创建测试任务")

    # 4. 创建测试任务
    print("\n📌 步骤2: 创建RPA测试任务...")
    task_id = create_crawler_task(
        task_type="taobao",
        keywords=["路亚竿", "钓鱼竿"],
        max_pages=2,
        shop_url="https://shop123456.taobao.com"  # 示例URL
    )

    if not task_id:
        print("\n❌ 创建爬虫任务失败")
        return

    # 5. 执行RPA爬虫
    print("\n📌 步骤3: 执行RPA爬虫...")
    if not execute_rpa_crawler(task_id):
        print("\n❌ 执行RPA爬虫失败")
        return

    # 6. 监控任务
    print("\n📌 步骤4: 监控任务状态...")
    monitor_crawler_task(task_id, timeout=5)

    # 7. 显示任务列表
    print("\n📌 步骤5: 查看任务列表...")
    list_crawler_tasks(limit=5)

    print("\n✅ RPA爬虫测试完成！")
    print("\n💡 提示:")
    print("1. 真实爬虫需要有效的淘宝登录状态")
    print("2. 可以通过Web界面管理爬虫任务: http://localhost:5173/crawler")
    print("3. 查看截图: shared/data/screenshots/")

def print_usage():
    """打印使用说明"""
    print("🎣 智能钓鱼助手调试脚本 v3.1.1")
    print("="*60)
    print("用法:")
    print("  python debug_agent.py [model_provider] [mode] [query]")
    print("")
    print("参数:")
    print("  model_provider  模型提供商 (qwen, zhipu, openai, doubao)")
    print("  mode           运行模式")
    print("  query          查询内容 (direct模式时使用)")
    print("")
    print("可用模式:")
    print("  direct            直接查询 (默认)")
    print("  interactive       交互模式")
    print("  test              测试模式")
    print("  batch             批量测试")
    print("  debug             调试模式")
    print("  crawler           爬虫测试模式 (RPA) ⭐")
    print("  crawler-create    创建普通爬虫任务")
    print("  crawler-create-shop 创建店铺爬虫任务")
    print("  crawler-rpa-check  检查RPA环境和登录状态")
    print("  crawler-screenshot 截取网页截图")
    print("  crawler-list      列出爬虫任务")
    print("  crawler-monitor   监控爬虫任务")
    print("  crawler-clean     清理爬虫任务")
    print("")
    print("示例:")
    print("  python debug_agent.py                    # 通义千问 + 直接查询(默认)")
    print("  python debug_agent.py qwen               # 通义千问 + 直接查询")
    print("  python debug_agent.py qwen interactive   # 通义千问 + 交互模式")
    print("  python debug_agent.py qwen debug          # 通义千问 + 调试模式")
    print("  python debug_agent.py qwen direct \"今天白天北京钓鱼怎么样？\"  # 自定义查询")
    print("  python debug_agent.py _ crawler          # RPA爬虫测试模式")
    print("  python debug_agent.py _ crawler-create   # 创建普通爬虫任务")
    print("  python debug_agent.py _ crawler-create-shop https://shop123.taobao.com  # 创建店铺爬虫任务")
    print("  python debug_agent.py _ crawler-rpa-check # 检查RPA环境和登录状态")
    print("  python debug_agent.py _ crawler-screenshot https://item.taobao.com/xxx.htm  # 截取商品截图")
    print("  python debug_agent.py _ crawler-list     # 列出最近任务")
    print("  python debug_agent.py _ crawler-monitor 5 # 监控任务ID=5")
    print("  python debug_agent.py _ crawler-clean   # 清理7天前的任务")
    print("="*60)

def main():
    """主函数"""
    # 检查帮助参数
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['-h', '--help', 'help']:
        print_usage()
        return

    print("🎣 智能钓鱼助手调试脚本 v3.1.2")
    print("="*60)

    # 解析命令行参数
    model_provider = "qwen"  # 默认使用通义千问
    mode = "direct"         # 默认直接查询模式
    query = "明天余杭区钓鱼什么情况？"  # 默认查询

    if len(sys.argv) > 1:
        model_provider = sys.argv[1]
    if len(sys.argv) > 2:
        mode = sys.argv[2]
    if len(sys.argv) > 3:
        query = sys.argv[3]

    # 爬虫模式不需要 model_provider
    if mode.startswith("crawler"):
        print(f"🕷️ 运行模式: {mode}")

        # 根据不同的爬虫模式执行相应功能
        if mode == "crawler":
            # 爬虫测试模式
            crawler_test_mode()
            return
        elif mode == "crawler-create":
            # 创建爬虫任务
            task_id = create_crawler_task("taobao", ["路亚竿"], 5)
            if task_id:
                print(f"\n✅ 任务创建成功，ID: {task_id}")
                print("💡 使用以下命令监控任务:")
                print(f"   python debug_agent.py _ crawler-monitor {task_id}")
            return
        elif mode == "crawler-create-shop":
            # 创建店铺爬虫任务
            shop_url = query if query else "https://shop123456.taobao.com"
            task_id = create_crawler_task(
                task_type="taobao",
                keywords=["路亚竿"],
                max_pages=5,
                shop_url=shop_url
            )
            if task_id:
                print(f"\n✅ 店铺爬虫任务创建成功，ID: {task_id}")
                print(f"📌 目标店铺: {shop_url}")
                print("💡 使用以下命令监控任务:")
                print(f"   python debug_agent.py _ crawler-monitor {task_id}")
            return
        elif mode == "crawler-rpa-check":
            # 检查RPA环境
            check_rpa_environment()
            test_rpa_login()
            return
        elif mode == "crawler-screenshot":
            # 截取网页截图
            url = query if query else "https://www.taobao.com"
            take_screenshot(url)
            return
        elif mode == "crawler-list":
            # 列出爬虫任务
            limit = int(query) if query and query.isdigit() else 10
            list_crawler_tasks(limit)
            return
        elif mode == "crawler-monitor":
            # 监控特定任务
            if query and query.isdigit():
                task_id = int(query)
                monitor_crawler_task(task_id)
            else:
                print("❌ 请提供任务ID")
                print("示例: python debug_agent.py _ crawler-monitor 123")
            return
        elif mode == "crawler-clean":
            # 清理爬虫任务
            status_filter = query if query in ['success', 'failed', 'pending', 'running'] else None
            clean_crawler_tasks(status=status_filter, days=7)
            return

    print(f"🤖 使用模型: {model_provider}")
    print(f"🎮 运行模式: {mode}")
    if mode == "direct":
        print(f"📝 查询内容: {query}")
    elif mode == "debug":
        print(f"🔍 调试模式: 检查天气API和温度数据")
    elif mode == "interactive":
        print(f"💡 提示: 使用 'python debug_agent.py' 进入直接查询模式")

    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，程序退出")
        return

    # 测试Agent创建
    agent = None
    try:
        from packages.agent_fishing import create_agent
        agent = create_agent(
            model_provider=model_provider,
            enable_logging=True,
            timeout=60
        )
    except Exception as e:
        print(f"\n❌ Agent创建失败: {str(e)}")
        print("\n💡 可能的解决方案:")
        print("  1. 检查 .env 文件中的API密钥配置")
        print("  2. 确保网络连接正常")
        print("  3. 运行 'uv sync' 安装依赖")
        return

    # 根据模式运行
    if mode == "test":
        # 测试模式：运行几个示例查询
        test_queries = [
            "现在几点了？",
            "今天杭州钓鱼怎么样？"
        ]

        for query in test_queries:
            if not test_single_query(agent, query):
                print("⚠️  测试失败，但继续其他测试")

    elif mode == "batch":
        # 批量测试模式
        batch_test_mode(agent)

    elif mode == "debug":
        # 调试模式：检查天气API
        weather_data, coords = debug_weather_api_calls()
        if weather_data and coords:
            print(f"\n✅ API调试完成，现在测试完整查询...")
            direct_query_mode(agent, query)

    elif mode == "direct":
        # 直接查询模式
        direct_query_mode(agent, query)

    else:  # interactive or default
        # 交互模式
        interactive_mode(agent)

    # 显示统计信息
    if agent:
        show_agent_stats(agent)

if __name__ == "__main__":
    main()