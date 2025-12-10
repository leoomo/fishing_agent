#!/usr/bin/env python3
"""列出所有API端点"""
import requests
import json

response = requests.get("http://localhost:8000/openapi.json")
data = response.json()

print('🎯 Phase 3 核心管理模块 API 端点清单')
print('='*60)
print()

# 装备管理
print('📦 装备管理 API (Equipment Admin)')
equipment_paths = {k:v for k,v in data['paths'].items() if 'equipment' in k and '/admin' in k}
for path, methods in sorted(equipment_paths.items()):
    for method, details in methods.items():
        if method != 'parameters':
            print(f'  {method.upper():6} {path:45} - {details.get("summary", "")}')
print()

# 品牌管理
print('🏷️  品牌管理 API (Brand Admin)')
brand_paths = {k:v for k,v in data['paths'].items() if 'brands' in k}
for path, methods in sorted(brand_paths.items()):
    for method, details in methods.items():
        if method != 'parameters':
            print(f'  {method.upper():6} {path:45} - {details.get("summary", "")}')
print()

# 用户管理
print('👥 用户管理 API (User Admin)')
user_paths = {k:v for k,v in data['paths'].items() if '/users' in k and '/admin' in k}
for path, methods in sorted(user_paths.items()):
    for method, details in methods.items():
        if method != 'parameters':
            print(f'  {method.upper():6} {path:45} - {details.get("summary", "")}')
print()

# 导入导出
print('📥📤 导入导出 API (Import/Export)')
import_export_paths = {k:v for k,v in data['paths'].items() if 'import-export' in k}
for path, methods in sorted(import_export_paths.items()):
    for method, details in methods.items():
        if method != 'parameters':
            print(f'  {method.upper():6} {path:45} - {details.get("summary", "")}')
print()

print('='*60)
print(f'✅ 总计: {len([p for p in data["paths"] if "/admin" in p])} 个管理端点')
print()
print('📚 Swagger文档: http://localhost:8000/docs')
print('📖 ReDoc文档: http://localhost:8000/redoc')
