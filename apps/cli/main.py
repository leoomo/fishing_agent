#!/usr/bin/env python3
"""
智能钓鱼助手 CLI 应用

基于 LangChain 1.0+ 的智能钓鱼助手，提供：
- 实时天气查询
- 智能钓鱼推荐
- 7因子评分算法
- 自然语言交互
"""

import os
import sys
import warnings
from dotenv import load_dotenv

# 抑制 LangSmith UUID v7 警告（库内部兼容性问题）
warnings.filterwarnings("ignore", message="LangSmith now uses UUID v7")

# 加载环境变量
load_dotenv()


def main():
    """主程序入口"""
    try:
        from packages.agent_fishing import create_agent

        print("🎣 智能钓鱼助手 v3.1.1")
        print("=" * 50)
        print("输入您的问题，例如：")
        print("- 明天杭州钓鱼怎么样？")
        print("- 北京今天天气如何？")
        print("- 推荐一个钓鱼地点")
        print("输入 'quit' 退出程序")
        print("=" * 50)

        # 创建智能体
        agent = create_agent(model_provider="zhipu", enable_logging=True)

        # 交互式对话
        while True:
            try:
                user_input = input("\n🎣 请输入您的问题: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 感谢使用智能钓鱼助手！")
                    break

                if not user_input:
                    continue

                print("\n🤔 正在思考...")
                response = agent.run(user_input)
                print(f"\n🎯 回答: {response}")

            except KeyboardInterrupt:
                print("\n👋 程序已退出")
                break
            except Exception as e:
                print(f"\n❌ 处理请求时出错: {str(e)}")
                print("请检查您的网络连接和API密钥配置")

    except ImportError as e:
        print(f"❌ 导入模块失败: {str(e)}")
        print("请确保已安装所有依赖: uv sync")
    except Exception as e:
        print(f"❌ 程序启动失败: {str(e)}")
        print("请检查环境变量配置和API密钥")


if __name__ == "__main__":
    main()
