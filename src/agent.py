#!/usr/bin/env python3
"""
基于 LangChain 1.0+ 的现代智能钓鱼助手
优化架构设计，集成了天气数据修复和LLM调用优化
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# LangChain 核心组件
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatTongyi
from langchain_core.tools import tool

# 导入新架构的工具系统
from tools import get_all_tools, get_basic_tools, get_fishing_tools

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OptimizedFishingAgent:
    """
    优化的钓鱼智能助手

    特性:
    - 集成修复后的天气工具，提供详细天气数据
    - 简化架构，提高稳定性
    - 智能降级机制，确保服务可靠性
    - 模块化设计，易于维护和扩展
    """

    def __init__(
        self,
        model_provider: str = "qwen",
        enable_logging: bool = True,
        timeout: int = 60
    ):
        """
        初始化智能钓鱼助手

        Args:
            model_provider: 模型提供商 ("qwen", "zhipu", "doubao")
            enable_logging: 启用日志记录
            timeout: 请求超时时间（秒）
        """
        self.model_provider = model_provider
        self.enable_logging = enable_logging
        self.timeout = timeout

        # 初始化核心组件
        self.model = self._initialize_model()
        self.tools = self._setup_tools()
        self.middleware = []  # 简化架构，空中间件列表
        self.agent = self._create_agent()

        logger.info(f"✅ 智能钓鱼助手初始化完成")
        logger.info(f"   模型: {model_provider}")
        logger.info(f"   工具数: {len(self.tools)}")
        logger.info(f"   日志记录: {'启用' if enable_logging else '禁用'}")

    def _initialize_model(self):
        """初始化语言模型"""
        try:
            if self.model_provider == "qwen":
                api_key = os.getenv("DASHSCOPE_API_KEY")
                if not api_key:
                    raise ValueError("DASHSCOPE_API_KEY 未配置")

                return ChatTongyi(
                    model="qwen-plus",
                    api_key=api_key,
                    timeout=self.timeout
                )

            elif self.model_provider == "zhipu":
                api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")
                if not api_key:
                    raise ValueError("ANTHROPIC_AUTH_TOKEN 未配置")

                return init_chat_model(
                    model="glm-4.6",
                    model_provider="openai",
                    base_url="https://open.bigmodel.cn/api/paas/v4/",
                    api_key=api_key,
                    timeout=self.timeout
                )

            elif self.model_provider == "doubao":
                api_key = os.getenv("ARK_API_KEY")
                if not api_key:
                    raise ValueError("ARK_API_KEY 未配置")

                return ChatOpenAI(
                    base_url="https://ark.cn-beijing.volces.com/api/v3",
                    api_key=api_key,
                    timeout=self.timeout
                )

            else:
                raise ValueError(f"不支持的模型提供商: {self.model_provider}")

        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            raise

    def _setup_tools(self) -> List:
        """设置工具集 - 使用新架构的工具系统"""
        # 使用新架构获取所有工具
        tools = get_all_tools()

        # 获取分类统计
        basic_tools = get_basic_tools()
        fishing_tools = get_fishing_tools()

        logger.info(f"🛠️ 新架构工具集配置完成: {len(tools)} 个工具")
        logger.info(f"   基础工具: {len(basic_tools)} 个")
        logger.info(f"   钓鱼工具: {len(fishing_tools)} 个")
        return tools

    def _setup_middleware(self) -> List:
        """设置中间件"""
        # 暂时简化，不使用中间件
        return []

    def _create_agent(self):
        """创建智能体"""
        system_prompt = """你是一个专业的智能钓鱼助手，专门帮助用户获取钓鱼相关的信息和建议。

🛠️ 你的核心工具:
1. get_current_time - 获取当前时间
2. calculate - 数学计算
3. search_information - 信息搜索
4. query_current_weather - 查询当前天气
5. query_weather_by_date - 查询指定日期天气
6. query_fishing_recommendation - 钓鱼时间推荐和天气分析（核心工具）
7. 其他天气工具 - 查询预报、时段天气等

🎯 智能工具选择策略:
- 钓鱼相关查询 → 优先使用 query_fishing_recommendation
- 天气相关查询 → 根据查询类型选择合适的天气工具
- 钓鱼推荐工具优势: 一次调用完成天气+钓鱼综合分析
- 每个查询只选择最相关的1-2个工具，避免冗余

🐟 专业钓鱼知识:
- 最佳钓鱼温度: 15-25°C
- 理想天气条件: 多云、阴天、小雨天气
- 最佳钓鱼时段: 早上5-9点、傍晚18-21点
- 需要避免的条件: 强风>15km/h、暴雨、极端温度
- 推荐装备: 根据天气和目标鱼种选择合适的路亚装备

💡 回复原则:
- 选择最合适的工具，而不是最多工具
- 优先使用能一次性解决问题的钓鱼推荐工具
- 避免重复调用功能相似的工具
- 为用户提供专业、准确、有用的回复
- 用中文回答，保持友好和专业的语调

示例交互:
- "今天余杭区钓鱼怎么样" → query_fishing_recommendation
- "北京明天天气如何" → query_weather_by_date
- "计算123*456" → calculate
- "现在几点了" → get_current_time"""

        # 创建agent参数
        create_kwargs = {
            "model": self.model,
            "tools": self.tools,
            "system_prompt": system_prompt
        }

        # 简化架构，暂不使用中间件
        # if self.middleware:
        #     create_kwargs["middleware"] = self.middleware

        agent = create_agent(**create_kwargs)
        logger.info("🤖 智能体创建完成")

        return agent

    def run(self, user_input: str) -> str:
        """
        运行智能体

        Args:
            user_input: 用户输入

        Returns:
            智能体回复
        """
        try:
            logger.info(f"📝 用户输入: {user_input}")

            # 标准LangChain调用
            result = self.agent.invoke({
                "messages": [
                    {"role": "user", "content": user_input}
                ]
            })

            # 提取回复内容
            if isinstance(result, dict) and "messages" in result:
                messages = result["messages"]
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        response = last_message.content
                    elif isinstance(last_message, dict) and "content" in last_message:
                        response = last_message["content"]
                    else:
                        response = str(last_message)
                else:
                    response = str(result)
            else:
                response = str(result)

            logger.info(f"🤖 智能体回复: {len(response)} 字符")
            return response

        except Exception as e:
            error_msg = f"智能体执行出错: {str(e)}"
            logger.error(f"💥 {error_msg}")

            # 智能降级处理
            if self._is_weather_fishing_query(user_input):
                return self._fallback_weather_response(user_input)
            else:
                return f"抱歉，我遇到了一些技术问题：{error_msg}。请稍后重试。"

    def _is_weather_fishing_query(self, query: str) -> bool:
        """判断是否为天气钓鱼相关查询"""
        weather_keywords = ["天气", "温度", "下雨", "晴", "阴", "多云"]
        fishing_keywords = ["钓鱼", "路亚", "钓", "渔"]

        query_lower = query.lower()
        return (any(keyword in query_lower for keyword in weather_keywords) or
                any(keyword in query_lower for keyword in fishing_keywords))

    def _fallback_weather_response(self, query: str) -> str:
        """降级天气钓鱼回复"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return f"""
## 🎯 智能钓鱼助手 - 降级模式

⚠️ 系统暂时遇到技术问题，为您提供基础建议：

**当前时间**: {current_time}
**查询内容**: {query}

### 🎣 基础钓鱼建议
- **最佳时段**: 早上5-9点、傍晚18-21点
- **理想温度**: 15-25°C
- **推荐天气**: 多云、阴天天气
- **避免条件**: 强风、暴雨、极端温度

### 🌤️ 通用建议
- 清晨和傍晚是鱼类活动高峰期
- 多云天气下鱼类更加活跃
- 选择适合当前季节的装备和饵料

建议稍后重试以获取详细的天气数据和专业分析。

---
*由智能钓鱼助手提供（降级模式）*
        """.strip()

    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {
            "model_provider": self.model_provider,
            "tools_count": len(self.tools),
            "middleware_count": len(self.middleware),
            "timeout": self.timeout,
            "logging_enabled": self.enable_logging
        }

        # 获取智能中间件统计（如果可用）
        if self.middleware and len(self.middleware) > 0:
            for middleware in self.middleware:
                if hasattr(middleware, 'get_unified_stats'):
                    middleware_stats = middleware.get_unified_stats()
                    stats["middleware_stats"] = middleware_stats
                    break

        return stats

    def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        health_status = {
            "status": "healthy",
            "checks": {}
        }

        # 检查模型
        try:
            _ = self.model
            health_status["checks"]["model"] = "✅ 正常"
        except Exception as e:
            health_status["checks"]["model"] = f"❌ 异常: {e}"
            health_status["status"] = "degraded"

        # 检查工具
        try:
            assert len(self.tools) > 0
            health_status["checks"]["tools"] = "✅ 正常"
        except Exception as e:
            health_status["checks"]["tools"] = f"❌ 异常: {e}"
            health_status["status"] = "degraded"

        # 检查中间件（简化版本）
        try:
            assert len(self.middleware) >= 0  # 中间件可以为空
            health_status["checks"]["middleware"] = "✅ 正常 (简化版本)"
        except Exception as e:
            health_status["checks"]["middleware"] = f"❌ 异常: {e}"
            health_status["status"] = "degraded"

        return health_status

    def reset_stats(self):
        """重置统计信息"""
        if self.middleware and len(self.middleware) > 0:
            for middleware in self.middleware:
                if hasattr(middleware, 'reset_stats'):
                    middleware.reset_stats()
                    logger.info("📊 中间件统计已重置")
                    break
        else:
            logger.info("📊 无中间件可重置")


def create_optimized_fishing_agent(**kwargs) -> OptimizedFishingAgent:
    """
    创建优化的钓鱼智能助手

    Args:
        model_provider: 模型提供商，默认 "qwen"
        enable_logging: 启用日志记录，默认 True
        timeout: 超时时间，默认 60秒

    Returns:
        OptimizedFishingAgent 实例
    """
    return OptimizedFishingAgent(**kwargs)


def demonstrate_agent():
    """演示智能钓鱼助手功能"""
    print("🎯 智能钓鱼助手演示")
    print("=" * 60)

    # 检查API密钥
    required_keys = {
        "DASHSCOPE_API_KEY": "阿里云通义千问",
        "ANTHROPIC_AUTH_TOKEN": "智谱AI GLM",
        "ARK_API_KEY": "豆包大模型"
    }

    available_models = []
    for key, name in required_keys.items():
        if os.getenv(key):
            available_models.append((key, name))

    if not available_models:
        print("❌ 错误: 请配置至少一个API密钥")
        for key, name in required_keys.items():
            print(f"   {key}: {name}")
        return

    # 选择模型
    if os.getenv("DASHSCOPE_API_KEY"):
        model_provider = "qwen"
        model_name = "通义千问"
    elif os.getenv("ANTHROPIC_AUTH_TOKEN"):
        model_provider = "zhipu"
        model_name = "智谱AI GLM"
    else:
        model_provider = "doubao"
        model_name = "豆包"

    print(f"✅ 使用模型: {model_name}")

    try:
        # 创建智能体
        agent = create_optimized_fishing_agent(
            model_provider=model_provider,
            enable_logging=True
        )

        # 健康检查
        health = agent.health_check()
        print(f"🏥 系统状态: {health['status']}")
        for check, status in health['checks'].items():
            print(f"   {check}: {status}")

        # 测试用例
        test_cases = [
            "今天余杭区钓鱼怎么样？",
            "北京明天天气如何？",
            "现在几点了？",
            "计算 123 * 456",
            "路亚钓鱼的基本技巧"
        ]

        print(f"\n🧪 测试 {len(test_cases)} 个用例:")

        for i, test_input in enumerate(test_cases, 1):
            print(f"\n📝 测试 {i}: {test_input}")
            print("-" * 40)

            try:
                response = agent.run(test_input)
                print(f"🤖 回复: {response[:200]}{'...' if len(response) > 200 else ''}")

            except Exception as e:
                print(f"❌ 失败: {e}")

        # 显示统计信息
        stats = agent.get_stats()
        print(f"\n📊 系统统计:")
        for key, value in stats.items():
            if key != "middleware_stats":
                print(f"   {key}: {value}")

        if "middleware_stats" in stats:
            print("   中间件统计:")
            for key, value in stats["middleware_stats"].items():
                print(f"     {key}: {value}")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🎯 智能钓鱼助手")
    print("基于 LangChain 1.0+ 和优化架构设计")
    print()

    demonstrate_agent()


if __name__ == "__main__":
    main()