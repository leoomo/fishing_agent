# 基础功能指南 v5.0.2

本指南将帮助您深入了解和使用智能钓鱼助手 v5.0.2 的各种核心功能。

## 📋 目录

- [基础使用](#基础使用)
- [钓鱼推荐功能](#钓鱼推荐功能)
- [路亚装备管理](#路亚装备管理)
- [装备信息提取与导入](#装备信息提取与导入)
- [图片处理与OCR识别](#图片处理与ocr识别)
- [微信小程序使用](#微信小程序使用)
- [API 使用示例](#api-使用示例)
- [高级功能](#高级功能)
- [爬虫与工作流管理](#爬虫与工作流管理)
- [最佳实践](#最佳实践)

## 🎣 基础使用

### 1. 时间查询

支持多种时间表达方式：

```python
# 相对时间
agent.run("今天钓鱼怎么样？")
agent.run("明天杭州钓鱼条件如何？")
agent.run("这个周末适合钓鱼吗？")

# 绝对时间
agent.run("2024年12月25日钓鱼怎么样？")

# 时间段
agent.run("明天上午适合钓鱼吗？")
agent.run("后天晚上去钓鱼可以吗？")
```

### 2. 地点查询

支持全国所有城市和地区：

```python
# 城市级别
agent.run("北京哪里适合钓鱼？")
agent.run("武汉东湖钓鱼条件怎么样？")

# 具体地点
agent.run("杭州西湖现在天气如何？能钓鱼吗？")

# 坐标查询（高级功能）
from packages.agents.fishing.utils import get_coordinates
coords = get_coordinates("北京")
print(f"北京坐标: {coords}")
```

### 3. 天气查询

获取详细的天气信息：

```python
from packages.agents.fishing.tools import get_weather

# 获取当前天气
weather = get_weather("北京", "today")
print(f"天气: {weather}")

# 获取钓鱼评分
from packages.agents.fishing.tools import query_fishing_recommendation
recommendation = query_fishing_recommendation("北京", "明天")
print(f"钓鱼推荐: {recommendation}")
```

## 🌟 钓鱼推荐功能

### 核心功能特点

1. **7因子科学评分系统**
   - 温度：考虑体感温度和水温对鱼情的影响
   - 天气：晴雨、云量对鱼类活动的影响
   - 风力：风力等级对水层和溶氧量的影响
   - 气压：气压变化对鱼类觅食的影响
   - 湿度：空气湿度对舒适度的影响
   - 季节：不同季节鱼类习性变化
   - 月相：月相对潮汐和鱼类活动的影响

2. **智能时间段分析**
   ```python
   # 系统自动识别时间段并给出建议
   agent.run("明天早上6点到9点北京钓鱼条件如何？")
   agent.run("周末下午去海边钓鱼怎么样？")
   ```

3. **个性化推荐**
   ```python
   # 根据用户偏好推荐
   agent.run("我喜欢钓鲤鱼，明天北京哪里适合？")
   agent.run("新手入门，推荐适合的钓鱼地点和装备")
   ```

## 🎯 路亚装备管理

### 装备数据库功能

系统内置完整的路亚装备数据库，支持：

1. **装备查询**
   ```python
   # 查询特定品牌装备
   agent.run("光威有哪些性价比高的路亚竿？")
   agent.run("达亿瓦纺车轮3000型有什么特点？")
   
   # 按需求查询
   agent.run("适合新手入门的路亚装备推荐")
   agent.run("预算1000元以内的高端装备推荐")
   ```

2. **装备对比**
   ```python
   # 对比不同装备
   agent.run("光威赤刃和达亿瓦路亚竿哪个好？")
   agent.run("纺车轮和水滴轮的区别和选择建议")
   ```

3. **装备搭配**
   ```python
   # 智能装备搭配
   agent.run("钓鲈鱼需要准备什么装备？")
   agent.run("路亚新手装备套装推荐")
   ```

### 装备管理界面

在Web管理界面中，您可以：

- 查看装备图片和详细参数
- 添加个人装备到收藏
- 创建装备搭配方案
- 分享装备使用心得

## 🔍 装备信息提取与导入

### 智能文本提取

系统能够从各种文本中提取装备信息：

```python
from packages.agents.equipment_import import EquipmentImportAgent

# 创建导入Agent
agent = EquipmentImportAgent(model_provider="zhipu")

# 从电商描述提取
text = """
光威赤刃 GT602L-M 路亚竿，碳纤维材质，超轻硬设计，
适合淡水作钓，长度2.4米，自重120g，售价299元。
"""

result = agent.extract_and_save(text=text, source_type="ecommerce")
print(f"提取结果: {result}")
```

### 批量处理功能

支持从多个来源批量导入装备信息：

1. **论坛帖子提取**
2. **电商商品描述**
3. **装备评测文章**
4. **用户分享内容**

## 📸 图片处理与OCR识别

### 智能OCR功能

系统支持多种OCR提供商：

1. **本地OCR（Ollama）**
   ```python
   from packages.data_processing.ocr import OCRMergeProcessor
   
   processor = OCRMergeProcessor(provider="ollama")
   result = processor.recognize_table(["equipment_image1.jpg", "equipment_image2.jpg"])
   ```

2. **云端OCR（SiliconFlow）**
   ```python
   processor = OCRMergeProcessor(provider="siliconflow")
   result = processor.recognize_table(["equipment_table.jpg"])
   ```

### 智能图片合并

系统能够自动检测和合并相关的图片：

```python
from packages.data_processing.image import BatchMergeProcessor

processor = BatchMergeProcessor(source_dir="./images")
merged_results = processor.process()

# 自动识别装备表格、参数列表等
# 支持批量处理多张相关图片
```

## 📱 微信小程序使用

### 小程序特色功能

1. **一键登录**
   - 使用微信账号快速登录
   - 自动保存用户偏好和历史记录

2. **语音输入**
   - 支持语音转文字输入
   - 方便户外使用

3. **位置服务**
   - 自动获取当前位置
   - 提供周边钓鱼地点推荐

4. **推送通知**
   - 天气变化提醒
   - 最佳钓鱼时间推送

### 小程序使用界面

```
底部导航栏：
├── 首页     - 智能对话和推荐
├── 发现     - 钓鱼地点和攻略
├── 装备     - 装备管理和推荐
├── 我的     - 个人中心和设置
```

## 🔌 API 使用示例

### 认证接口

```python
import requests

# 微信登录
response = requests.post("http://localhost:8000/api/v1/auth/wechat/login", json={
    "code": "wx_code"
})

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
```

### 核心功能接口

```python
# 钓鱼推荐接口
response = requests.post("http://localhost:8000/api/v1/fishing/chat", 
                        headers=headers, json={
    "query": "明天北京钓鱼怎么样？",
    "model_provider": "zhipu"
})

# 装备提取接口
response = requests.post("http://localhost:8000/api/v1/equipment/import/extract",
                        headers=headers, json={
    "text": "光威赤刃路亚竿，价格299元",
    "source_type": "forum"
})

# OCR识别接口
with open("equipment.jpg", "rb") as f:
    response = requests.post("http://localhost:8000/api/v1/ocr/recognize-table",
                            headers=headers, files={"files": f})
```

## 🚀 高级功能

### 1. 数据分析

系统能够分析用户的钓鱼数据：

```python
# 获取个人钓鱼统计
response = requests.get("http://localhost:8000/api/v1/analytics/personal/stats",
                        headers=headers)

# 获取装备使用统计
response = requests.get("http://localhost:8000/api/v1/analytics/equipment/usage",
                        headers=headers)
```

### 2. 智能提醒

基于用户习惯的智能提醒：

- 天气变化提醒
- 最佳钓鱼时间推送
- 装备保养提醒
- 新装备推荐通知

### 3. 社交功能

与其他钓友分享交流：

- 分享钓鱼成果
- 交流装备心得
- 组织钓鱼活动
- 点评钓点信息

## 🕷️ 爬虫与工作流管理

### 装备信息爬取

系统支持自动从各大平台获取装备信息：

```python
from packages.scraper.spiders import TaobaoSpider, JDSpider

# 创建爬虫实例
spider = TaobaoSpider()

# 爬取装备信息
results = spider.crawl(keywords=["路亚竿", "纺车轮"])
```

### 工作流管理

支持复杂的自动化工作流：

1. **装备信息更新工作流**
   - 定期爬取最新装备信息
   - 自动更新装备数据库
   - 通知用户新装备上架

2. **价格监控工作流**
   - 监控目标装备价格变化
   - 价格下降时推送通知
   - 生成价格趋势分析

## 💡 最佳实践

### 提问技巧

1. **描述具体需求**
   ```
   ✅ 好的提问：明天早上6-8点北京朝阳区适合钓什么鱼？
   ❌ 一般的提问：明天钓鱼怎么样？
   ```

2. **提供背景信息**
   ```
   ✅ 好的提问：我是新手，有光威赤刃路亚竿，想在北京钓鲈鱼，求推荐地点和技巧
   ❌ 一般的提问：推荐钓点
   ```

3. **分步骤提问**
   ```
   第一步：北京明天天气如何？
   第二步：适合钓什么鱼？
   第三步：需要什么装备？
   第四步：有什么技巧建议？
   ```

### 数据管理建议

1. **定期更新个人装备信息**
2. **记录钓鱼日志和成果**
3. **关注装备价格变化**
4. **参与社区讨论和分享**

### 安全注意事项

1. **天气安全**
   - 恶劣天气避免作钓
   - 注意雷电防护
   - 关注水位变化

2. **装备保养**
   - 定期检查装备状态
   - 及时更换老化部件
   - 妥善存放避免损坏

3. **环保钓鱼**
   - 遵守钓场规定
   - 保护水资源环境
   - 合理放生保持生态

## ❓ 常见问题

### Q: 如何提高推荐的准确性？

A: 
1. 提供更具体的时间和地点信息
2. 说明您的钓鱼偏好和目标鱼种
3. 分享您的实际钓鱼反馈

### Q: 装备推荐是否可靠？

A: 
1. 基于大量用户实际使用数据
2. 结合专业钓友的经验总结
3. 定期更新装备信息和价格

### Q: 天气数据多久更新一次？

A: 
1. 实时天气数据每小时更新
2. 预报数据每天更新4次
3. 极端天气会及时推送提醒

---

## 📖 相关文档

- [快速开始](./getting-started.md) - 5分钟上手指南
- [装备管理](./equipment-management.md) - 详细装备使用指南
- [钓鱼推荐](./fishing-recommendations.md) - 深入了解推荐系统
- [故障排除](./troubleshooting.md) - 常见问题解决方案
- [常见问题](./faq.md) - 用户FAQ解答

---

**指南版本**: v5.0.2  
**适用系统版本**: v5.0.2+  
**更新时间**: 2024-12-20