#!/usr/bin/env python3
"""列出 Phase 4 新增的 API 端点"""
import requests
import json

response = requests.get("http://localhost:8000/openapi.json")
data = response.json()

print('🎯 Phase 4 API 端点清单')
print('='*60)
print()

# 爬虫管理
print('🕷️ 爬虫管理 API (Crawler)')
crawler_paths = {k:v for k,v in data['paths'].items() if '/crawler' in k}
for path, methods in sorted(crawler_paths.items()):
    for method, details in methods.items():
        if method != 'parameters':
            summary = details.get('summary', '')
            print(f'  {method.upper():6} {path:50} - {summary}')
print()

# 监控管理
print('📊 监控管理 API (Monitor)')
monitor_paths = {k:v for k,v in data['paths'].items() if '/monitor' in k}
for path, methods in sorted(monitor_paths.items()):
    for method, details in methods.items():
        if method != 'parameters':
            summary = details.get('summary', '')
            print(f'  {method.upper():6} {path:50} - {summary}')
print()

print('='*60)
print(f'✅ 爬虫管理: {len(crawler_paths)} 个端点')
print(f'✅ 监控管理: {len(monitor_paths)} 个端点')
print(f'✅ 总计新增: {len(crawler_paths) + len(monitor_paths)} 个端点')
print()
print('📚 完整文档: http://localhost:8000/docs')
print('📖 ReDoc文档: http://localhost:8000/redoc')
