"""
API Worker - 适配 apps/api 的分布式Worker

使用 ApiWorkerClient 连接到 apps/api 的 /api/v1/worker/* 端点
"""

import logging
import signal
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Callable

from .api_client import ApiWorkerClient

logger = logging.getLogger(__name__)


class ApiWorker:
    """
    API Worker - 适配 apps/api 的分布式Worker

    功能:
    - 注册到服务端获取认证 Token
    - 定期轮询领取待执行任务
    - 执行任务并汇报进度/结果
    - 发送心跳保持连接
    """

    def __init__(
        self,
        server_url: str,
        worker_id: Optional[str] = None,
        worker_name: Optional[str] = None,
        supported_types: List[str] = None,
        max_concurrent: int = 1,
        poll_interval: int = 5,
        heartbeat_interval: int = 30,
    ):
        """
        初始化 Worker

        Args:
            server_url: 服务器地址
            worker_id: Worker ID (自动生成)
            worker_name: Worker 名称
            supported_types: 支持的任务类型
            max_concurrent: 最大并发任务数
            poll_interval: 轮询间隔 (秒)
            heartbeat_interval: 心跳间隔 (秒)
        """
        self.server_url = server_url.rstrip("/")
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.worker_name = worker_name or f"Worker-{self.worker_id[:8]}"
        self.supported_types = supported_types or ["taobao", "jd", "forum"]
        self.max_concurrent = max_concurrent
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval

        # 运行状态
        self.running = False
        self.current_tasks: List[int] = []

        # HTTP 客户端
        self.client = ApiWorkerClient(
            server_url=server_url,
            worker_id=self.worker_id,
            worker_name=self.worker_name,
            supported_types=self.supported_types,
            max_concurrent=max_concurrent,
        )

        # 线程
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._poll_thread: Optional[threading.Thread] = None

        # 信号处理
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        logger.info(
            f"Worker 初始化: id={self.worker_id}, name={self.worker_name}, "
            f"server={self.server_url}"
        )

    def _handle_signal(self, signum, _frame):
        """处理终止信号"""
        logger.info(f"收到信号 {signum}，准备退出...")
        self.stop()
        sys.exit(0)

    def start(self) -> bool:
        """
        启动 Worker

        Returns:
            是否成功
        """
        logger.info("正在启动 Worker...")

        # 注册
        if not self.client.register():
            logger.error("注册失败，无法启动")
            return False

        self.running = True

        # 启动心跳线程
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="heartbeat",
        )
        self._heartbeat_thread.start()

        # 启动轮询线程
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="poll",
        )
        self._poll_thread.start()

        logger.info(
            f"Worker 已启动: poll_interval={self.poll_interval}s, "
            f"heartbeat_interval={self.heartbeat_interval}s"
        )

        return True

    def stop(self):
        """停止 Worker"""
        logger.info("正在停止 Worker...")
        self.running = False

        # 等待线程结束
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        if self._poll_thread:
            self._poll_thread.join(timeout=5)

        logger.info("Worker 已停止")

    def run_forever(self):
        """持续运行直到收到终止信号"""
        if not self.start():
            return

        logger.info("Worker 正在运行，按 Ctrl+C 退出")

        # 主线程保持运行
        while self.running:
            time.sleep(1)

    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                response = self.client.heartbeat(
                    current_tasks=self.current_tasks,
                )

                if response:
                    # 处理命令
                    commands = response.get("commands", [])
                    self._handle_commands(commands)

            except Exception as e:
                logger.error(f"心跳失败: {e}")

            time.sleep(self.heartbeat_interval)

    def _poll_loop(self):
        """任务轮询循环"""
        while self.running:
            try:
                # 检查是否还有空闲槽位
                if len(self.current_tasks) < self.max_concurrent:
                    tasks = self.client.claim_tasks(
                        max_tasks=self.max_concurrent - len(self.current_tasks)
                    )

                    for task_info in tasks:
                        task_id = task_info["task_id"]
                        self.current_tasks.append(task_id)

                        # 在线程中执行任务
                        thread = threading.Thread(
                            target=self._task_wrapper,
                            args=(task_info,),
                            daemon=True,
                        )
                        thread.start()

            except Exception as e:
                logger.error(f"轮询失败: {e}")

            time.sleep(self.poll_interval)

    def _handle_commands(self, commands: List[Dict]):
        """处理服务器下发的命令"""
        for cmd in commands:
            cmd_type = cmd.get("type")
            if cmd_type == "cancel_task":
                task_id = cmd.get("task_id")
                logger.info(f"收到取消任务命令: {task_id}")

                # 从当前任务列表移除
                if task_id in self.current_tasks:
                    self.current_tasks.remove(task_id)

                # 汇报取消状态
                self.client.report_progress(
                    task_id=task_id,
                    status="cancelled",
                    message="任务已取消",
                )

    def _task_wrapper(self, task_info: Dict):
        """任务执行包装器"""
        task_id = task_info["task_id"]
        try:
            self.execute_task(task_info)
        finally:
            # 任务完成，从当前任务列表移除
            if task_id in self.current_tasks:
                self.current_tasks.remove(task_id)

    def execute_task(self, task_info: Dict) -> bool:
        """
        执行任务

        子类可以重写此方法实现具体的任务执行逻辑

        Args:
            task_info: 任务信息

        Returns:
            是否成功
        """
        task_id = task_info["task_id"]
        task_type = task_info.get("task_type", "unknown")
        config = task_info.get("config", {})

        logger.info(f"开始执行任务 {task_id}: type={task_type}")

        try:
            # 汇报开始
            self.client.report_progress(task_id, "running", 10, "任务开始执行")

            # TODO: 根据 task_type 调用对应的爬虫逻辑
            # 这里需要子类实现具体的爬虫逻辑
            result = self._execute_task_impl(task_type, config)

            # 汇报完成
            if result.get("success"):
                self.client.report_progress(
                    task_id,
                    "success",
                    100,
                    "任务执行完成",
                    success_items=result.get("success_items", 0),
                    total_items=result.get("total_items", 0),
                    result_data=result.get("data"),
                )
                return True
            else:
                self.client.report_progress(
                    task_id,
                    "failed",
                    0,
                    "任务执行失败",
                    error_message=result.get("error", "未知错误"),
                    failed_items=result.get("failed_items", 0),
                )
                return False

        except Exception as e:
            logger.error(f"任务 {task_id} 执行异常: {e}", exc_info=True)
            self.client.report_progress(
                task_id,
                "failed",
                0,
                f"执行异常: {str(e)}",
                error_message=str(e),
            )
            return False

    def _execute_task_impl(self, task_type: str, config: Dict) -> Dict:
        """
        实际执行任务的实现

        子类应该重写此方法

        Args:
            task_type: 任务类型
            config: 任务配置

        Returns:
            执行结果
        """
        logger.warning(f"未实现的任务类型: {task_type}")
        return {
            "success": False,
            "error": f"不支持的任务类型: {task_type}",
            "success_items": 0,
            "failed_items": 0,
            "total_items": 0,
        }


class TaobaoWorker(ApiWorker):
    """
    淘宝爬虫 Worker

    支持执行淘宝任务并上传图片
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 导入 RPA 模块
        try:
            from packages.scraper.rpa.taobao_shop_category_rpa import TaobaoShopCategoryRPA
            self.TaobaoShopCategoryRPA = TaobaoShopCategoryRPA
            self.rpa_available = True
        except ImportError as e:
            logger.warning(f"无法导入淘宝RPA模块: {e}")
            self.rpa_available = False

    def execute_task(self, task_info: Dict) -> bool:
        """
        执行任务（重写以传递 task_id）

        Args:
            task_info: 任务信息

        Returns:
            是否成功
        """
        task_id = task_info["task_id"]
        task_type = task_info.get("task_type", "unknown")
        config = task_info.get("config", {})

        logger.info(f"开始执行任务 {task_id}: type={task_type}")

        try:
            # 汇报开始
            self.client.report_progress(task_id, "running", 10, "任务开始执行")

            # 执行任务（传递 task_id）
            result = self._execute_task_impl(task_type, config, task_id)

            # 汇报完成
            if result.get("success"):
                self.client.report_progress(
                    task_id,
                    "success",
                    100,
                    "任务执行完成",
                    success_items=result.get("success_items", 0),
                    total_items=result.get("total_items", 0),
                    result_data=result.get("data"),
                )
                return True
            else:
                self.client.report_progress(
                    task_id,
                    "failed",
                    0,
                    "任务执行失败",
                    error_message=result.get("error", "未知错误"),
                    failed_items=result.get("failed_items", 0),
                )
                return False

        except Exception as e:
            logger.error(f"任务 {task_id} 执行异常: {e}", exc_info=True)
            self.client.report_progress(
                task_id,
                "failed",
                0,
                f"执行异常: {str(e)}",
                error_message=str(e),
            )
            return False

    def _execute_task_impl(
        self, task_type: str, config: Dict, task_id: int
    ) -> Dict:
        """执行淘宝任务"""
        if task_type == "taobao":
            return self._execute_taobao_task(config, task_id)
        else:
            return super()._execute_task_impl(task_type, config)

    def _execute_taobao_task(self, config: Dict, task_id: int, save_cache: bool = True) -> Dict:
        """
        执行淘宝爬虫任务并上传图片

        Args:
            config: 任务配置
            task_id: 任务ID
            save_cache: 是否保存缓存文件（用于调试）

        Returns:
            执行结果
        """
        # 检查是否从缓存加载
        cache_file = config.get("_cache_file")
        if cache_file:
            return self._execute_from_cache(cache_file, task_id)

        if not self.rpa_available:
            return {
                "success": False,
                "error": "淘宝RPA模块不可用",
                "success_items": 0,
                "failed_items": 0,
                "total_items": 0,
            }

        # 解析配置
        keywords_raw = config.get("keywords", "")
        shop_url = config.get("shop_url", "")
        max_results = config.get("max_results", 20)

        # 关键词列表
        if isinstance(keywords_raw, list):
            keywords = [kw.strip() for kw in keywords_raw if kw and kw.strip()]
        elif isinstance(keywords_raw, str) and keywords_raw:
            keywords = [kw.strip() for kw in keywords_raw.split(",") if kw.strip()]
        else:
            keywords = []

        logger.info(f"任务配置: keywords={keywords}, shop_url={shop_url}")

        all_results = []
        failed_items = 0

        try:
            # 创建 RPA 实例
            rpa = self.TaobaoShopCategoryRPA()

            # 配置店铺 URL
            if shop_url:
                rpa.shop_url = shop_url

            # 配置分类
            if keywords:
                rpa.category_name = keywords[0]

            # 执行爬取
            all_results = rpa.crawl()
            logger.info(f"爬取完成，获取到 {len(all_results)} 个商品")

            if not all_results:
                return {
                    "success": False,
                    "error": "未采集到任何商品数据",
                    "success_items": 0,
                    "failed_items": 1,
                    "total_items": 1,
                }

            # 保存缓存（用于调试）
            if save_cache:
                try:
                    self._save_crawl_cache(task_id, config, all_results)
                except Exception as e:
                    logger.warning(f"保存缓存失败: {e}")

            # 上传图片
            self.client.report_progress(
                task_id, "running", 70, "正在上传图片..."
            )
            upload_result = self._upload_images(task_id, all_results)

            # 构建结果数据
            products_data = []
            for item in all_results:
                products_data.append({
                    "name": item.name,
                    "brand": item.brand_name,
                    "price": item.price_min,
                    "url": item.source_url,
                    "category": item.category,
                    "model": item.model,
                    "specs": item.specs,
                })

            return {
                "success": True,
                "success_items": len(all_results),
                "failed_items": failed_items,
                "total_items": len(all_results) + failed_items,
                "data": {
                    "products": products_data,
                    "keywords": keywords,
                    "shop_url": shop_url,
                    "upload_result": upload_result,
                },
            }

        except Exception as e:
            logger.error(f"淘宝任务执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "success_items": len(all_results),
                "failed_items": failed_items + 1,
                "total_items": len(all_results) + failed_items + 1,
            }

    def _upload_images(self, task_id: int, results: List) -> Optional[Dict]:
        """
        上传爬取的图片到服务端

        Args:
            task_id: 任务ID
            results: 爬取结果列表

        Returns:
            上传结果
        """
        from pathlib import Path
        import re

        images_base_path = Path("shared/images")

        products_metadata = []
        image_files = []

        try:
            for idx, item in enumerate(results):
                # 获取商品ID（从URL提取或使用图片目录名）
                product_id = None
                if hasattr(item, 'source_url') and item.source_url:
                    match = re.search(r'id=(\d+)', item.source_url)
                    if match:
                        product_id = match.group(1)

                if not product_id:
                    # 使用图片目录名
                    product_id = f"product_{idx}"

                # 图片目录
                image_dir = images_base_path / product_id
                if not image_dir.exists():
                    logger.warning(f"图片目录不存在: {image_dir}")
                    continue

                # 获取所有图片
                img_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
                if not img_files:
                    logger.warning(f"没有找到图片文件: {image_dir}")
                    continue

                logger.info(f"处理商品 {idx} 的 {len(img_files)} 张图片")

                # 添加产品元数据
                products_metadata.append({
                    "product_id": self._generate_product_id(
                        getattr(item, 'brand_name', ''),
                        getattr(item, 'name', '')
                    ),
                    "brand_name": getattr(item, 'brand_name', ''),
                    "product_name": getattr(item, 'name', ''),
                    "source_url": getattr(item, 'source_url', ''),
                    "image_count": len(img_files),
                    "equipment_type": "路亚竿",  # 默认类型，可根据配置修改
                })

                # 添加图片文件（重命名为 {idx}_{img_idx}.ext）
                for img_idx, img_file in enumerate(img_files):
                    ext = img_file.suffix if img_file.suffix else '.jpg'
                    new_filename = f"{idx}_{img_idx}{ext}"
                    image_files.append((new_filename, open(img_file, 'rb')))

            if not image_files:
                logger.warning("没有图片需要上传")
                return None

            # 调用上传
            try:
                result = self.client.upload_images(
                    task_id=task_id,
                    products=products_metadata,
                    image_files=image_files,
                )
            finally:
                # 确保文件被关闭
                for _, f in image_files:
                    try:
                        f.close()
                    except Exception:
                        pass

            return result

        except Exception as e:
            logger.error(f"图片上传失败: {e}", exc_info=True)
            return None

    def _generate_product_id(self, brand_name: str, product_name: str) -> str:
        """生成产品标识：品牌_产品名"""
        import re

        brand = brand_name.strip().lower() if brand_name else ""
        product = product_name.strip().lower() if product_name else ""

        # 替换特殊字符为下划线
        brand = re.sub(r'[^\w\-]', '_', brand)
        product = re.sub(r'[^\w\-]', '_', product)

        # 合并连续下划线
        brand = re.sub(r'_+', '_', brand).strip('_')
        product = re.sub(r'_+', '_', product).strip('_')

        return f"{brand}_{product}" if brand and product else f"product_{uuid.uuid4().hex[:8]}"

    def _save_crawl_cache(
        self,
        task_id: int,
        config: Dict,
        results: List,
        images_base_path: Path = None
    ):
        """
        保存爬虫抓取结果到 JSON 缓存文件

        Args:
            task_id: 任务ID
            config: 任务配置
            results: 爬虫结果列表
            images_base_path: 图片基础路径
        """
        from datetime import datetime
        import re

        if images_base_path is None:
            images_base_path = Path("shared/images")

        # 确保缓存目录存在
        cache_dir = Path("shared/debug/crawl_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)

        # 构建缓存数据
        cache_data = {
            "task_id": task_id,
            "task_type": "taobao",
            "config": config,
            "timestamp": datetime.now().isoformat(),
            "products": []
        }

        for idx, item in enumerate(results):
            # 获取商品ID（从URL提取或使用图片目录名）
            product_id = None
            if hasattr(item, 'source_url') and item.source_url:
                match = re.search(r'id=(\d+)', item.source_url)
                if match:
                    product_id = match.group(1)

            if not product_id:
                product_id = f"product_{idx}"

            # 查找图片目录
            image_dir = images_base_path / product_id
            img_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))

            cache_data["products"].append({
                "index": idx,
                "product_id": product_id,
                "brand_name": getattr(item, 'brand_name', ''),
                "product_name": getattr(item, 'name', ''),
                "source_url": getattr(item, 'source_url', ''),
                "equipment_type": "路亚竿",
                "image_count": len(img_files),
                "images": [str(f) for f in img_files]
            })

        # 保存到文件
        cache_file = cache_dir / f"{task_id}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        logger.info(f"爬虫缓存已保存: {cache_file}")

    def _load_crawl_cache(self, cache_file: str) -> Optional[Dict]:
        """
        从 JSON 缓存文件加载爬虫数据

        Args:
            cache_file: 缓存文件路径

        Returns:
            缓存数据或 None
        """
        try:
            cache_path = Path(cache_file)
            if not cache_path.exists():
                logger.error(f"缓存文件不存在: {cache_file}")
                return None

            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"从缓存加载: task_id={data.get('task_id')}, products={len(data.get('products', []))}")
            return data

        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return None

    def _execute_from_cache(self, cache_file: str, task_id: int) -> Dict:
        """
        从缓存文件执行上传（跳过爬虫步骤）

        Args:
            cache_file: 缓存文件路径
            task_id: 任务ID

        Returns:
            执行结果
        """
        # 加载缓存
        cache_data = self._load_crawl_cache(cache_file)
        if not cache_data:
            return {
                "success": False,
                "error": f"无法加载缓存文件: {cache_file}",
                "success_items": 0,
                "failed_items": 1,
                "total_items": 1,
            }

        logger.info(f"从缓存上传: products={len(cache_data.get('products', []))}")

        # 模拟爬虫结果对象（用于 _upload_images）
        class CachedItem:
            def __init__(self, data):
                self.name = data.get("product_name", "")
                self.brand_name = data.get("brand_name", "")
                self.source_url = data.get("source_url", "")
                # 添加其他可能需要的属性
                self.price_min = None
                self.category = None
                self.model = None
                self.specs = None

        # 构建模拟结果列表
        cached_results = [CachedItem(p) for p in cache_data.get("products", [])]

        # 上传图片
        try:
            self.client.report_progress(
                task_id, "running", 50, "从缓存上传图片..."
            )
            upload_result = self._upload_images_from_cache(
                task_id, cache_data.get("products", [])
            )

            # 构建结果数据
            products_data = []
            for p in cache_data.get("products", []):
                products_data.append({
                    "name": p.get("product_name", ""),
                    "brand": p.get("brand_name", ""),
                    "price": None,
                    "url": p.get("source_url", ""),
                    "category": None,
                    "model": None,
                    "specs": None,
                })

            return {
                "success": True,
                "success_items": len(cache_data.get("products", [])),
                "failed_items": 0,
                "total_items": len(cache_data.get("products", [])),
                "data": {
                    "products": products_data,
                    "upload_result": upload_result,
                    "from_cache": True,
                },
            }

        except Exception as e:
            logger.error(f"从缓存上传失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "success_items": 0,
                "failed_items": len(cache_data.get("products", [])),
                "total_items": len(cache_data.get("products", [])),
            }

    def _upload_images_from_cache(
        self,
        task_id: int,
        products: List[Dict],
    ) -> Optional[Dict]:
        """
        从缓存数据上传图片

        Args:
            task_id: 任务ID
            products: 产品列表（来自缓存）

        Returns:
            上传结果
        """
        from pathlib import Path

        products_metadata = []
        image_files = []

        try:
            for idx, product in enumerate(products):
                # 添加产品元数据
                products_metadata.append({
                    "product_id": self._generate_product_id(
                        product.get("brand_name", ""),
                        product.get("product_name", "")
                    ),
                    "brand_name": product.get("brand_name", ""),
                    "product_name": product.get("product_name", ""),
                    "source_url": product.get("source_url", ""),
                    "image_count": product.get("image_count", 0),
                    "equipment_type": product.get("equipment_type", "路亚竿"),
                })

                # 添加图片文件
                for img_path_str in product.get("images", []):
                    img_path = Path(img_path_str)
                    if img_path.exists():
                        # 获取扩展名
                        ext = img_path.suffix if img_path.suffix else '.jpg'
                        # 文件名格式: {idx}_{img_idx}.ext
                        img_idx = len([f for f in image_files if f[0].startswith(f"{idx}_")])
                        new_filename = f"{idx}_{img_idx}{ext}"
                        image_files.append((new_filename, open(img_path, 'rb')))

            if not image_files:
                logger.warning("缓存中没有图片需要上传")
                return None

            logger.info(f"准备上传 {len(image_files)} 张图片")

            # 调用上传
            try:
                result = self.client.upload_images(
                    task_id=task_id,
                    products=products_metadata,
                    image_files=image_files,
                )
            finally:
                # 确保文件被关闭
                for _, f in image_files:
                    try:
                        f.close()
                    except Exception:
                        pass

            return result

        except Exception as e:
            logger.error(f"缓存图片上传失败: {e}", exc_info=True)
            return None
