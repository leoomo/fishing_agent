#!/usr/bin/env python3
"""
简化缓存系统

替代复杂的分层缓存，提供简单高效的内存缓存功能。
支持TTL过期和基本的缓存管理。
"""

import json
import os
import time
from typing import Any, Dict, Optional, Union
from pathlib import Path


class SimpleCache:
    """简化的缓存系统，替代复杂的多层缓存架构"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化简化缓存

        Args:
            cache_dir: 可选的持久化缓存目录
        """
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_dir = None

        if cache_dir:
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_file_cache()

    def _load_file_cache(self):
        """从文件加载缓存（如果指定了cache_dir）"""
        if not self.cache_dir:
            return

        cache_file = self.cache_dir / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 过滤已过期的缓存项
                    current_time = time.time()
                    for key, value in data.items():
                        if value.get('expires_at', current_time + 1) > current_time:
                            self._memory_cache[key] = value
            except Exception as e:
                # 缓存文件损坏时忽略
                pass

    def _save_file_cache(self):
        """保存缓存到文件（如果指定了cache_dir）"""
        if not self.cache_dir:
            return

        try:
            cache_file = self.cache_dir / "cache.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._memory_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            # 忽略文件保存错误，不影响缓存功能
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        if key in self._memory_cache:
            cache_item = self._memory_cache[key]
            if cache_item.get('expires_at', time.time() + 1) > time.time():
                return cache_item['value']
            else:
                # 过期了，删除
                del self._memory_cache[key]

        return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示永不过期
        """
        expires_at = None
        if ttl is not None:
            expires_at = time.time() + ttl

        self._memory_cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }

        # 如果启用了文件缓存，立即保存
        if self.cache_dir:
            self._save_file_cache()

    def delete(self, key: str) -> bool:
        """
        删除缓存项

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        if key in self._memory_cache:
            del self._memory_cache[key]
            if self.cache_dir:
                self._save_file_cache()
            return True
        return False

    def clear(self) -> None:
        """清空所有缓存"""
        self._memory_cache.clear()
        if self.cache_dir:
            cache_file = self.cache_dir / "cache.json"
            try:
                if cache_file.exists():
                    cache_file.unlink()
            except Exception:
                pass

    def cleanup_expired(self) -> int:
        """
        清理过期的缓存项

        Returns:
            清理的缓存项数量
        """
        current_time = time.time()
        expired_keys = []

        for key, value in self._memory_cache.items():
            if value.get('expires_at', current_time + 1) <= current_time:
                expired_keys.append(key)

        for key in expired_keys:
            del self._memory_cache[key]

        if expired_keys and self.cache_dir:
            self._save_file_cache()

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        current_time = time.time()
        valid_items = 0
        expired_items = 0

        for value in self._memory_cache.values():
            if value.get('expires_at', current_time + 1) > current_time:
                valid_items += 1
            else:
                expired_items += 1

        return {
            'total_items': len(self._memory_cache),
            'valid_items': valid_items,
            'expired_items': expired_items,
            'has_file_cache': self.cache_dir is not None
        }


# 全局缓存实例
_cache_file_dir = os.getenv('CACHE_DIR')
if _cache_file_dir:
    _cache_file_dir = Path(_cache_file_dir) / "fishing_agent_cache"
else:
    # 默认使用用户目录下的缓存
    _cache_file_dir = Path.home() / ".cache" / "fishing_agent"

# 创建全局缓存实例
cache = SimpleCache(str(_cache_file_dir))