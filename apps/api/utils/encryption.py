import os
from cryptography.fernet import Fernet

# 从环境变量读取加密密钥（如果不存在则生成）
ENCRYPTION_KEY = os.getenv('CONFIG_ENCRYPTION_KEY')

if not ENCRYPTION_KEY:
    # 生成新密钥（仅用于开发环境）
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"⚠️  警告: 未设置 CONFIG_ENCRYPTION_KEY，使用临时密钥: {ENCRYPTION_KEY}")
    print("   生产环境请设置环境变量: export CONFIG_ENCRYPTION_KEY=<your_key>")

cipher = Fernet(ENCRYPTION_KEY.encode())


def encrypt_value(value: str) -> str:
    """
    加密配置值

    Args:
        value: 明文字符串

    Returns:
        str: 加密后的字符串
    """
    return cipher.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    """
    解密配置值

    Args:
        encrypted_value: 加密字符串

    Returns:
        str: 明文字符串
    """
    return cipher.decrypt(encrypted_value.encode()).decode()
