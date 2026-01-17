#!/usr/bin/env python3
"""
脚本生成模块 - 将PPT内容转换为教学讲解脚本

功能:
- 基于PPT提取的内容生成教学脚本
- 使用规则模板生成讲解文本
- 可选AI增强（Ollama）

作者: Claude Code
版本: v1.0
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class ScriptGenerator:
    """脚本生成器类"""

    def __init__(self, template_file: Optional[str] = None):
        """
        初始化脚本生成器

        Args:
            template_file: 模板文件路径，如果为None则使用默认模板
        """
        if template_file is None:
            template_file = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "templates", "teaching_script.txt"
            )

        self.template_file = Path(template_file)
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """
        从模板文件加载所有模板

        Returns:
            Dict[str, str]: 模板字典
        """
        templates = {}
        if not self.template_file.exists():
            raise FileNotFoundError(f"模板文件不存在: {self.template_file}")

        with open(self.template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析模板
        # 匹配 TEMPLATE_XXX = """...""" 格式
        pattern = r'TEMPLATE_(\w+)\s*=\s*"""(.+?)"""'
        matches = re.findall(pattern, content, re.DOTALL)

        for name, template in matches:
            # 清理模板内容
            template = template.strip()
            # 处理多行内容
            template = re.sub(r'\n\s+', '\n', template)
            templates[name.lower()] = template

        return templates

    def _replace_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        替换模板中的变量

        Args:
            template: 模板字符串
            variables: 变量字典

        Returns:
            str: 替换后的字符串
        """
        result = template

        # 替换所有变量
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))

        # 清理未替换的变量
        result = re.sub(r'\{[\w_]+\}', '', result)

        # 标准化空格
        result = re.sub(r'\s+', ' ', result)

        return result.strip()

    def _format_content_list(self, content: List[str]) -> str:
        """
        格式化内容列表

        Args:
            content: 内容列表

        Returns:
            str: 格式化后的文本
        """
        if not content:
            return ""

        formatted_items = []
        for i, item in enumerate(content, 1):
            # 清理文本
            item = item.strip()
            if item:
                formatted_items.append(f"第{i}点，{item}。")

        return " ".join(formatted_items)

    def _select_template(self, slide_data: Dict[str, Any], index: int, total: int) -> str:
        """
        根据幻灯片内容选择合适的模板

        Args:
            slide_data: 幻灯片数据
            index: 当前索引
            total: 总页数

        Returns:
            str: 选择的模板名称
        """
        title = slide_data.get('title', '').strip()
        content = slide_data.get('content', [])

        # 多页情况下的首页使用开场白模板
        if total > 1 and index == 0:
            return 'intro'

        # 单页或非首页：根据内容类型选择模板
        # 仅标题无内容
        if title and not content:
            return 'title_slide'

        # 有标题和内容
        if title and content:
            # 内容较多（>=3个要点），使用详细模板
            if len(content) >= 3:
                return 'content_detailed'

            # 内容较少（<3个要点），使用简要模板
            return 'content_brief'

        # 仅内容无标题
        if content and not title:
            return 'content_only'

        # 默认使用简要模板
        return 'content_brief'

    def _generate_transition(self, current_data: Dict[str, Any],
                           next_data: Optional[Dict[str, Any]],
                           index: int, total: int) -> str:
        """
        生成过渡语

        Args:
            current_data: 当前幻灯片数据
            next_data: 下一张幻灯片数据
            index: 当前索引
            total: 总页数

        Returns:
            str: 过渡语
        """
        # 不是最后一页，生成到下一页的过渡
        if index < total - 1 and next_data:
            variables = {
                'previous_title': current_data.get('title', ''),
                'next_title': next_data.get('title', ''),
            }
            template = self.templates.get('transition_next', '')
            return self._replace_variables(template, variables)

        # 最后一页，生成结尾
        if index == total - 1:
            variables = {
                'summary_topics': current_data.get('title', '本课程'),
            }
            template = self.templates.get('outro', '')
            return self._replace_variables(template, variables)

        return ""

    def generate_script(self, slides_data: List[Dict[str, Any]],
                       course_name: str = "课程") -> List[Dict[str, Any]]:
        """
        基于PPT内容生成教学脚本

        Args:
            slides_data: PPT解析后的数据
            course_name: 课程名称

        Returns:
            List[Dict]: 生成的脚本列表
                - page: 页码
                - title: 标题
                - content: 原始内容
                - script: 生成的讲解脚本

        Raises:
            Exception: 脚本生成失败
        """
        if not slides_data:
            return []

        scripts = []
        total_slides = len(slides_data)

        for index, slide_data in enumerate(slides_data):
            try:
                # 选择模板
                template_name = self._select_template(slide_data, index, total_slides)
                template = self.templates.get(template_name, '')

                if not template:
                    # 如果没有找到模板，使用默认模板
                    template = self.templates.get('content_brief', '')

                # 准备变量
                title = slide_data.get('title', '').strip()
                content = slide_data.get('content', [])

                # 格式化内容
                formatted_content = self._format_content_list(content)

                variables = {
                    'title': title,
                    'content': formatted_content,
                    'page': index + 1,
                    'course_name': course_name,
                    'content_summary': formatted_content[:50] + '...' if len(formatted_content) > 50 else formatted_content,
                    'content_intro': f"这一页包含了{len(content)}个要点。" if content else "",
                    'content_points': formatted_content,
                    'content朗读': formatted_content,
                    'content_list': formatted_content,
                    'content_explanation': "让我们逐一了解。" if content else "",
                    'table_description': f"表格包含{len(content)}行数据。" if content else "",
                }

                # 替换变量
                script_text = self._replace_variables(template, variables)

                # 生成过渡语
                next_data = slides_data[index + 1] if index < total_slides - 1 else None
                transition = self._generate_transition(slide_data, next_data, index, total_slides)

                # 合并脚本和过渡语
                full_script = script_text
                if transition:
                    full_script += " " + transition

                # 优化脚本
                full_script = self.optimize_script(full_script)

                scripts.append({
                    'page': index + 1,
                    'title': title,
                    'content': content,
                    'script': full_script
                })

            except Exception as e:
                # 如果生成失败，记录错误并继续
                print(f"生成第{index + 1}页脚本时出错: {str(e)}")
                # 返回默认脚本
                scripts.append({
                    'page': index + 1,
                    'title': slide_data.get('title', ''),
                    'content': slide_data.get('content', []),
                    'script': f"这是第{index + 1}页的内容。"
                })

        return scripts

    def check_script_quality(self, script: str) -> Dict[str, Any]:
        """
        检查脚本质量

        Args:
            script: 待检查的脚本

        Returns:
            Dict[str, Any]: 质量检查报告
        """
        issues = []
        score = 100

        if not script:
            return {
                'score': 0,
                'issues': ['脚本为空'],
                'suggestions': ['请提供脚本内容']
            }

        # 检查文本长度
        length = len(script)
        if length < 20:
            issues.append('脚本过短')
            score -= 10
        elif length > 500:
            issues.append('脚本过长')
            score -= 10

        # 检查语句完整性
        if not re.search(r'[。！？]', script):
            issues.append('缺少句号或问号')
            score -= 15

        # 检查重复内容
        words = script.split()
        if len(words) > 0:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.5:
                issues.append('内容重复度较高')
                score -= 10

        # 检查专业术语
        technical_terms = ['人工智能', '机器学习', '深度学习', '神经网络', '算法', '数据', '模型']
        has_technical = any(term in script for term in technical_terms)
        if not has_technical:
            issues.append('未检测到专业术语')
            score -= 5

        # 检查停顿标记
        pause_count = script.count('{pause}')
        if pause_count == 0:
            issues.append('缺少停顿标记')
            score -= 10
        elif pause_count > length / 20:
            issues.append('停顿标记过多')
            score -= 5

        # 生成建议
        suggestions = []
        if length < 20:
            suggestions.append('增加更多内容描述')
        if length > 500:
            suggestions.append('建议拆分长句')
        if not re.search(r'[。！？]', script):
            suggestions.append('添加适当的标点符号')
        if pause_count == 0:
            suggestions.append('添加停顿标记以改善语音效果')

        return {
            'score': max(0, score),
            'issues': issues,
            'suggestions': suggestions,
            'length': length,
            'pause_count': pause_count
        }

    def optimize_script(self, script: str) -> str:
        """
        优化脚本质量

        Args:
            script: 原始脚本

        Returns:
            str: 优化后的脚本
        """
        if not script:
            return ""

        result = script

        # 1. 添加适当的停顿标记
        # 在句号、逗号、问号、感叹号后添加停顿
        result = re.sub(r'([。！？])', r'\1{pause}', result)
        result = re.sub(r'([，])', r'\1{pause}', result)

        # 2. 优化连接词
        # 替换简单的连接词
        result = re.sub(r'现在我们来看', '接下来我们来看', result)
        result = re.sub(r'让我们', '请大家跟随我一起', result)

        # 3. 调整语速标记
        # 在长句中添加语速调整标记
        sentences = result.split('{pause}')
        optimized_sentences = []
        for sentence in sentences:
            if len(sentence) > 50:
                # 长句添加语速标记
                optimized_sentences.append(sentence + '{speed:0.9}')
            else:
                optimized_sentences.append(sentence)
        result = '{pause}'.join(optimized_sentences)

        # 4. 清理多余的停顿
        result = re.sub(r'\{pause\}\s*\{pause\}', '{pause}', result)

        # 5. 标准化空格
        result = re.sub(r'\s+', ' ', result)

        return result.strip()

    def optimize_script_with_feedback(self, script: str) -> Dict[str, Any]:
        """
        优化脚本并提供反馈

        Args:
            script: 原始脚本

        Returns:
            Dict[str, Any]: 优化结果和反馈
        """
        # 检查质量
        quality_report = self.check_script_quality(script)

        # 优化脚本
        optimized = self.optimize_script(script)

        # 再次检查优化后的质量
        final_report = self.check_script_quality(optimized)

        return {
            'original': script,
            'optimized': optimized,
            'original_quality': quality_report,
            'final_quality': final_report,
            'improvement': final_report['score'] - quality_report['score']
        }

    def edit_script(self, script: str, edits: Dict[str, str]) -> str:
        """
        支持人工编辑脚本

        Args:
            script: 原始脚本
            edits: 编辑指令字典
                - 'find': 要查找的文本
                - 'replace': 替换为的文本
                - 'insert': 要插入的文本（需要指定位置）
                - 'delete': 要删除的文本

        Returns:
            str: 编辑后的脚本
        """
        result = script

        # 执行替换
        if 'find' in edits and 'replace' in edits:
            result = result.replace(edits['find'], edits['replace'])

        # 执行插入（简单实现，插入到末尾）
        if 'insert' in edits:
            result += " " + edits['insert']

        # 执行删除
        if 'delete' in edits:
            result = result.replace(edits['delete'], '')

        return result.strip()

    def batch_edit_scripts(self, scripts: List[Dict[str, Any]],
                          global_edits: Optional[Dict[str, str]] = None,
                          per_script_edits: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, Any]]:
        """
        批量编辑多个脚本

        Args:
            scripts: 脚本列表
            global_edits: 全局编辑指令
            per_script_edits: 每页特定编辑指令

        Returns:
            List[Dict[str, Any]]: 编辑后的脚本列表
        """
        edited_scripts = []

        for i, script_data in enumerate(scripts):
            edited_script_text = script_data['script']

            # 应用全局编辑
            if global_edits:
                edited_script_text = self.edit_script(edited_script_text, global_edits)

            # 应用特定编辑
            if per_script_edits and i < len(per_script_edits):
                edited_script_text = self.edit_script(edited_script_text, per_script_edits[i])

            edited_scripts.append({
                'page': script_data['page'],
                'title': script_data['title'],
                'content': script_data['content'],
                'script': edited_script_text
            })

        return edited_scripts

    def generate_script_with_ai(self, slides_data: List[Dict[str, Any]],
                               course_name: str = "课程") -> List[Dict[str, Any]]:
        """
        使用AI模型生成更自然的脚本（占位符实现）

        Args:
            slides_data: PPT解析后的数据
            course_name: 课程名称

        Returns:
            List[Dict]: AI生成的脚本列表
        """
        # TODO: 实现AI增强功能
        # 当前返回基础版本
        return self.generate_script(slides_data, course_name)


# 模块级别的便捷函数
def generate_script(slides_data: List[Dict[str, Any]],
                   course_name: str = "课程") -> List[Dict[str, Any]]:
    """
    基于PPT内容生成教学脚本（便捷函数）

    Args:
        slides_data: PPT解析后的数据
        course_name: 课程名称

    Returns:
        List[Dict]: 生成的脚本列表
    """
    generator = ScriptGenerator()
    return generator.generate_script(slides_data, course_name)


def optimize_script(script: str) -> str:
    """
    优化脚本质量（便捷函数）

    Args:
        script: 原始脚本

    Returns:
        str: 优化后的脚本
    """
    generator = ScriptGenerator()
    return generator.optimize_script(script)


if __name__ == "__main__":
    print("脚本生成模块已加载")
    print("版本: v1.0")
    print("功能: 基于规则模板生成教学脚本")

    # 测试代码
    test_data = [
        {
            'page': 1,
            'title': '人工智能简介',
            'content': ['什么是人工智能', 'AI的发展历程', 'AI的应用领域']
        },
        {
            'page': 2,
            'title': '机器学习基础',
            'content': ['监督学习', '无监督学习', '强化学习']
        }
    ]

    generator = ScriptGenerator()
    scripts = generator.generate_script(test_data, "AI基础课程")

    print("\n生成脚本示例:")
    for script in scripts:
        print(f"\n第{script['page']}页: {script['title']}")
        print(f"脚本: {script['script'][:100]}...")
