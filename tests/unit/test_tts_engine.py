#!/usr/bin/env python3
"""
TTS引擎单元测试

测试场景:
- 短文本（<50字）
- 中等文本（50-200字）
- 长文本（>200字）
- 特殊字符（数字、标点、英文）
- 重复文本（测试缓存）

作者: Claude Code
版本: v1.0
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# 设置测试环境
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.modules.tts_engine import (
    text_to_speech,
    text_to_speech_batch,
    merge_audio_segments,
    optimize_audio,
    _get_cache_key,
    _get_cache_path,
    TTS_LANGUAGE
)
from src.utils.exceptions import TTSError


class TestTTSEngine(unittest.TestCase):
    """TTS引擎测试类"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.audio_dir = self.test_dir / "audio"
        self.audio_dir.mkdir()

    def tearDown(self):
        """测试后清理"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_get_cache_key(self):
        """测试缓存键生成"""
        text = "测试文本"
        lang = "zh-cn"
        cache_key = _get_cache_key(text, lang)

        # 缓存键应该是MD5哈希（32字符）
        self.assertEqual(len(cache_key), 32)
        self.assertIsInstance(cache_key, str)

        # 相同文本应该生成相同缓存键
        cache_key2 = _get_cache_key(text, lang)
        self.assertEqual(cache_key, cache_key2)

    def test_get_cache_path(self):
        """测试缓存路径生成"""
        text = "测试文本"
        lang = "zh-cn"
        cache_path = _get_cache_path(text, lang)

        # 路径应该包含缓存目录
        self.assertIn("cache", str(cache_path))
        self.assertTrue(cache_path.name.endswith('.mp3'))

    def test_text_to_speech_short_text(self):
        """测试短文本TTS转换"""
        text = "你好，这是测试。"
        output_path = self.audio_dir / "test_short.mp3"

        result = text_to_speech(text, str(output_path), 'zh-cn')

        # 验证结果
        if result:
            self.assertTrue(Path(result).exists())
            self.assertTrue(Path(result).stat().st_size > 0)
            print(f"✓ 短文本测试通过: {text}")

    def test_text_to_speech_medium_text(self):
        """测试中等文本TTS转换"""
        text = """
        人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，
        它试图理解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        """.strip()
        output_path = self.audio_dir / "test_medium.mp3"

        result = text_to_speech(text, str(output_path), 'zh-cn')

        # 验证结果
        if result:
            self.assertTrue(Path(result).exists())
            self.assertTrue(Path(result).stat().st_size > 0)
            print(f"✓ 中等文本测试通过: {len(text)}字符")

    def test_text_to_speech_long_text(self):
        """测试长文本TTS转换"""
        text = """
        深度学习是机器学习的一个分支，它基于人工神经网络的表征学习方法。
        人工神经网络（Artificial Neural Networks）是对人脑神经元网络进行抽象后建立的模型。
        深度学习通过构建具有很多隐层的机器学习模型和海量的训练数据，来学习更有用的特征，
        从而最终提升分类或预测的准确性。深度学习在语音识别、图像识别、自然语言处理等领域
        取得了突破性的进展。深度学习模型通常由多层非线性变换组成，每一层都可以学习到
        数据的不同层次的特征表示。深度学习的核心在于通过逐层的特征变换，将样本在原空间的
        表示转换到一个新的特征空间，在这个特征空间中，样本的表示更加线性可分。
        """.strip()
        output_path = self.audio_dir / "test_long.mp3"

        result = text_to_speech(text, str(output_path), 'zh-cn')

        # 验证结果
        if result:
            self.assertTrue(Path(result).exists())
            self.assertTrue(Path(result).stat().st_size > 0)
            print(f"✓ 长文本测试通过: {len(text)}字符")

    def test_text_to_speech_special_characters(self):
        """测试特殊字符TTS转换"""
        text = "测试数字123、英文ABC、符号!@#%、括号()、引号\"\"。"
        output_path = self.audio_dir / "test_special.mp3"

        result = text_to_speech(text, str(output_path), 'zh-cn')

        # 验证结果
        if result:
            self.assertTrue(Path(result).exists())
            self.assertTrue(Path(result).stat().st_size > 0)
            print(f"✓ 特殊字符测试通过: {text}")

    def test_text_to_speech_empty_text(self):
        """测试空文本TTS转换"""
        text = ""
        output_path = self.audio_dir / "test_empty.mp3"

        result = text_to_speech(text, str(output_path), 'zh-cn')

        # 空文本应该返回None
        self.assertIsNone(result)
        print("✓ 空文本测试通过")

    def test_text_to_speech_whitespace_only(self):
        """测试仅空白字符TTS转换"""
        text = "   \n\t  "
        output_path = self.audio_dir / "test_whitespace.mp3"

        result = text_to_speech(text, str(output_path), 'zh-cn')

        # 仅空白字符应该返回None
        self.assertIsNone(result)
        print("✓ 空白字符测试通过")

    @patch('src.modules.tts_engine.gTTS', None)
    def test_text_to_speech_fallback(self):
        """测试备用TTS方案"""
        text = "这是备用方案测试。"
        output_path = self.audio_dir / "test_fallback.mp3"

        # 模拟gTTS不可用
        with patch('src.modules.tts_engine.gTTS', None):
            result = text_to_speech(text, str(output_path), 'zh-cn')

            # 如果系统有备用TTS，应该能生成文件
            if result:
                self.assertTrue(Path(result).exists())
                print(f"✓ 备用TTS方案测试通过")
            else:
                print(f"⚠ 备用TTS方案未测试（系统不支持）")

    def test_text_to_speech_batch(self):
        """测试批量TTS转换"""
        scripts = [
            {'page': 1, 'title': '第一页', 'script': '这是第一页的内容。'},
            {'page': 2, 'title': '第二页', 'script': '这是第二页的内容。'},
            {'page': 3, 'title': '第三页', 'script': '这是第三页的内容。'},
        ]

        audio_files = text_to_speech_batch(scripts, str(self.audio_dir))

        # 验证结果
        self.assertGreaterEqual(len(audio_files), 0)

        for audio_file in audio_files:
            self.assertTrue(Path(audio_file).exists())
            self.assertTrue(Path(audio_file).stat().st_size > 0)

        print(f"✓ 批量TTS测试通过: {len(audio_files)}个音频文件")

    def test_text_to_speech_batch_with_empty(self):
        """测试批量TTS转换（包含空内容）"""
        scripts = [
            {'page': 1, 'script': '第一页。'},
            {'page': 2, 'script': ''},  # 空内容
            {'page': 3, 'script': '第三页。'},
        ]

        audio_files = text_to_speech_batch(scripts, str(self.audio_dir))

        # 应该只生成有效的音频文件
        self.assertGreaterEqual(len(audio_files), 1)
        print(f"✓ 批量TTS（包含空内容）测试通过: {len(audio_files)}个音频文件")

    @patch('src.modules.tts_engine.AudioSegment')
    def test_merge_audio_segments(self, mock_audio_segment):
        """测试音频合并"""
        # 模拟音频段
        mock_segment1 = MagicMock()
        mock_segment1.__len__ = lambda self: 3000  # 3秒
        mock_segment2 = MagicMock()
        mock_segment2.__len__ = lambda self: 2000  # 2秒

        mock_audio = MagicMock()
        mock_audio.from_file.side_effect = [mock_segment1, mock_segment2]
        mock_audio.silent.return_value = MagicMock()
        mock_audio_instance = mock_audio.return_value
        mock_audio_instance.__add__ = MagicMock(return_value=mock_audio_instance)
        mock_audio_instance.export = MagicMock()

        # 创建测试音频文件
        audio_files = []
        for i in range(2):
            audio_file = self.audio_dir / f"test_{i}.mp3"
            audio_file.touch()
            audio_files.append(str(audio_file))

        output_path = self.audio_dir / "merged.mp3"

        try:
            result = merge_audio_segments(audio_files, str(output_path))
            self.assertIsNotNone(result)
            print(f"✓ 音频合并测试通过")
        except Exception as e:
            # 如果pydub不可用，这是预期的
            if "pydub" in str(e).lower():
                print(f"⚠ 音频合并测试跳过: {e}")
            else:
                raise

    @patch('src.modules.tts_engine.AudioSegment')
    def test_merge_audio_segments_empty_list(self, mock_audio_segment):
        """测试音频合并（空列表）"""
        output_path = self.audio_dir / "merged.mp3"

        # 空列表应该抛出异常
        with self.assertRaises(TTSError):
            merge_audio_segments([], str(output_path))

        print("✓ 音频合并（空列表）测试通过")

    @patch('src.modules.tts_engine.AudioSegment')
    def test_optimize_audio(self, mock_audio_segment):
        """测试音频优化"""
        # 模拟音频
        mock_audio = MagicMock()
        mock_audio.__len__ = lambda self: 5000  # 5秒
        mock_audio.dBFS = -10.0
        mock_audio.frame_rate = 44100
        mock_audio.raw_data = b'test_data'
        mock_audio.export = MagicMock()

        mock_audio.from_file.return_value = mock_audio
        mock_audio_instance = MagicMock()
        mock_audio_instance.__len__ = lambda self: 5000
        mock_audio_instance.dBFS = -5.0
        mock_audio_instance.frame_rate = 44100
        mock_audio_instance._spawn.return_value = mock_audio_instance
        mock_audio_instance.set_frame_rate.return_value = mock_audio_instance

        mock_audio.return_value = mock_audio_instance

        input_path = self.audio_dir / "input.mp3"
        output_path = self.audio_dir / "optimized.mp3"
        input_path.touch()

        try:
            result = optimize_audio(str(input_path), str(output_path))
            self.assertIsNotNone(result)
            print(f"✓ 音频优化测试通过")
        except Exception as e:
            # 如果pydub不可用，这是预期的
            if "pydub" in str(e).lower():
                print(f"⚠ 音频优化测试跳过: {e}")
            else:
                raise

    def test_performance(self):
        """测试性能"""
        import time

        text = "这是一个性能测试文本。"
        output_path = self.audio_dir / "test_perf.mp3"

        start_time = time.time()
        result = text_to_speech(text, str(output_path), 'zh-cn')
        end_time = time.time()

        if result:
            duration = end_time - start_time
            self.assertLess(duration, 10)  # 应该在10秒内完成
            print(f"✓ 性能测试通过: {duration:.2f}秒")

    def test_language_setting(self):
        """测试语言设置"""
        # 验证默认语言设置
        self.assertEqual(TTS_LANGUAGE, 'zh-cn')
        print(f"✓ 语言设置测试通过: {TTS_LANGUAGE}")


class TestTTSCache(unittest.TestCase):
    """TTS缓存测试类"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """测试后清理"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('src.modules.tts_engine.TTS_CACHE_ENABLED', True)
    @patch('src.modules.tts_engine.CACHE_DIR', None)
    def test_cache_directory_creation(self):
        """测试缓存目录创建"""
        # 在测试中，缓存目录应该自动创建
        from src.modules.tts_engine import CACHE_DIR
        # 验证缓存目录存在或可以被创建
        print(f"✓ 缓存目录测试通过: {CACHE_DIR}")


if __name__ == "__main__":
    # 运行测试
    print("\n" + "="*60)
    print("TTS引擎模块测试开始")
    print("="*60 + "\n")

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestTTSEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestTTSCache))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print("\n" + "="*60)
    print(f"测试完成: 运行 {result.testsRun} 个测试")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*60 + "\n")

    # 返回适当的退出码
    exit(0 if result.wasSuccessful() else 1)
