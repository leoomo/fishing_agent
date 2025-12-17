"""
表格内容提取模块

使用百度AI Studio API提取图片中的表格文字内容，
并将HTML格式转换为标准Markdown格式。

作者: Claude Code
版本: 1.0.0
"""

import base64
import os
import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any, Tuple, Optional


class TableContentExtractor:
    """表格内容提取器类"""

    def __init__(self, api_url: str = "https://17pdfbx8mbh6jfb4.aistudio-app.com/layout-parsing",
                 token: str = "2bd26c0083441cc29419808330b3dc3ac0504376"):
        """
        初始化表格内容提取器

        Args:
            api_url: API地址
            token: 访问令牌
        """
        self.api_url = api_url
        self.token = token
        self.headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

    def _detect_file_type(self, file_path: str) -> int:
        """
        检测文件类型

        Args:
            file_path: 文件路径

        Returns:
            0 for PDF, 1 for images
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        return 0 if file_ext == '.pdf' else 1

    def _prepare_payload(self, file_path: str) -> Dict[str, Any]:
        """
        准备API请求载荷

        Args:
            file_path: 图片文件路径

        Returns:
            请求载荷字典
        """
        with open(file_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")

        return {
            "file": file_data,
            "fileType": self._detect_file_type(file_path),
            "useDocOrientationClassify": False,
            "useDocUnwarping": False,
            "useChartRecognition": False,
        }

    def html_table_to_markdown(self, html_content: str) -> str:
        """
        将HTML表格转换为Markdown格式

        Args:
            html_content: HTML内容

        Returns:
            Markdown格式的内容
        """
        # 清理HTML内容
        html_content = re.sub(r'<div[^>]*>', '', html_content)
        html_content = re.sub(r'</div>', '', html_content)
        html_content = re.sub(r'<table[^>]*>', '<table>', html_content)
        html_content = re.sub(r"</?style[^>]*>", "", html_content)

        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找表格
        table = soup.find('table')
        if not table:
            # 如果没有表格，提取文本内容
            text = soup.get_text(strip=True)
            return text if text else "未找到内容"

        markdown_rows = []

        # 处理表格行
        for i, row in enumerate(table.find_all('tr')):
            cells = []

            # 处理单元格（th或td）
            for cell in row.find_all(['th', 'td']):
                text = cell.get_text(strip=True)
                text = re.sub(r'\s+', ' ', text)
                cells.append(text if text else ' ')

            if cells:
                markdown_row = '| ' + ' | '.join(cells) + ' |'
                markdown_rows.append(markdown_row)

                # 在第一行后添加分隔线
                if i == 0:
                    separator = '|' + '---|' * len(cells)
                    markdown_rows.append(separator)

        return '\n'.join(markdown_rows)

    def extract_from_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        从单个文件提取表格内容

        Args:
            file_path: 文件路径

        Returns:
            (成功状态, 内容列表)
        """
        try:
            payload = self._prepare_payload(file_path)
            response = requests.post(self.api_url, json=payload, headers=self.headers)

            if response.status_code == 200:
                result = response.json()["result"]
                contents = []

                for res in result["layoutParsingResults"]:
                    if res["markdown"]["text"]:
                        # 转换HTML为Markdown
                        markdown_content = self.html_table_to_markdown(res["markdown"]["text"])
                        contents.append(markdown_content)

                return True, contents
            else:
                return False, [f"API错误: {response.status_code}"]

        except Exception as e:
            return False, [f"提取失败: {str(e)}"]

    def extract_from_images(self, image_folder: str) -> Dict[str, Any]:
        """
        从文件夹中批量提取图片的表格内容

        Args:
            image_folder: 图片文件夹路径

        Returns:
            提取结果字典
        """
        # 获取所有图片文件
        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
        image_files = []

        for root, dirs, files in os.walk(image_folder):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.lower().endswith(image_extensions):
                    rel_path = os.path.relpath(os.path.join(root, f), image_folder)
                    image_files.append(rel_path)

        if not image_files:
            return {
                "success": False,
                "error": "未找到图片文件",
                "results": []
            }

        results = []
        success_count = 0
        error_count = 0

        for image_file in image_files:
            img_path = os.path.join(image_folder, image_file)
            success, contents = self.extract_from_file(img_path)

            result = {
                "filename": image_file,
                "success": success,
                "contents": contents,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            if success:
                success_count += 1
            else:
                error_count += 1

            results.append(result)

            # 避免API调用过于频繁
            import time
            time.sleep(0.5)

        return {
            "success": True,
            "total_files": len(image_files),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }

    def save_to_markdown(self, results: Dict[str, Any], output_file: str = "extracted_tables.md"):
        """
        将提取结果保存为Markdown文件

        Args:
            results: 提取结果
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 表格内容提取结果\n\n")
            f.write(f"**提取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**总文件数**: {results['total_files']}\n")
            f.write(f"**成功提取**: {results['success_count']}\n")
            f.write(f"**提取失败**: {results['error_count']}\n\n")
            f.write("---\n\n")

            for result in results["results"]:
                f.write(f"## {result['filename']}\n\n")
                f.write(f"**状态**: {'✅ 成功' if result['success'] else '❌ 失败'}\n\n")

                if result["success"] and result["contents"]:
                    for i, content in enumerate(result["contents"], 1):
                        if len(result["contents"]) > 1:
                            f.write(f"### 表格 {i}\n\n")
                        f.write(content)
                        f.write("\n\n")
                elif not result["success"] and result["contents"]:
                    f.write(f"**错误信息**: {result['contents'][0]}\n\n")

                f.write("---\n\n")


# 便捷函数
def extract_table_content(file_path: str) -> Tuple[bool, List[str]]:
    """
    便捷函数：从单个文件提取表格内容

    Args:
        file_path: 文件路径

    Returns:
        (成功状态, 内容列表)
    """
    extractor = TableContentExtractor()
    return extractor.extract_from_file(file_path)


def extract_tables_from_folder(folder_path: str, output_file: str = None) -> Dict[str, Any]:
    """
    便捷函数：从文件夹批量提取表格内容

    Args:
        folder_path: 文件夹路径
        output_file: 输出文件路径（可选）

    Returns:
        提取结果字典
    """
    extractor = TableContentExtractor()
    results = extractor.extract_from_images(folder_path)

    if output_file:
        extractor.save_to_markdown(results, output_file)

    return results


# 模块级别配置
DEFAULT_API_URL = "https://17pdfbx8mbh6jfb4.aistudio-app.com/layout-parsing"
DEFAULT_TOKEN = "2bd26c0083441cc29419808330b3dc3ac0504376"