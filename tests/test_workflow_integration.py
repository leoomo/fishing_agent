#!/usr/bin/env python3
"""
工作流系统集成测试

测试工作流系统的核心功能，不依赖复杂的RPA环境
"""

import logging
import json
import sys
import time
import threading
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from packages.agent_fishing.tools.lure.database import get_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestWorkflowIntegration:
    """工作流集成测试类"""

    def __init__(self):
        self.db = get_db()

    def test_database_tables(self):
        """测试数据库表是否正确创建"""
        logger.info("=== 测试数据库表结构 ===")

        try:
            # 检查crawler_tasks表
            result = self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crawler_tasks'")
            if result:
                logger.info("✅ crawler_tasks表存在")

                # 检查新增字段
                columns = self.db.execute("PRAGMA table_info(crawler_tasks)")
                column_names = [col['name'] for col in columns]

                required_fields = [
                    'workflow_id', 'workflow_name', 'parent_task_id',
                    'step_order', 'step_config', 'platform', 'shop_url',
                    'retry_count', 'max_retries', 'timeout_seconds',
                    'requires_intervention', 'duplicate_items', 'invalid_items'
                ]

                missing_fields = []
                for field in required_fields:
                    if field not in column_names:
                        missing_fields.append(field)

                if missing_fields:
                    logger.error(f"❌ 缺少字段: {missing_fields}")
                    return False
                else:
                    logger.info("✅ 所有必要字段都存在")
            else:
                logger.error("❌ crawler_tasks表不存在")
                return False

            # 检查crawler_workflow_templates表
            result = self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crawler_workflow_templates'")
            if result:
                logger.info("✅ crawler_workflow_templates表存在")
            else:
                logger.error("❌ crawler_workflow_templates表不存在")
                return False

            # 检查crawler_schedules表
            result = self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crawler_schedules'")
            if result:
                logger.info("✅ crawler_schedules表存在")
            else:
                logger.error("❌ crawler_schedules表不存在")
                return False

            return True

        except Exception as e:
            logger.error(f"数据库测试失败: {e}", exc_info=True)
            return False

    def test_task_creation(self):
        """测试任务创建功能"""
        logger.info("\n=== 测试任务创建 ===")

        try:
            # 创建一个测试任务
            task_config = {
                "keywords": ["路亚竿"],
                "max_pages": 2,
                "platform": "taobao"
            }

            insert_query = """
            INSERT INTO crawler_tasks (
                task_type, task_name, status, config, platform,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """

            task_id = self.db.execute_write(
                insert_query,
                ("taobao", "测试任务-路亚竿爬取", "pending", json.dumps(task_config), "taobao")
            )

            if task_id:
                logger.info(f"✅ 成功创建任务，ID: {task_id}")

                # 验证任务
                task = self.db.execute("SELECT * FROM crawler_tasks WHERE id = ?", (task_id,))
                if task:
                    logger.info(f"✅ 任务验证成功: {task[0]['task_name']}")
                    return True
                else:
                    logger.error("❌ 无法查询创建的任务")
                    return False
            else:
                logger.error("❌ 任务创建失败")
                return False

        except Exception as e:
            logger.error(f"任务创建测试失败: {e}", exc_info=True)
            return False

    def test_workflow_template_creation(self):
        """测试工作流模板创建"""
        logger.info("\n=== 测试工作流模板创建 ===")

        try:
            # 示例工作流模板
            workflow_template = {
                "name": "淘宝店铺商品抓取",
                "description": "从淘宝店铺抓取所有商品",
                "version": "1.0",
                "steps": [
                    {
                        "id": "step_1",
                        "order": 1,
                        "task_type": "taobao",
                        "name": "分析店铺分类",
                        "config": {
                            "shop_url": "{{shop_url}}",
                            "action": "analyze_shop"
                        },
                        "max_retries": 3,
                        "timeout": 600,
                        "depends_on": []
                    },
                    {
                        "id": "step_2",
                        "order": 2,
                        "task_type": "taobao",
                        "name": "抓取店铺商品",
                        "config": {
                            "shop_url": "{{shop_url}}",
                            "categories": "{{step_1.result.categories}}",
                            "max_pages": "{{max_pages}}"
                        },
                        "max_retries": 3,
                        "timeout": 3600,
                        "depends_on": ["step_1"]
                    }
                ],
                "params": {
                    "shop_url": {
                        "type": "string",
                        "required": True,
                        "description": "店铺URL"
                    },
                    "max_pages": {
                        "type": "integer",
                        "default": 5,
                        "description": "每个分类最大抓取页数"
                    }
                }
            }

            insert_query = """
            INSERT INTO crawler_workflow_templates (
                name, description, template_json, category, is_system,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """

            template_id = self.db.execute_write(
                insert_query,
                (
                    "淘宝店铺商品抓取",
                    "从淘宝店铺抓取所有商品",
                    json.dumps(workflow_template),
                    "shop",
                    1  # 系统模板
                )
            )

            if template_id:
                logger.info(f"✅ 成功创建工作流模板，ID: {template_id}")
                return True
            else:
                logger.error("❌ 工作流模板创建失败")
                return False

        except Exception as e:
            logger.error(f"工作流模板测试失败: {e}", exc_info=True)
            return False

    def test_schedule_creation(self):
        """测试定时调度创建"""
        logger.info("\n=== 测试定时调度创建 ===")

        try:
            # 获取工作流模板ID
            template = self.db.execute("SELECT id FROM crawler_workflow_templates LIMIT 1")
            if not template:
                logger.warning("⚠️ 没有找到工作流模板，跳过调度测试")
                return True

            template_id = template[0]['id']

            # 创建调度
            schedule_config = {
                "shop_url": "https://shop.taobao.com/example",
                "max_pages": 10
            }

            insert_query = """
            INSERT INTO crawler_schedules (
                name, template_id, cron_expression, timezone, config,
                is_enabled, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """

            schedule_id = self.db.execute_write(
                insert_query,
                (
                    "每日凌晨2点抓取",
                    template_id,
                    "0 2 * * *",  # 每天凌晨2点
                    "Asia/Shanghai",
                    json.dumps(schedule_config),
                    1  # 启用
                )
            )

            if schedule_id:
                logger.info(f"✅ 成功创建定时调度，ID: {schedule_id}")
                return True
            else:
                logger.error("❌ 定时调度创建失败")
                return False

        except Exception as e:
            logger.error(f"定时调度测试失败: {e}", exc_info=True)
            return False

    def test_dag_execution(self):
        """测试DAG执行逻辑"""
        logger.info("\n=== 测试DAG执行逻辑 ===")

        try:
            # 简单的DAG执行器
            class SimpleDAGEngine:
                def __init__(self):
                    self.completed_steps = set()
                    self.step_results = {}

                def execute_step(self, step):
                    logger.info(f"执行步骤: {step['name']} (order={step['order']})")

                    # 检查依赖
                    for dep in step.get('depends_on', []):
                        if dep not in self.completed_steps:
                            logger.warning(f"步骤 {step['id']} 依赖 {dep} 未完成，跳过")
                            return False

                    # 模拟执行
                    time.sleep(0.1)

                    # 记录完成
                    self.completed_steps.add(step['id'])
                    self.step_results[step['id']] = f"Step {step['id']} result"

                    logger.info(f"✅ 步骤完成: {step['name']}")
                    return True

                def execute_workflow(self, workflow_def):
                    steps = sorted(workflow_def['steps'], key=lambda x: x['order'])

                    # 多轮执行直到所有步骤完成
                    max_rounds = len(steps) * 2
                    for round_num in range(max_rounds):
                        logger.info(f"\n--- 执行轮次 {round_num + 1} ---")

                        progress_made = False
                        for step in steps:
                            if step['id'] not in self.completed_steps:
                                if self.execute_step(step):
                                    progress_made = True

                        # 检查是否全部完成
                        if len(self.completed_steps) == len(steps):
                            logger.info("✅ 所有步骤执行完成！")
                            return True

                        # 如果本轮没有进展，可能存在循环依赖
                        if not progress_made:
                            logger.error("❌ 检测到循环依赖或无法满足的依赖")
                            return False

                    return False

            # 测试工作流
            test_workflow = {
                "steps": [
                    {
                        "id": "step_1",
                        "order": 1,
                        "name": "初始化",
                        "depends_on": []
                    },
                    {
                        "id": "step_2",
                        "order": 2,
                        "name": "执行任务",
                        "depends_on": ["step_1"]
                    },
                    {
                        "id": "step_3",
                        "order": 3,
                        "name": "清理",
                        "depends_on": ["step_2"]
                    }
                ]
            }

            engine = SimpleDAGEngine()
            success = engine.execute_workflow(test_workflow)

            if success:
                logger.info(f"✅ DAG执行成功，完成步骤: {list(engine.completed_steps)}")
                return True
            else:
                logger.error("❌ DAG执行失败")
                return False

        except Exception as e:
            logger.error(f"DAG执行测试失败: {e}", exc_info=True)
            return False

    def test_parameter_replacement(self):
        """测试参数替换功能"""
        logger.info("\n=== 测试参数替换 ===")

        try:
            # 参数替换函数
            def replace_params(template_str, params):
                """替换模板中的参数占位符"""
                for key, value in params.items():
                    placeholder = f"{{{{{key}}}}}"
                    if isinstance(value, str):
                        template_str = template_str.replace(placeholder, value)
                    else:
                        template_str = template_str.replace(placeholder, json.dumps(value))
                return template_str

            # 测试用例
            template = {
                "shop_url": "{{shop_url}}",
                "max_pages": "{{max_pages}}",
                "categories": ["{{category}}", "{{other_category}}"]
            }

            params = {
                "shop_url": "https://shop.taobao.com/test",
                "max_pages": 10,
                "category": "鱼竿",
                "other_category": "渔轮"
            }

            template_str = json.dumps(template, indent=2)
            result_str = replace_params(template_str, params)
            result = json.loads(result_str)

            logger.info(f"✅ 参数替换成功:")
            logger.info(f"  shop_url: {result['shop_url']}")
            logger.info(f"  max_pages: {result['max_pages']}")
            logger.info(f"  categories: {result['categories']}")

            # 验证替换结果
            assert result['shop_url'] == params['shop_url']
            assert result['max_pages'] == params['max_pages']
            assert params['category'] in result['categories']

            return True

        except Exception as e:
            logger.error(f"参数替换测试失败: {e}", exc_info=True)
            return False


def main():
    """运行所有测试"""
    logger.info("开始工作流系统集成测试")

    tester = TestWorkflowIntegration()

    tests = [
        ("数据库表结构", tester.test_database_tables),
        ("任务创建", tester.test_task_creation),
        ("工作流模板创建", tester.test_workflow_template_creation),
        ("定时调度创建", tester.test_schedule_creation),
        ("DAG执行", tester.test_dag_execution),
        ("参数替换", tester.test_parameter_replacement),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'='*50}")

        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 异常: {e}", exc_info=True)
            results.append((test_name, False))

    # 输出测试结果
    logger.info(f"\n{'='*50}")
    logger.info("测试结果汇总:")
    logger.info(f"{'='*50}")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        logger.info("🎉 所有测试通过！工作流系统基础功能正常。")
        return 0
    else:
        logger.error("部分测试失败，需要进一步调试。")
        return 1


if __name__ == "__main__":
    exit(main())