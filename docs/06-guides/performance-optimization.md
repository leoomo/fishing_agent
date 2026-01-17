# 性能优化指南 v5.1.0

智能钓鱼助手系统的性能优化策略和实践指南。

## 📋 目录

- [性能指标](#性能指标)
- [数据库优化](#数据库优化)
- [缓存策略](#缓存策略)
- [API性能](#api性能)
- [前端优化](#前端优化)
- [算法优化](#算法优化)
- [监控调优](#监控调优)
- [常见问题](#常见问题)

## 📊 性能指标

### 系统指标
- **API响应时间**: 目标 P95 < 500ms
- **并发处理能力**: 支持 1000+ 并发用户
- **系统可用性**: 99.9% SLA
- **错误率**: < 0.1%

### 业务指标
- **钓鱼推荐响应**: < 2秒
- **OCR处理速度**: 10张图片 < 30秒
- **装备导入效率**: 1000条记录 < 1分钟
- **用户查询速度**: 查询响应 < 1秒

## 🗄️ 数据库优化

### 查询优化

#### 1. 索引策略
```sql
-- 用户表索引
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_created_at ON users(created_at);

-- 装备表索引
CREATE INDEX idx_equipment_brand ON equipment(brand);
CREATE INDEX idx_equipment_category ON equipment(category);
CREATE INDEX idx_equipment_price ON equipment(price);
CREATE INDEX idx_equipment_created ON equipment(created_at);

-- 聊合索引
CREATE INDEX idx_equipment_brand_category ON equipment(brand, category);
CREATE INDEX idx_equipment_search ON equipment(brand, model, category);
```

#### 2. 查询优化示例
```python
# packages/agents/fishing/tools/lure/database.py
from sqlalchemy import text

# 优化前的查询
def get_equipment_slow(category: str, price_range: tuple):
    query = text(f"""
        SELECT * FROM equipment 
        WHERE category = '{category}'
        AND price BETWEEN {price_range[0]} AND {price_range[1]}
        ORDER BY created_at DESC
        LIMIT 50
    """)
    return db.execute(query).fetchall()

# 优化后的查询
def get_equipment_optimized(category: str, price_range: tuple, limit: int = 50):
    from packages.agents.fishing.tools.lure.database import Equipment
    
    query = Equipment.query.filter(
        Equipment.category == category,
        Equipment.price.between(price_range[0], price_range[1])
    ).order_by(Equipment.created_at.desc()).limit(limit)
    
    return query.all()
```

### 连接池优化
```python
# shared/config/database.py
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

# 创建连接池
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # 生产环境关闭SQL日志
)

# 连接池使用示例
with engine.connect() as conn:
    result = conn.execute("SELECT COUNT(*) FROM users")
    count = result.scalar()
```

### 数据库配置优化
```python
# PostgreSQL配置优化
config = {
    "shared_buffers": "256MB",
    "effective_cache_size": "1GB",
    "work_mem": "8MB",
    "maintenance_work_mem": "64MB",
    "checkpoint_completion_target": "0.9",
    "wal_buffers": "16MB",
    "default_statistics_target": 1000,
    "random_page_cost": "1.1",
    "effective_io_concurrency": "200"
}
```

## 🚀 缓存策略

### 多层缓存架构
```python
# shared/cache/cache_manager.py
from typing import Any, Optional
import time
import hashlib
import json
import redis
from functools import wraps

class CacheManager:
    def __init__(self):
        # L1: 应用内存缓存
        self.memory_cache = {}
        self.memory_cache_ttl = {}
        
        # L2: Redis分布式缓存
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # L3: 数据库缓存（通过查询缓存实现）
        
    def _generate_key(self, key: str) -> str:
        """生成缓存键"""
        return f"fishing_agent:{hashlib.md5(key.encode()).hexdigest()}"
    
    def get(self, key: str, level: int = 1) -> Optional[Any]:
        """获取缓存"""
        cache_key = self._generate_key(key)
        
        # L1: 内存缓存
        if level >= 1:
            if cache_key in self.memory_cache:
                cache_time = self.memory_cache_ttl.get(cache_key, 0)
                if time.time() - cache_time < 300:  # 5分钟TTL
                    return self.memory_cache[cache_key]
                else:
                    del self.memory_cache[cache_key]
                    del self.memory_cache_ttl[cache_key]
        
        # L2: Redis缓存
        if level >= 2:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                print(f"Redis缓存获取失败: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300, level: int = 1):
        """设置缓存"""
        cache_key = self._generate_key(key)
        
        # L1: 内存缓存
        if level >= 1:
            self.memory_cache[cache_key] = value
            self.memory_cache_ttl[cache_key] = time.time()
        
        # L2: Redis缓存
        if level >= 2:
            try:
                self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(value, default=str)
                )
            except Exception as e:
                print(f"Redis缓存设置失败: {e}")

# 全局缓存管理器
cache_manager = CacheManager()
```

### 缓存装饰器
```python
# shared/cache/decorators.py
from functools import wraps

def cache_result(ttl: int = 300, level: int = 1):
    """缓存结果装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key, level)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl, level)
            
            return result
        return wrapper
    return decorator

# 使用示例
@cache_result(ttl=600, level=2)  # 缓存10分钟，使用L2缓存
def get_weather_data(location: str, date: str):
    # 天气数据获取逻辑
    pass
```

### 智能缓存策略
```python
# packages/agents/fishing/core/cache.py
class SmartCache:
    def __init__(self):
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0
        }
    
    def get_with_fallback(self, key: str, fallback_func, ttl: int = 300):
        """带回退机制的缓存获取"""
        # 尝试从缓存获取
        result = cache_manager.get(key)
        if result is not None:
            self.cache_stats['hits'] += 1
            return result
        
        # 缓存未命中，执行回退函数
        self.cache_stats['misses'] += 1
        result = fallback_func()
        
        # 缓存结果
        if result is not None:
            cache_manager.set(key, result, ttl)
            self.cache_stats['sets'] += 1
        
        return result
    
    def get_cache_stats(self):
        """获取缓存统计"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        if total > 0:
            hit_rate = self.cache_stats['hits'] / total
        else:
            hit_rate = 0
        
        return {
            'hit_rate': hit_rate,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets']
        }
```

## 🌐 API性能

### FastAPI优化配置
```python
# apps/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

# 创建应用实例
app = FastAPI(
    title="智能钓鱼助手API",
    version="5.0.2",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 配置生产优化
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        access_log=True,
        use_colors=True,
        limit_concurrency=1000,
        limit_max_requests=10000,
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30
    )
```

### 异步处理优化
```python
# apps/api/services/async_service.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List

class AsyncProcessingService:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_equipment_batch(
        self, 
        equipment_data: List[dict]
    ) -> List[dict]:
        """异步批量处理装备数据"""
        loop = asyncio.get_event_loop()
        
        # 创建异步任务
        tasks = []
        for data in equipment_data:
            task = loop.run_in_executor(
                self.executor,
                self.process_single_equipment,
                data
            )
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 记录错误但不中断处理
                print(f"处理第{i+1}条数据失败: {result}")
                continue
            processed_results.append(result)
        
        return processed_results
    
    def process_single_equipment(self, data: dict) -> dict:
        """处理单个装备数据"""
        # 数据验证
        validated_data = self.validate_equipment(data)
        
        # 数据转换
        processed_data = self.transform_equipment(validated_data)
        
        # 数据保存
        saved_data = self.save_equipment(processed_data)
        
        return saved_data
```

### 响应优化
```python
# apps/api/middleware/response_middleware.py
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import json
import gzip
from io import BytesIO

class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 调用下一个中间件
        response = await call_next(request)
        
        # 压缩大响应
        if (len(response.body) > 1024 and 
            "gzip" not in request.headers.get("accept-encoding", "")):
            
            # 压缩响应体
            buffer = BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode="wb") as gz_file:
                gz_file.write(response.body)
            
            # 设置响应头
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = str(len(buffer.getvalue()))
            
            # 更新响应体
            response.body = buffer.getvalue()
        
        return response

# 添加到应用
app.add_middleware(ResponseCompressionMiddleware)
```

## 🎨 前端优化

### React性能优化
```typescript
// apps/web-admin/src/utils/performance.ts
import { useCallback, useMemo } from 'react';
import { debounce } from 'lodash-es';

// 防抖Hook
export const useDebounce = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
) => {
  const debouncedCallback = useCallback(
    debounce(callback, delay),
    [callback, delay]
  );
  
  return debouncedCallback;
};

// 记忆化Hook
export const useMemoWithCompare = <T>(
  factory: () => T,
  deps: React.DependencyList,
  compare?: (prev: T, next: T) => boolean
) => {
  const prevRef = React.useRef<T>();
  
  const memoizedValue = useMemo(() => {
    const nextValue = factory();
    
    // 自定义比较函数
    if (prevRef.current && compare) {
      if (compare(prevRef.current, nextValue)) {
        return prevRef.current;
      }
    }
    
    prevRef.current = nextValue;
    return nextValue;
  }, deps);
  
  return memoizedValue;
};

// 虚拟列表优化
export const useVirtualList = <T>(
  items: T[],
  itemHeight: number,
  containerHeight: number,
  overscan: number = 5
) => {
  const [scrollTop, setScrollTop] = React.useState(0);
  
  const visibleCount = Math.ceil(containerHeight / itemHeight);
  const totalCount = items.length;
  const startIndex = Math.max(
    0,
    Math.min(totalCount - visibleCount, Math.floor(scrollTop / itemHeight) - overscan)
  );
  
  const endIndex = Math.min(
    totalCount,
    startIndex + visibleCount + 2 * overscan
  );
  
  const visibleItems = items.slice(startIndex, endIndex);
  
  const totalHeight = items.length * itemHeight;
  
  return {
    visibleItems,
    startIndex,
    endIndex,
    totalHeight,
    onScroll: (e: React.UIEvent<HTMLDivElement>) => {
      setScrollTop(e.currentTarget.scrollTop);
    }
  };
};
```

### 图片懒加载
```typescript
// apps/web-admin/src/components/LazyImage.tsx
import React, { useState, useRef, useEffect } from 'react';

interface LazyImageProps {
  src: string;
  placeholder?: string;
  alt?: string;
  className?: string;
  style?: React.CSSProperties;
}

const LazyImage: React.FC<LazyImageProps> = ({
  src,
  placeholder = '/images/placeholder.png',
  alt = '',
  className = '',
  style = {}
}) => {
  const [loaded, setLoaded] = useState(false);
  const [inView, setInView] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
        }
      },
      {
        threshold: 0.1
      }
    );
    
    if (imgRef.current) {
      observer.observe(imgRef.current);
    }
    
    return () => observer.disconnect();
  }, []);
  
  useEffect(() => {
    if (inView && !loaded && imgRef.current) {
      imgRef.current.src = src;
      imgRef.current.onload = () => setLoaded(true);
    }
  }, [inView, loaded, src]);
  
  return (
    <img
      ref={imgRef}
      src={loaded ? src : placeholder}
      alt={alt}
      className={className}
      style={{
        transition: 'opacity 0.3s',
        opacity: loaded ? 1 : 0.7,
        ...style
      }}
    />
  );
};

export default LazyImage;
```

## 🔧 算法优化

### 动态Prompt优化
```python
# packages/agents/fishing/middleware/dynamic_prompt.py
from typing import Dict, List
import hashlib

class DynamicPromptManager:
    def __init__(self):
        self.prompt_cache = {}
        self.template_stats = {}
        
        # 预定义模板
        self.templates = {
            "fishing": {
                "base": "你是一个专业的钓鱼助手，基于天气、时间和地点为用户提供建议。",
                "rules": "请根据7因子评分系统给出建议：温度、天气、风力、气压、湿度、季节、月相。",
                "output": "格式：建议分为时间段、推荐钓点、装备建议、注意事项。"
            },
            "weather": {
                "base": "你是一个天气预报助手。",
                "rules": "提供准确的天气信息，包括温度、湿度、风力、气压等。",
                "output": "格式：实时天气、预报天气、钓鱼适宜度分析。"
            }
        }
    
    def get_optimized_prompt(self, query: str) -> str:
        """获取优化的Prompt"""
        # 生成查询哈希
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # 检查缓存
        if query_hash in self.prompt_cache:
            return self.prompt_cache[query_hash]
        
        # 智能选择模板
        template_type = self._select_template(query)
        template = self.templates[template_type]
        
        # 组装Prompt
        prompt = f"{template['base']}\n\n{template['rules']}\n\n{template['output']}\n\n用户问题：{query}"
        
        # 缓存结果
        if len(self.prompt_cache) < 1000:  # 限制缓存大小
            self.prompt_cache[query_hash] = prompt
        
        # 更新统计
        self.template_stats[template_type] = self.template_stats.get(template_type, 0) + 1
        
        return prompt
    
    def _select_template(self, query: str) -> str:
        """智能选择模板类型"""
        query_lower = query.lower()
        
        # 关键词匹配
        if any(keyword in query_lower for keyword in ["钓鱼", "钓点", "路亚", "拟饵"]):
            return "fishing"
        elif any(keyword in query_lower for keyword in ["天气", "温度", "下雨", "晴天"]):
            return "weather"
        else:
            return "fishing"  # 默认模板
    
    def get_template_stats(self) -> Dict[str, int]:
        """获取模板使用统计"""
        return self.template_stats.copy()
```

### 工具选择优化
```python
# packages/agents/fishing/core/tool_optimizer.py
import time
from typing import Dict, Any, List

class ToolUsageOptimizer:
    def __init__(self):
        self.tool_performance = {}
        self.tool_usage_count = {}
        
    def record_tool_usage(self, tool_name: str, execution_time: float, success: bool):
        """记录工具使用情况"""
        if tool_name not in self.tool_performance:
            self.tool_performance[tool_name] = {
                'total_time': 0,
                'success_count': 0,
                'total_count': 0,
                'avg_time': 0
            }
        
        perf = self.tool_performance[tool_name]
        perf['total_time'] += execution_time
        perf['total_count'] += 1
        
        if success:
            perf['success_count'] += 1
        
        perf['avg_time'] = perf['total_time'] / perf['total_count']
    
    def get_tool_ranking(self) -> List[str]:
        """获取工具性能排名"""
        # 计算性能分数
        tool_scores = {}
        for tool_name, perf in self.tool_performance.items():
            success_rate = perf['success_count'] / perf['total_count']
            avg_time = perf['avg_time']
            
            # 综合评分 (成功率权重0.7，时间权重0.3)
            score = (success_rate * 0.7) + (1 / (avg_time / 1000 + 1) * 0.3)
            tool_scores[tool_name] = score
        
        # 按分数排序
        return sorted(tool_scores.keys(), 
                     key=lambda x: tool_scores[x], 
                     reverse=True)
    
    def recommend_tool_selection(self, available_tools: List[str], 
                                max_tools: int = 5) -> List[str]:
        """推荐工具选择"""
        # 优先选择性能好的工具
        ranked_tools = self.get_tool_ranking()
        
        # 过滤可用工具
        filtered_tools = [
            tool for tool in ranked_tools 
            if tool in available_tools
        ]
        
        # 返前N个
        return filtered_tools[:max_tools]
```

## 📊 监控调优

### 性能监控
```python
# shared/monitoring/performance_monitor.py
import time
import psutil
import threading
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    response_time: float
    active_connections: int
    request_count: int
    error_count: int

class PerformanceMonitor:
    def __init__(self):
        self.metrics_history = []
        self.max_history = 1000
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: int = 60):
        """开始监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self._store_metrics(metrics)
                self._check_alerts(metrics)
                time.sleep(interval)
            except Exception as e:
                print(f"监控异常: {e}")
                time.sleep(interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # 系统指标
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 应用指标（这里需要从应用日志或监控系统获取）
        response_time = self._get_avg_response_time()
        active_connections = self._get_active_connections()
        request_count = self._get_request_count()
        error_count = self._get_error_count()
        
        return PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage=disk.percent,
            response_time=response_time,
            active_connections=active_connections,
            request_count=request_count,
            error_count=error_count
        )
    
    def _store_metrics(self, metrics: PerformanceMetrics):
        """存储指标"""
        self.metrics_history.append(metrics)
        
        # 限制历史记录数量
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """检查告警条件"""
        alerts = []
        
        # CPU使用率告警
        if metrics.cpu_percent > 80:
            alerts.append(f"CPU使用率过高: {metrics.cpu_percent:.1f}%")
        
        # 内存使用率告警
        if metrics.memory_percent > 85:
            alerts.append(f"内存使用率过高: {metrics.memory_percent:.1f}%")
        
        # 磁盘使用率告警
        if metrics.disk_usage > 90:
            alerts.append(f"磁盘使用率过高: {metrics.disk_usage:.1f}%")
        
        # 响应时间告警
        if metrics.response_time > 1000:
            alerts.append(f"响应时间过长: {metrics.response_time:.1f}ms")
        
        # 错误率告警
        if metrics.request_count > 0:
            error_rate = metrics.error_count / metrics.request_count
            if error_rate > 0.05:  # 5%错误率
                alerts.append(f"错误率过高: {error_rate:.1%}")
        
        if alerts:
            self._send_alerts(alerts)
    
    def _send_alerts(self, alerts: List[str]):
        """发送告警"""
        for alert in alerts:
            print(f"性能告警: {alert}")
            # 这里可以集成邮件、短信、Slack等告警通道
    
    # 以下方法需要根据实际应用实现
    def _get_avg_response_time(self) -> float:
        """获取平均响应时间"""
        # 从应用日志或监控系统获取
        return 0.0
    
    def _get_active_connections(self) -> int:
        """获取活跃连接数"""
        # 从应用状态获取
        return 0
    
    def _get_request_count(self) -> int:
        """获取请求数量"""
        # 从应用日志统计
        return 0
    
    def _get_error_count(self) -> int:
        """获取错误数量"""
        # 从应用日志统计
        return 0
```

### 日志分析
```python
# shared/monitoring/log_analyzer.py
import re
import json
from typing import Dict, List
from collections import defaultdict, Counter

class LogAnalyzer:
    def __init__(self):
        self.error_patterns = [
            r'ERROR',
            r'Exception',
            r'Failed',
            r'Timeout'
        ]
        
        self.warning_patterns = [
            r'WARNING',
            r'Deprecated',
            r'Performance'
        ]
    
    def analyze_logs(self, log_file: str) -> Dict:
        """分析日志文件"""
        analysis = {
            'total_lines': 0,
            'errors': [],
            'warnings': [],
            'performance_issues': [],
            'error_types': Counter(),
            'response_times': [],
            'peak_usage': []
        }
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                analysis['total_lines'] += 1
                
                # 错误检测
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.error_patterns):
                    error_info = self._parse_error(line)
                    analysis['errors'].append(error_info)
                    analysis['error_types'][error_info['type']] += 1
                
                # 警告检测
                elif any(re.search(pattern, line, re.IGNORECASE) for pattern in self.warning_patterns):
                    warning_info = self._parse_warning(line)
                    analysis['warnings'].append(warning_info)
                
                # 性能问题检测
                elif 'response_time' in line:
                    response_time = self._extract_response_time(line)
                    if response_time:
                        analysis['response_times'].append(response_time)
        
        return analysis
    
    def _parse_error(self, line: str) -> Dict:
        """解析错误信息"""
        # 提取时间戳
        timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
        timestamp = timestamp_match.group(0) if timestamp_match else ""
        
        # 提取错误类型
        error_type = "Unknown"
        if 'Exception' in line:
            error_type = "Exception"
        elif 'Timeout' in line:
            error_type = "Timeout"
        elif 'Failed' in line:
            error_type = "Failed"
        
        # 提取错误消息
        message_match = re.search(r'(ERROR|Exception|Failed|Timeout)\s*[:：]?\s*(.+)', line)
        message = message_match.group(1) if message_match else line.strip()
        
        return {
            'timestamp': timestamp,
            'type': error_type,
            'message': message,
            'line': line.strip()
        }
    
    def _parse_warning(self, line: str) -> Dict:
        """解析警告信息"""
        return {
            'timestamp': "",
            'type': "Warning",
            'message': line.strip()
        }
    
    def _extract_response_time(self, line: str) -> float:
        """提取响应时间"""
        match = re.search(r'response_time[:=]\s*(\d+\.?\d*)', line)
        if match:
            return float(match.group(1))
        return 0.0
    
    def get_performance_report(self, analysis: Dict) -> str:
        """生成性能报告"""
        report = f"""
# 性能分析报告
## 基本统计
- 总日志行数: {analysis['total_lines']}
- 错误数量: {len(analysis['errors'])}
- 警告数量: {len(analysis['warnings'])}
- 响应时间样本: {len(analysis['response_times'])}

## 错误分析
"""
        
        # 错误类型分布
        if analysis['error_types']:
            report += "### 错误类型分布\n"
            for error_type, count in analysis['error_types'].most_common():
                report += f"- {error_type}: {count}\n"
        
        # 响应时间分析
        if analysis['response_times']:
            avg_time = sum(analysis['response_times']) / len(analysis['response_times'])
            max_time = max(analysis['response_times'])
            p95_time = sorted(analysis['response_times'])[int(len(analysis['response_times']) * 0.95)]
            
            report += f"""
### 响应时间分析
- 平均响应时间: {avg_time:.2f}ms
- 最大响应时间: {max_time:.2f}ms
- P95响应时间: {p95_time:.2f}ms
"""
        
        return report
```

## ❓ 常见问题

### Q: 数据库查询慢怎么办？

**A**: 
1. 添加合适的索引
2. 使用查询优化
3. 考虑读写分离
4. 启用查询缓存

### Q: API响应慢怎么办？

**A**: 
1. 启用异步处理
2. 优化序列化
3. 压缩大响应
4. 使用CDN加速

### Q: 内存占用过高怎么办？

**A**: 
1. 检查内存泄漏
2. 优化数据结构
3. 使用流式处理
4. 调整缓存大小

### Q: 并发处理能力不足？

**A**: 
1. 增加工作进程
2. 优化数据库连接池
3. 使用消息队列
4. 实施限流策略

---

**指南版本**: v5.1.0
**最后更新**: 2025-01-16
**相关技术**: FastAPI、React、PostgreSQL、Redis