#!/usr/bin/env python3
"""
自然脚本生成器 - 生成更自然的教学讲解脚本

特点:
- 不说"第几页"
- 直接讲解核心内容
- 符合真实讲解习惯
- 自然流畅

作者: Claude Code
版本: v2.0
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class NaturalScriptGenerator:
    """自然脚本生成器"""

    def __init__(self):
        """初始化生成器"""
        pass

    def _clean_text(self, text: str) -> str:
        """
        清理文本，移除无用字符

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        # 移除常见的无用文本
        text = re.sub(r'\.pptx$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'第\d+章', '', text)
        text = re.sub(r'^\d+$', '', text)  # 纯数字
        text = re.sub(r'^(PART|SECTION|CHAPTER)\s*\d*\.?\d*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def generate_natural_script(self, slides_data: List[Dict[str, Any]],
                               course_name: str = "课程") -> List[Dict[str, Any]]:
        """
        生成自然讲解脚本

        Args:
            slides_data: PPT解析后的数据
            course_name: 课程名称

        Returns:
            List[Dict]: 生成的脚本列表
        """
        if not slides_data:
            return []

        scripts = []

        for index, slide_data in enumerate(slides_data):
            title = self._clean_text(slide_data.get('title', ''))
            content = slide_data.get('content', [])

            # 跳过无效页面（如目录页）
            if self._is_invalid_slide(title, content, index):
                continue

            # 生成脚本
            script_parts = []

            # 开场（仅第一页有意义的页面）
            if index == 0 and (title or any(content)):
                script_parts.append(f"今天我们来学习：{title}" if title else "今天我们来学习这部分内容")

            # 添加标题（仅当标题有意义且不是页码）
            if title and not title.isdigit() and len(title) > 1:
                script_parts.append(f"我们来看：{title}")

            # 添加内容
            for item in content:
                item = self._clean_text(item)
                if item and len(item) > 1:
                    script_parts.append(item)

            # 合并脚本
            script = " ".join(script_parts)

            # 添加停顿标记
            script = self._add_pauses(script)

            scripts.append({
                'page': index + 1,
                'title': title,
                'content': content,
                'script': script
            })

        return scripts

    def _is_invalid_slide(self, title: str, content: List[str], index: int) -> bool:
        """
        判断是否为无效页面（如目录页）

        Args:
            title: 标题
            content: 内容列表
            index: 页面索引

        Returns:
            bool: True表示跳过此页
        """
        # 跳过纯数字标题（通常是页码）
        if title.isdigit():
            return True

        # 跳过明显是目录的页面
        if index < 2 and any(keyword in title.lower() for keyword in ['目录', 'contents', 'chapter', '章']):
            return True

        return False

    def _add_pauses(self, text: str) -> str:
        """
        添加自然的停顿标记

        Args:
            text: 原始文本

        Returns:
            str: 添加停顿后的文本
        """
        if not text:
            return ""

        result = text

        # 在句号、问号、感叹号后添加停顿
        result = re.sub(r'([。！？])', r'\1{pause}', result)

        # 在逗号后添加停顿（但不要太多）
        result = re.sub(r'([，])', r'\1{pause}', result)

        # 清理多余的停顿
        result = re.sub(r'\{pause\}\s*\{pause\}', '{pause}', result)

        # 标准化空格
        result = re.sub(r'\s+', ' ', result)

        return result.strip()


# 便捷函数
def generate_natural_script(slides_data: List[Dict[str, Any]],
                           course_name: str = "课程") -> List[Dict[str, Any]]:
    """
    生成自然讲解脚本（便捷函数）

    Args:
        slides_data: PPT解析后的数据
        course_name: 课程名称

    Returns:
        List[Dict]: 生成的脚本列表
    """
    generator = NaturalScriptGenerator()
    return generator.generate_natural_script(slides_data, course_name)


if __name__ == "__main__":
    print("自然脚本生成器已加载")
    print("版本: v2.0")
    print("特点: 自然流畅，符合真实讲解习惯")
