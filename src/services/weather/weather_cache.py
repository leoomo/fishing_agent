#!/usr/bin/env python3
"""
天气数据缓存系统
支持内存缓存和文件持久化缓存
"""

import json
import time
import hashlib
import builtins
import inspect
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict


@dataclass
class CacheEntry:
    """缓存条目数据类"""
    key: str
    value: Any
    timestamp: float
    ttl: int  # 生存时间（秒）
    access_count: int = 0
    last_access: float = 0.0

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > (self.timestamp + self.ttl)

    def update_access(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_access = time.time()


class LRUCache:
    """简单的LRU缓存实现"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                return None
            entry.update_access()
            # 移动到末尾（最近使用）
            self.cache.move_to_end(key)
            return entry.value
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        # 如果缓存已满，删除最久未使用的条目
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl
        )
        entry.update_access()

        self.cache[key] = entry
        self.cache.move_to_end(key)

    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self):
        """清空缓存"""
        self.cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)

    def cleanup_expired(self) -> int:
        """清理过期条目，返回清理数量"""
        expired_keys = []
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.cache:
            return {
                "size": 0,
                "hit_rate": 0.0,
                "total_accesses": 0,
                "expired_entries": 0
            }

        total_accesses = sum(entry.access_count for entry in self.cache.values())
        expired_count = sum(1 for entry in self.cache.values() if entry.is_expired())

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_accesses": total_accesses,
            "expired_entries": expired_count,
            "oldest_entry": min(entry.timestamp for entry in self.cache.values()) if self.cache else 0,
            "newest_entry": max(entry.timestamp for entry in self.cache.values()) if self.cache else 0
        }


class WeatherCache:
    """天气数据缓存系统"""

    def __init__(self,
                 memory_size: int = 1000,
                 file_path: str = "src/data/cache/weather_cache.json",
                 default_ttl: int = 3600):
        """
        初始化缓存系统

        Args:
            memory_size: 内存缓存最大条目数
            file_path: 文件缓存路径
            default_ttl: 默认TTL（秒）
        """
        self.memory_cache = LRUCache(memory_size)
        self.file_path = Path(file_path)
        self.default_ttl = default_ttl
        self.file_cache: Dict[str, CacheEntry] = {}

        # 确保缓存目录存在
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # 加载文件缓存
        self._load_file_cache()

    def _load_file_cache(self):
        """从文件加载缓存"""
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r', encoding='utf-8') as cache_file:
                    data = json.load(cache_file)

                for key, entry_data in data.items():
                    # 反序列化value字段
                    if 'value' in entry_data:
                        entry_data['value'] = self._deserialize_value(entry_data['value'])

                    entry = CacheEntry(**entry_data)
                    if not entry.is_expired():
                        self.file_cache[key] = entry

                print(f"📁 从文件加载了 {len(self.file_cache)} 条缓存记录")

        except Exception as e:
            print(f"⚠️ 加载文件缓存失败: {e}")
            self.file_cache = {}

    def _serialize_value(self, value):
        """序列化值，处理特殊类型"""
        if isinstance(value, datetime):
            return {"__datetime__": True, "value": value.isoformat()}
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return value

    def _deserialize_value(self, value):
        """反序列化值，处理特殊类型"""
        if isinstance(value, dict) and value.get("__datetime__"):
            # 反序列化datetime对象
            try:
                return datetime.fromisoformat(value["value"])
            except:
                return value
        elif isinstance(value, list):
            return [self._deserialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._deserialize_value(v) for k, v in value.items()}
        else:
            return value

    def _save_file_cache(self):
        """保存缓存到文件"""
        try:
            # 清理过期条目
            self._cleanup_file_cache()

            # 只保存未过期的条目
            data_to_save = {}
            failed_entries = []

            for key, entry in self.file_cache.items():
                if not entry.is_expired():
                    try:
                        # 序列化value字段以处理datetime等特殊类型
                        serialized_value = self._serialize_value(entry.value)

                        entry_dict = {
                            'key': entry.key,
                            'value': serialized_value,
                            'timestamp': entry.timestamp,
                            'ttl': entry.ttl,
                            'access_count': entry.access_count,
                            'last_access': entry.last_access
                        }

                        data_to_save[key] = entry_dict
                    except Exception as e:
                        failed_entries.append((key, str(e)))
                        print(f"⚠️ 跳过无法序列化的缓存条目 {key}: {e}")

            # 使用绝对路径打开文件
            # 使用不同的变量名避免冲突
            with open(str(self.file_path), 'w', encoding='utf-8') as cache_file:
                json.dump(data_to_save, cache_file, ensure_ascii=False, indent=2)

            if failed_entries:
                print(f"⚠️ 有 {len(failed_entries)} 个缓存条目因序列化问题被跳过")
            else:
                print(f"✅ 成功保存 {len(data_to_save)} 个缓存条目到文件")

        except Exception as e:
            import traceback
            import inspect

            # 获取调用栈信息
            caller_info = "未知方法"
            try:
                # 获取调用栈
                stack = inspect.stack()
                for frame_info in stack:
                    # 跳过当前方法和内部调用
                    if frame_info.function not in ['_save_file_cache', 'save', 'set']:
                        caller_info = f"{frame_info.function} ({frame_info.filename}:{frame_info.lineno})"
                        break
            except:
                pass

            print(f"⚠️ 保存文件缓存失败: {e}")
            print(f"🔍 触发方法: {caller_info}")
            print(f"📋 详细错误: {traceback.format_exc()}")

    def _cleanup_file_cache(self):
        """清理文件缓存中的过期条目"""
        expired_keys = []
        for key, entry in self.file_cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            del self.file_cache[key]

    def _generate_key(self, place_name: str, extra_params: Optional[Dict[str, Any]] = None) -> str:
        """生成缓存键"""
        key_data = {"place": place_name}
        if extra_params:
            key_data.update(extra_params)

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def get(self, place_name: str, extra_params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        获取缓存数据

        Args:
            place_name: 地名
            extra_params: 额外参数

        Returns:
            缓存的数据或None
        """
        key = self._generate_key(place_name, extra_params)

        # 1. 检查内存缓存
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # 2. 检查文件缓存
        if key in self.file_cache:
            entry = self.file_cache[key]
            if not entry.is_expired():
                entry.update_access()
                # 将数据加载到内存缓存
                self.memory_cache.set(key, entry.value, entry.ttl)
                return entry.value
            else:
                # 删除过期条目
                del self.file_cache[key]
                self._save_file_cache()

        return None

    def set(self,
            place_name: str,
            value: Any,
            ttl: Optional[int] = None,
            extra_params: Optional[Dict[str, Any]] = None):
        """
        设置缓存数据

        Args:
            place_name: 地名
            value: 要缓存的数据
            ttl: 生存时间（秒）
            extra_params: 额外参数
        """
        if ttl is None:
            ttl = self.default_ttl

        key = self._generate_key(place_name, extra_params)

        # 设置内存缓存
        self.memory_cache.set(key, value, ttl)

        # 设置文件缓存
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl
        )
        entry.update_access()

        self.file_cache[key] = entry

        # 异步保存到文件（避免频繁IO）
        if len(self.file_cache) % 10 == 0:  # 每10次修改保存一次
            self._save_file_cache()

    def delete(self, place_name: str, extra_params: Optional[Dict[str, Any]] = None) -> bool:
        """删除缓存条目"""
        key = self._generate_key(place_name, extra_params)

        memory_deleted = self.memory_cache.delete(key)
        file_deleted = False

        if key in self.file_cache:
            del self.file_cache[key]
            file_deleted = True
            self._save_file_cache()

        return memory_deleted or file_deleted

    def clear(self):
        """清空所有缓存"""
        self.memory_cache.clear()
        self.file_cache.clear()

        # 删除缓存文件
        if self.file_path.exists():
            self.file_path.unlink()

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        memory_cleaned = self.memory_cache.cleanup_expired()
        file_cleaned = len([k for k, v in self.file_cache.items() if v.is_expired()])

        # 清理文件缓存中的过期条目
        self._cleanup_file_cache()
        self._save_file_cache()

        return memory_cleaned + file_cleaned

    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        memory_stats = self.memory_cache.get_statistics()
        file_stats = {
            "size": len(self.file_cache),
            "expired_entries": len([k for k, v in self.file_cache.items() if v.is_expired()])
        }

        # 计算总缓存命中率（简化计算）
        total_memory_accesses = memory_stats.get("total_accesses", 0)
        total_file_accesses = sum(entry.access_count for entry in self.file_cache.values())
        total_accesses = total_memory_accesses + total_file_accesses

        return {
            "memory_cache": memory_stats,
            "file_cache": file_stats,
            "total_entries": memory_stats["size"] + file_stats["size"],
            "total_accesses": total_accesses,
            "cache_file_path": str(self.file_path),
            "default_ttl": self.default_ttl
        }

    def save_to_file(self):
        """强制保存缓存到文件"""
        self._save_file_cache()

    def preload_cache(self, common_places: list):
        """预加载常用地点的缓存"""
        print(f"🔄 预加载 {len(common_places)} 个常用地点的缓存...")
        # 这里可以预加载一些常用地点的天气数据
        # 实际实现需要调用天气API获取数据
        pass


# 全局缓存实例
_weather_cache = None

def get_weather_cache() -> WeatherCache:
    """获取全局天气缓存实例"""
    global _weather_cache
    if _weather_cache is None:
        _weather_cache = WeatherCache()
    return _weather_cache


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试 WeatherCache")
    print("=" * 50)

    # 创建缓存实例
    cache = WeatherCache(memory_size=5, default_ttl=2)  # 2秒TTL用于测试

    # 测试基本操作
    print("📝 测试基本缓存操作:")

    # 设置缓存
    cache.set("北京", {"temperature": 25, "humidity": 60})
    cache.set("上海", {"temperature": 28, "humidity": 70})
    cache.set("广州", {"temperature": 32, "humidity": 80})

    # 获取缓存
    beijing_weather = cache.get("北京")
    print(f"   北京天气: {beijing_weather}")

    shanghai_weather = cache.get("上海")
    print(f"   上海天气: {shanghai_weather}")

    not_found = cache.get("不存在的城市")
    print(f"   不存在的城市: {not_found}")

    # 测试TTL过期
    print("\n⏰ 测试TTL过期:")
    print("   等待3秒...")
    time.sleep(3)

    beijing_weather_after = cache.get("北京")
    print(f"   3秒后北京天气: {beijing_weather_after}")

    # 测试LRU淘汰
    print("\n🔄 测试LRU淘汰:")
    cache.set("城市1", {"temp": 1})
    cache.set("城市2", {"temp": 2})
    cache.set("城市3", {"temp": 3})
    cache.set("城市4", {"temp": 4})
    cache.set("城市5", {"temp": 5})
    cache.set("城市6", {"temp": 6})  # 这应该淘汰城市1

    city1_weather = cache.get("城市1")
    city6_weather = cache.get("城市6")
    print(f"   城市1天气（应该被淘汰）: {city1_weather}")
    print(f"   城市6天气: {city6_weather}")

    # 获取统计信息
    print("\n📊 缓存统计信息:")
    stats = cache.get_statistics()
    for category, data in stats.items():
        if isinstance(data, dict):
            print(f"   {category}:")
            for key, value in data.items():
                print(f"     {key}: {value}")
        else:
            print(f"   {category}: {data}")

    # 清理测试
    print("\n🧹 清理测试:")
    cache.cleanup_expired()
    cache.clear()
    print("   缓存已清空")

    print("\n✅ 测试完成！")