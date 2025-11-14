#!/usr/bin/env python3
"""
验证日志中间件集成

快速检查日志中间件是否正确集成到项目中。
"""

import os
import sys

def check_files():
    """检查必要的文件是否存在"""
    print("🔍 检查文件结构")

    required_files = [
        "services/middleware/__init__.py",
        "services/middleware/config.py",
        "services/middleware/logging_middleware.py",
        "test_logging_middleware.py",
        "example_logging_middleware.py",
        ".env.middleware.example"
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n⚠️  缺少文件: {len(missing_files)}")
        return False

    print("\n✅ 所有必需文件都存在")
    return True


def check_imports():
    """检查导入是否正常"""
    print("\n🔍 检查导入")

    try:
        sys.path.insert(0, '.')

        # 测试配置导入
        from services.middleware import MiddlewareConfig
        print("✅ MiddlewareConfig 导入成功")

        # 测试配置功能
        config = MiddlewareConfig()
        print(f"✅ 默认配置: 级别={config.log_level}, 控制台={config.log_to_console}")

        # 测试环境变量导入
        env_config = MiddlewareConfig.from_env()
        print("✅ 环境变量配置加载成功")

        return True

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def check_integration():
    """检查智能体集成"""
    print("\n🔍 检查智能体集成")

    try:
        from modern_langchain_agent import ModernLangChainAgent
        print("✅ ModernLangChainAgent 导入成功")

        # 检查是否有日志相关参数
        import inspect
        sig = inspect.signature(ModernLangChainAgent.__init__)
        params = list(sig.parameters.keys())

        expected_params = ['model_provider', 'enable_logging', 'middleware_config']
        missing_params = [p for p in expected_params if p not in params]

        if missing_params:
            print(f"⚠️  缺少参数: {missing_params}")
            return False
        else:
            print("✅ 智能体包含日志中间件参数")

        return True

    except Exception as e:
        print(f"❌ 集成检查失败: {e}")
        return False


def check_env_example():
    """检查环境变量示例"""
    print("\n🔍 检查环境变量示例")

    env_file = ".env.middleware.example"
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()

        required_vars = [
            'AGENT_LOG_LEVEL',
            'AGENT_LOG_CONSOLE',
            'AGENT_LOG_FILE',
            'AGENT_PERF_MONITOR',
            'AGENT_TOOL_TRACKING'
        ]

        missing_vars = [var for var in required_vars if var not in content]

        if missing_vars:
            print(f"⚠️  环境变量示例缺少: {missing_vars}")
            return False
        else:
            print("✅ 环境变量示例完整")

        return True
    else:
        print("❌ 环境变量示例文件不存在")
        return False


def check_logs_directory():
    """检查日志目录"""
    print("\n🔍 检查日志目录")

    if os.path.exists("logs"):
        print("✅ logs 目录存在")
        return True
    else:
        print("⚠️  logs 目录不存在（创建时会自动创建）")
        return True  # 这是正常的


def main():
    """主验证函数"""
    print("🚀 AgentLoggingMiddleware 集成验证")
    print("=" * 50)

    checks = [
        check_files,
        check_imports,
        check_integration,
        check_env_example,
        check_logs_directory
    ]

    results = []
    for check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {check_func.__name__} 执行失败: {e}")
            results.append(False)

    # 总结
    passed = sum(results)
    total = len(results)

    print(f"\n📊 验证结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有检查都通过！日志中间件已成功集成。")
        print("\n💡 下一步:")
        print("1. 运行 test_logging_middleware.py 进行功能测试")
        print("2. 运行 example_logging_middleware.py 查看使用示例")
        print("3. 在你的应用中启用 enable_logging=True")
    else:
        print("⚠️  部分检查未通过，请检查上述错误信息。")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)