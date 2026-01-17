#!/usr/bin/env python3
"""
脚本生成器单元测试

测试场景:
- 不同类型PPT（标题型、内容型、混合型）
- 不同语言内容（中英文混合）
- 不同页数（1页、10页、50页）
- 边界情况（无内容、超长文本、特殊字符）

作者: Claude Code
版本: v1.0
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.modules.script_generator import ScriptGenerator


class TestScriptGenerator(unittest.TestCase):
    """脚本生成器测试类"""

    def setUp(self):
        """测试前准备"""
        self.generator = ScriptGenerator()

    def test_generate_script(self):
        """测试基础脚本生成功能"""
        test_data = [
            {
                'title': '人工智能简介',
                'content': ['什么是AI', 'AI的应用']
            }
        ]

        scripts = self.generator.generate_script(test_data, "测试课程")

        # 验证返回结果
        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0]['page'], 1)
        self.assertEqual(scripts[0]['title'], '人工智能简介')
        self.assertIsInstance(scripts[0]['script'], str)
        self.assertGreater(len(scripts[0]['script']), 0)

    def test_optimize_script(self):
        """测试脚本优化功能"""
        script = "这是测试脚本。没有标点符号。让我们优化它。"

        optimized = self.generator.optimize_script(script)

        # 验证优化结果
        self.assertIsInstance(optimized, str)
        self.assertGreater(len(optimized), 0)
        # 验证添加了停顿标记
        self.assertIn('{pause}', optimized)

    def test_check_script_quality(self):
        """测试脚本质量检查功能"""
        # 测试高质量脚本
        good_script = "这是一个测试脚本。它包含完整的句子。还有标点符号。{pause}"
        quality = self.generator.check_script_quality(good_script)

        self.assertIsInstance(quality, dict)
        self.assertIn('score', quality)
        self.assertIn('issues', quality)
        self.assertIn('suggestions', quality)

        # 测试低质量脚本
        bad_script = "短"  # 太短
        quality = self.generator.check_script_quality(bad_script)

        self.assertLess(quality['score'], 100)

    def test_title_only_slide(self):
        """测试仅标题幻灯片"""
        test_data = [
            {
                'title': '重要概念',
                'content': []
            }
        ]

        scripts = self.generator.generate_script(test_data, "测试课程")

        # 验证模板选择
        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0]['title'], '重要概念')
        self.assertIn('重要概念', scripts[0]['script'])

    def test_content_only_slide(self):
        """测试仅内容幻灯片"""
        test_data = [
            {
                'title': '',
                'content': ['第一点', '第二点', '第三点']
            }
        ]

        scripts = self.generator.generate_script(test_data, "测试课程")

        # 验证内容朗读
        self.assertEqual(len(scripts), 1)
        self.assertIn('第一点', scripts[0]['script'])
        self.assertIn('第二点', scripts[0]['script'])

    def test_mixed_content_slide(self):
        """测试混合内容幻灯片"""
        test_data = [
            {
                'title': '机器学习基础',
                'content': ['监督学习', '无监督学习', '强化学习']
            }
        ]

        scripts = self.generator.generate_script(test_data, "测试课程")

        # 验证详细内容生成
        self.assertEqual(len(scripts), 1)
        self.assertIn('机器学习基础', scripts[0]['script'])
        # 验证所有内容都被包含
        for content in test_data[0]['content']:
            self.assertIn(content, scripts[0]['script'])

    def test_multi_language(self):
        """测试多语言内容"""
        test_data = [
            {
                'title': 'AI与人工智能',
                'content': ['Artificial Intelligence', '机器学习', 'Deep Learning深度学习']
            }
        ]

        scripts = self.generator.generate_script(test_data, "测试课程")

        # 验证多语言内容处理
        self.assertEqual(len(scripts), 1)
        self.assertIn('Artificial Intelligence', scripts[0]['script'])

    def test_empty_slide(self):
        """测试空幻灯片"""
        test_data = [
            {
                'title': '',
                'content': []
            }
        ]

        scripts = self.generator.generate_script(test_data, "测试课程")

        # 验证空幻灯片处理
        self.assertEqual(len(scripts), 1)
        self.assertIsInstance(scripts[0]['script'], str)

    def test_long_text(self):
        """测试超长文本"""
        # 创建包含超长内容的幻灯片
        long_content = ['内容' + str(i) for i in range(100)]
        test_data = [
            {
                'title': '超长内容测试',
                'content': long_content
            }
        ]

        scripts = self.generator.generate_script(test_data, "测试课程")

        # 验证超长文本处理
        self.assertEqual(len(scripts), 1)
        self.assertGreater(len(scripts[0]['script']), 100)

    def test_special_characters(self):
        """测试特殊字符"""
        test_data = [
            {
                'title': '特殊字符测试@#$%',
                'content': ['包含符号: &*()', '包含数字: 123', '包含引号: "test"']
            }
        ]

        scripts = self.generator.generate_script(test_data, "测试课程")

        # 验证特殊字符处理
        self.assertEqual(len(scripts), 1)
        # 应该能处理而不崩溃
        self.assertIsInstance(scripts[0]['script'], str)

    def test_multi_page_script(self):
        """测试多页脚本生成"""
        test_data = [
            {'title': '第1页', 'content': ['内容1']},
            {'title': '第2页', 'content': ['内容2']},
            {'title': '第3页', 'content': ['内容3']},
        ]

        scripts = self.generator.generate_script(test_data, "多页课程")

        # 验证多页处理
        self.assertEqual(len(scripts), 3)
        for i, script in enumerate(scripts):
            self.assertEqual(script['page'], i + 1)
            self.assertIn(str(i + 1), script['script'])

    def test_template_selection(self):
        """测试模板选择逻辑"""
        # 测试详细模板选择（>=3个要点）
        data_detailed = {'title': '标题', 'content': ['1', '2', '3']}
        template = self.generator._select_template(data_detailed, 1, 3)
        self.assertEqual(template, 'content_detailed')

        # 测试简要模板选择（<3个要点）
        data_brief = {'title': '标题', 'content': ['1', '2']}
        template = self.generator._select_template(data_brief, 1, 3)
        self.assertEqual(template, 'content_brief')

        # 测试标题页模板选择
        data_title = {'title': '标题', 'content': []}
        template = self.generator._select_template(data_title, 1, 3)
        self.assertEqual(template, 'title_slide')

        # 测试内容页模板选择
        data_content = {'title': '', 'content': ['1']}
        template = self.generator._select_template(data_content, 1, 3)
        self.assertEqual(template, 'content_only')

    def test_script_editing(self):
        """测试脚本编辑功能"""
        original = "这是原始脚本"
        edits = {'find': '原始', 'replace': '编辑后'}
        edited = self.generator.edit_script(original, edits)

        # 验证编辑结果
        self.assertIn('编辑后', edited)
        self.assertNotIn('原始', edited)

    def test_batch_edit_scripts(self):
        """测试批量编辑脚本"""
        scripts = [
            {'page': 1, 'title': '标题1', 'content': ['内容1'], 'script': '第一页'},
            {'page': 2, 'title': '标题2', 'content': ['内容2'], 'script': '第二页'}
        ]

        edited = self.generator.batch_edit_scripts(
            scripts,
            global_edits={'find': '页', 'replace': 'Slide'}
        )

        # 验证批量编辑
        self.assertEqual(len(edited), 2)
        self.assertIn('Slide', edited[0]['script'])

    def test_optimize_with_feedback(self):
        """测试带反馈的脚本优化"""
        script = "测试脚本。"

        feedback = self.generator.optimize_script_with_feedback(script)

        # 验证反馈结果
        self.assertIn('original', feedback)
        self.assertIn('optimized', feedback)
        self.assertIn('original_quality', feedback)
        self.assertIn('final_quality', feedback)
        self.assertIn('improvement', feedback)

    def test_format_content_list(self):
        """测试内容列表格式化"""
        content = ['要点1', '要点2', '要点3']
        formatted = self.generator._format_content_list(content)

        # 验证格式化结果
        self.assertIn('第1点', formatted)
        self.assertIn('要点1', formatted)
        self.assertIn('第2点', formatted)
        self.assertIn('第2点', formatted)

    def test_variable_replacement(self):
        """测试变量替换功能"""
        template = "这是{title}的测试。{page}页内容。"
        variables = {'title': 'AI', 'page': '1'}
        result = self.generator._replace_variables(template, variables)

        # 验证替换结果
        self.assertIn('AI', result)
        self.assertIn('1', result)
        self.assertNotIn('{title}', result)
        self.assertNotIn('{page}', result)

    def test_performance_many_slides(self):
        """测试多页性能（50页）"""
        # 创建50页测试数据
        test_data = [
            {
                'title': f'第{i}页',
                'content': [f'要点{j}' for j in range(3)]
            }
            for i in range(1, 51)
        ]

        import time
        start_time = time.time()
        scripts = self.generator.generate_script(test_data, "性能测试")
        end_time = time.time()

        # 验证性能
        self.assertEqual(len(scripts), 50)
        # 处理50页应该在合理时间内（这里设定5秒作为上限）
        self.assertLess(end_time - start_time, 5.0)

    def test_error_handling(self):
        """测试错误处理"""
        # 测试空数据
        scripts = self.generator.generate_script([], "测试")
        self.assertEqual(len(scripts), 0)

        # 测试无效模板文件路径（应该会抛出异常或使用默认）
        try:
            generator = ScriptGenerator("/nonexistent/template.txt")
            # 如果没有抛出异常，检查是否使用默认
            self.assertIsInstance(generator.templates, dict)
        except FileNotFoundError:
            # 预期的异常
            pass

    def tearDown(self):
        """测试后清理"""
        pass


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
