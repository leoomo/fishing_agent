#!/usr/bin/env python3
"""
测试微信登录功能
"""

import asyncio
import httpx
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.api.main")

# 加载.env文件
from dotenv import load_dotenv
load_dotenv()


async def test_wechat_login():
    """测试微信登录API"""

    # API基础URL
    base_url = "http://localhost:8000"

    # 模拟微信登录数据
    test_data = {
        "code": "031Kc1002CqHL31hR0002VvLTK3Kc10g",  # 这需要是一个真实的微信code
        "nickname": "测试用户",
        "avatar_url": "https://thirdwx.qlogo.cn/mmopen/vi_32/test.jpg",
        "gender": 1,
        "city": "深圳",
        "province": "广东",
        "country": "中国",
        "language": "zh_CN"
    }

    async with httpx.AsyncClient() as client:
        print("🧪 测试微信登录API...")

        try:
            # 1. 获取微信配置
            print("\n1️⃣ 获取微信配置...")
            response = await client.get(f"{base_url}/api/v1/auth/wechat/config")

            if response.status_code == 200:
                config_data = response.json()
                print(f"✅ 微信配置获取成功: {json.dumps(config_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 获取微信配置失败: {response.status_code} - {response.text}")
                return

            # 2. 测试微信登录（需要真实的微信code）
            print("\n2️⃣ 测试微信登录...")
            print("⚠️  注意：这需要一个真实的微信登录code，测试可能会失败")

            response = await client.post(
                f"{base_url}/api/v1/auth/wechat/login",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                login_data = response.json()
                print(f"✅ 微信登录成功:")
                print(f"   - Token类型: {login_data.get('token_type')}")
                print(f"   - 用户ID: {login_data.get('user', {}).get('user_id')}")
                print(f"   - 用户名: {login_data.get('user', {}).get('username')}")
                print(f"   - 角色: {login_data.get('user', {}).get('role')}")
                print(f"   - 登录类型: {login_data.get('user', {}).get('login_type')}")

                # 3. 测试使用token访问受保护的API
                print("\n3️⃣ 测试使用Token访问受保护API...")
                token = login_data.get("access_token")
                if token:
                    headers = {"Authorization": f"Bearer {token}"}
                    response = await client.get(
                        f"{base_url}/api/v1/auth/me",
                        headers=headers
                    )

                    if response.status_code == 200:
                        user_data = response.json()
                        print(f"✅ Token验证成功: 当前用户 - {user_data.get('user', {}).get('username')}")
                    else:
                        print(f"❌ Token验证失败: {response.status_code} - {response.text}")
                else:
                    print("❌ 未获取到access_token")
            else:
                error_data = response.json()
                print(f"❌ 微信登录失败: {response.status_code}")
                print(f"   错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")

                # 检查是否是配置错误
                if "配置缺失" in error_data.get("detail", ""):
                    print("\n💡 解决方案:")
                    print("   1. 在.env文件中配置WECHAT_APPID")
                    print("   2. 在.env文件中配置WECHAT_SECRET")
                    print("   3. 重启API服务器")
                elif "微信登录失败" in error_data.get("detail", ""):
                    print("\n💡 可能的原因:")
                    print("   1. 使用了无效的微信code（需要从微信小程序获取）")
                    print("   2. 微信AppID或AppSecret配置错误")
                    print("   3. 网络连接问题")

        except httpx.ConnectError:
            print("❌ 无法连接到API服务器")
            print("💡 请确保API服务器正在运行: uv run uvicorn apps.api.main:app --reload")
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")

    required_vars = {
        "WECHAT_APPID": "微信小程序AppID",
        "WECHAT_SECRET": "微信小程序AppSecret",
        "JWT_SECRET_KEY": "JWT密钥"
    }

    all_configured = True
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            if var == "WECHAT_SECRET":
                print(f"✅ {desc}: {'*' * 10}...{value[-4:]}")
            else:
                print(f"✅ {desc}: {value}")
        else:
            print(f"❌ {desc}: 未配置")
            all_configured = False

    if not all_configured:
        print("\n⚠️  请在.env文件中配置缺失的环境变量")
        return False

    return True


def run_database_migration():
    """运行数据库迁移"""
    print("\n🗄️  运行数据库迁移...")

    try:
        import sqlite3
        from packages.agent_fishing.tools.lure.migrations_wechat import run_wechat_migrations
        from packages.agent_fishing.tools.lure.database import get_db

        # 获取数据库连接
        db_path = get_db().get_database_path()
        print(f"数据库路径: {db_path}")

        conn = sqlite3.connect(db_path)
        run_wechat_migrations(conn)
        conn.close()

        print("✅ 数据库迁移完成")
        return True

    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("="*60)
    print("📱 微信登录功能测试")
    print("="*60)

    # 1. 检查环境配置
    if not check_environment():
        return

    # 2. 运行数据库迁移
    if not run_database_migration():
        return

    # 3. 测试API
    await test_wechat_login()

    print("\n" + "="*60)
    print("🎉 测试完成!")
    print("="*60)

    print("\n📋 后续步骤:")
    print("1. 在微信公众平台配置小程序AppID和AppSecret")
    print("2. 在微信开发者工具中测试小程序登录")
    print("3. 确保服务器域名已添加到微信小程序服务器域名配置")


if __name__ == "__main__":
    asyncio.run(main())