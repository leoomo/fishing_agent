#!/usr/bin/env python3
"""
智能钓鱼助手主程序入口

基于 LangChain 1.0+ 的智能钓鱼助手，提供：
- 实时天气查询
- 智能钓鱼推荐
- 7因子评分算法
- 自然语言交互
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """主程序入口"""
    try:
        from agent import create_optimized_fishing_agent

        print("🎣 智能钓鱼助手 - LangChain 1.0+")
        print("=" * 50)
        print("输入您的问题，例如：")
        print("- 明天杭州钓鱼怎么样？")
        print("- 北京今天天气如何？")
        print("- 推荐一个钓鱼地点")
        print("输入 'quit' 退出程序")
        print("=" * 50)

        # 创建智能体
        agent = create_optimized_fishing_agent()

        # 交互式对话
        while True:
            try:
                user_input = input("\n🎣 请输入您的问题: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 感谢使用智能钓鱼助手！")
                    break

                if not user_input:
                    continue

                print(f"\n🤔 正在思考...")
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
