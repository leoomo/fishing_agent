#!/usr/bin/env python3
"""
微信登录功能快速配置脚本
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()


def print_banner():
    """打印横幅"""
    print("="*60)
    print("📱 微信登录功能配置向导")
    print("="*60)


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    return True


def install_dependencies():
    """安装必要的依赖"""
    print("\n📦 检查并安装依赖...")

    required_packages = ["requests", "fastapi", "python-dotenv"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"安装缺失的依赖: {', '.join(missing_packages)}")
        os.system(f"uv add {' '.join(missing_packages)}")
    else:
        print("✅ 所有依赖已安装")


def setup_env_file():
    """设置.env文件"""
    print("\n⚙️  配置环境变量...")

    env_path = project_root / ".env"
    env_example_path = project_root / ".env.example"

    # 如果.env不存在，从.example复制
    if not env_path.exists():
        if env_example_path.exists():
            print("从.env.example复制.env文件...")
            import shutil
            shutil.copy(env_example_path, env_path)
        else:
            print("创建新的.env文件...")
            env_path.write_text("")

    # 读取当前.env内容
    env_content = env_path.read_text() if env_path.exists() else ""

    # 检查必需的配置
    required_configs = {
        "WECHAT_APPID": {
            "description": "微信小程序AppID",
            "example": "wx1234567890abcdef"
        },
        "WECHAT_SECRET": {
            "description": "微信小程序AppSecret",
            "example": "your-wechat-secret-here"
        },
        "JWT_SECRET_KEY": {
            "description": "JWT密钥（至少32字符）",
            "example": "super-secret-jwt-key-min-32-chars"
        }
    }

    missing_configs = []

    for config_key, config_info in required_configs.items():
        if not os.getenv(config_key):
            missing_configs.append((config_key, config_info))

    if missing_configs:
        print("\n❌ 缺失以下环境变量:")
        for config_key, config_info in missing_configs:
            print(f"   - {config_key}: {config_info['description']}")

        print("\n💡 配置方法:")
        print("1. 访问 https://mp.weixin.qq.com/ 获取微信小程序AppID和AppSecret")
        print("2. 在.env文件中添加这些配置")

        # 生成JWT密钥
        if "JWT_SECRET_KEY" in [c[0] for c in missing_configs]:
            import secrets
            jwt_key = secrets.token_urlsafe(32)
            print(f"\n🔑 建议的JWT密钥: {jwt_key}")

        return False
    else:
        print("✅ 环境变量配置完整")
        return True


def run_database_migration():
    """运行数据库迁移"""
    print("\n🗄️  运行数据库迁移...")

    try:
        import sqlite3
        from packages.agent_fishing.tools.lure.database import get_db
        from packages.agent_fishing.tools.lure.migrations import DatabaseMigrations
        from packages.agent_fishing.tools.lure.migrations_wechat import run_wechat_migrations

        # 获取数据库路径
        db_path = get_db().get_database_path()
        print(f"数据库路径: {db_path}")

        # 连接数据库
        conn = sqlite3.connect(db_path)

        try:
            # 运行常规迁移
            print("运行基础数据库迁移...")
            migrations = DatabaseMigrations(conn)
            migrations.run_all_migrations()

            # 运行微信登录迁移
            print("运行微信登录迁移...")
            run_wechat_migrations(conn)

            conn.commit()
            print("✅ 数据库迁移完成")
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def setup_miniprogram_config():
    """配置小程序"""
    print("\n📱 配置小程序...")

    manifest_path = project_root / "fishing_agent_app" / "fishing_agent" / "manifest.json"

    if not manifest_path.exists():
        print(f"❌ 找不到小程序配置文件: {manifest_path}")
        return False

    # 读取manifest.json
    import json
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    current_appid = manifest.get("mp-weixin", {}).get("appid", "")

    if current_appid == "请在此处填写微信小程序AppID" or not current_appid:
        print("⚠️  请在manifest.json中配置微信小程序AppID")
        print(f"文件路径: {manifest_path}")
        print("请将 mp-weixin.appid 设置为你的小程序AppID")
        return False
    else:
        print(f"✅ 小程序AppID已配置: {current_appid}")
        return True


def test_api_server():
    """测试API服务器"""
    print("\n🌐 测试API服务器连接...")

    try:
        import httpx
        import asyncio

        async def test_connection():
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get("http://localhost:8000/health")
                    if response.status_code == 200:
                        print("✅ API服务器运行正常")
                        return True
                    else:
                        print(f"❌ API服务器返回状态码: {response.status_code}")
                        return False
            except httpx.ConnectError:
                print("❌ 无法连接到API服务器")
                print("💡 请启动API服务器: uv run uvicorn apps.api.main:app --reload")
                return False
            except Exception as e:
                print(f"❌ 连接测试失败: {e}")
                return False

        return asyncio.run(test_connection())

    except ImportError:
        print("⚠️  无法导入httpx进行连接测试，请手动验证API服务器是否运行")
        return None


def print_summary(success):
    """打印配置总结"""
    print("\n" + "="*60)
    if success:
        print("🎉 微信登录功能配置完成！")
    else:
        print("⚠️  配置未完成，请解决上述问题后重试")
    print("="*60)

    print("\n📋 后续步骤:")
    print("1. 启动API服务器: uv run uvicorn apps.api.main:app --reload")
    print("2. 在微信开发者工具中打开小程序项目")
    print("3. 配置微信开发者工具的网络设置（如需要）")
    print("4. 测试微信登录功能")

    print("\n📖 相关文档:")
    print("- 微信登录使用指南: docs/wechat_login_guide.md")
    print("- 测试脚本: scripts/test_wechat_login.py")

    if not success:
        print("\n🆘 获取帮助:")
        print("1. 查看使用指南获取详细配置说明")
        print("2. 运行测试脚本进行诊断")
        print("3. 检查环境变量配置是否正确")


def main():
    """主函数"""
    print_banner()

    # 检查Python版本
    if not check_python_version():
        return

    # 安装依赖
    install_dependencies()

    # 配置环境变量
    env_ok = setup_env_file()

    # 运行数据库迁移
    if env_ok:
        migration_ok = run_database_migration()
    else:
        migration_ok = False

    # 配置小程序
    miniprogram_ok = setup_miniprogram_config()

    # 测试API服务器
    api_ok = test_api_server()

    # 总体结果
    success = all([
        env_ok,
        migration_ok,
        miniprogram_ok,
        api_ok is not False  # None表示无法测试，不算失败
    ])

    print_summary(success)


if __name__ == "__main__":
    main()