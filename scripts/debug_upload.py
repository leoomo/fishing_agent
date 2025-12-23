#!/usr/bin/env python3
"""
爬虫图片上传调试脚本

从缓存文件读取爬虫结果并上传到服务器，用于调试上传逻辑而无需重新运行RPA爬虫。

使用方法:
    # 从缓存文件上传到指定任务
    python scripts/debug_upload.py --cache shared/debug/crawl_cache/2.json --task-id 2

    # 指定服务器地址
    python scripts/debug_upload.py --cache shared/debug/crawl_cache/2.json --task-id 2 --server http://localhost:8000

    # 使用已有token跳过注册
    python scripts/debug_upload.py --cache shared/debug/crawl_cache/2.json --task-id 2 --token worker_id:api_key
"""

import argparse
import json
import logging
import sys
import uuid
from pathlib import Path

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from packages.scraper.worker.api_client import ApiWorkerClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_product_id(brand_name: str, product_name: str) -> str:
    """
    生成产品标识：品牌_产品名

    Args:
        brand_name: 品牌名称
        product_name: 产品名称

    Returns:
        产品标识
    """
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


def load_cache(cache_file: str) -> dict:
    """
    加载缓存文件

    Args:
        cache_file: 缓存文件路径

    Returns:
        缓存数据
    """
    cache_path = Path(cache_file)
    if not cache_path.exists():
        raise FileNotFoundError(f"缓存文件不存在: {cache_file}")

    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"缓存文件加载成功: {cache_file}")
    logger.info(f"  任务ID: {data.get('task_id')}")
    logger.info(f"  任务类型: {data.get('task_type')}")
    logger.info(f"  时间戳: {data.get('timestamp')}")
    logger.info(f"  产品数量: {len(data.get('products', []))}")

    return data


def upload_from_cache(
    cache_file: str,
    task_id: int,
    server_url: str = "http://localhost:8000",
    worker_token: str = None,
    worker_id: str = "debug-upload-worker",
) -> bool:
    """
    从缓存文件上传图片

    Args:
        cache_file: 缓存文件路径
        task_id: 任务ID
        server_url: 服务器地址
        worker_token: Worker认证token（可选）
        worker_id: Worker ID

    Returns:
        是否成功
    """
    # 加载缓存
    cache_data = load_cache(cache_file)
    products = cache_data.get("products", [])

    if not products:
        logger.error("缓存文件中没有产品数据")
        return False

    # 创建客户端
    client = ApiWorkerClient(
        server_url=server_url,
        worker_id=worker_id,
        worker_name="Debug-Upload-Worker",
        supported_types=["taobao", "jd", "forum"],
        max_concurrent=1,
    )

    # 注册或使用已有token
    if worker_token:
        client.token = worker_token
        logger.info(f"使用已有token: {worker_token[:20]}...")
    else:
        logger.info("注册Worker...")
        if not client.register():
            logger.error("Worker注册失败")
            return False
        logger.info(f"Worker注册成功: worker_id={client.worker_id}")

    # 准备上传数据
    products_metadata = []
    image_files = []

    for idx, product in enumerate(products):
        product_id = product.get("product_id", f"product_{idx}")
        brand_name = product.get("brand_name", "")
        product_name = product.get("product_name", "")

        # 添加产品元数据
        products_metadata.append({
            "product_id": generate_product_id(brand_name, product_name),
            "brand_name": brand_name,
            "product_name": product_name,
            "source_url": product.get("source_url", ""),
            "image_count": product.get("image_count", 0),
            "equipment_type": product.get("equipment_type", "路亚竿"),
        })

        # 添加图片文件
        for img_idx, img_path_str in enumerate(product.get("images", [])):
            img_path = Path(img_path_str)
            if img_path.exists():
                ext = img_path.suffix if img_path.suffix else '.jpg'
                # 文件名格式: {product_index}_{image_index}.ext
                new_filename = f"{idx}_{img_idx}{ext}"
                image_files.append((new_filename, open(img_path, 'rb')))
                logger.debug(f"添加图片: {new_filename} <- {img_path}")
            else:
                logger.warning(f"图片不存在: {img_path}")

    if not image_files:
        logger.error("没有找到有效的图片文件")
        return False

    logger.info(f"准备上传 {len(image_files)} 张图片，{len(products_metadata)} 个产品")

    # 上传
    try:
        result = client.upload_images(
            task_id=task_id,
            products=products_metadata,
            image_files=image_files,
        )

        if result:
            logger.info("=" * 50)
            logger.info("上传完成!")
            logger.info(f"  上传成功: {result.get('uploaded_count', 0)}")
            logger.info(f"  跳过重复: {result.get('skipped_count', 0)}")
            logger.info(f"  上传失败: {result.get('failed_count', 0)}")

            if result.get('pending_ids'):
                logger.info(f"  Pending IDs: {result.get('pending_ids')}")

            if result.get('errors'):
                logger.warning("  错误信息:")
                for err in result.get('errors', []):
                    logger.warning(f"    - {err}")

            logger.info("=" * 50)
            return result.get('success', False)
        else:
            logger.error("上传返回结果为空")
            return False

    except Exception as e:
        logger.error(f"上传失败: {e}", exc_info=True)
        return False

    finally:
        # 确保文件被关闭
        for _, f in image_files:
            try:
                f.close()
            except Exception:
                pass


def main():
    """入口函数"""
    parser = argparse.ArgumentParser(
        description="爬虫图片上传调试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/debug_upload.py --cache shared/debug/crawl_cache/2.json --task-id 2
  python scripts/debug_upload.py --cache shared/debug/crawl_cache/2.json --task-id 2 --server http://localhost:8000
  python scripts/debug_upload.py --cache shared/debug/crawl_cache/2.json --task-id 2 --token worker_id:api_key
        """
    )

    parser.add_argument(
        "--cache", "-c",
        required=True,
        help="缓存文件路径 (如: shared/debug/crawl_cache/2.json)"
    )
    parser.add_argument(
        "--task-id", "-t",
        type=int,
        required=True,
        help="任务ID"
    )
    parser.add_argument(
        "--server", "-s",
        default="http://localhost:8000",
        help="服务器地址 (默认: http://localhost:8000)"
    )
    parser.add_argument(
        "--token",
        help="Worker认证token (格式: worker_id:api_key)。如不提供将自动注册"
    )
    parser.add_argument(
        "--worker-id",
        default="debug-upload-worker",
        help="Worker ID (默认: debug-upload-worker)"
    )

    args = parser.parse_args()

    # 执行上传
    success = upload_from_cache(
        cache_file=args.cache,
        task_id=args.task_id,
        server_url=args.server,
        worker_token=args.token,
        worker_id=args.worker_id,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
