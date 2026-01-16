#!/usr/bin/env python3
"""
自定义异常模块 - 定义项目特定的异常类型

作者: Claude Code
版本: v1.0
"""


class AIPPTConverterError(Exception):
    """基础异常类 - 所有自定义异常的父类"""
    pass


class PPTParseError(AIPPTConverterError):
    """PPT解析错误"""
    def __init__(self, message: str, ppt_file: str = None):
        self.ppt_file = ppt_file
        super().__init__(f"PPT解析失败: {message}")


class ScriptGenerationError(AIPPTConverterError):
    """脚本生成错误"""
    def __init__(self, message: str, slide_number: int = None):
        self.slide_number = slide_number
        super().__init__(f"脚本生成失败: {message}")


class TTSError(AIPPTConverterError):
    """文本转语音错误"""
    def __init__(self, message: str, text_length: int = None):
        self.text_length = text_length
        super().__init__(f"TTS转换失败: {message}")


class VideoCompositionError(AIPPTConverterError):
    """视频合成错误"""
    def __init__(self, message: str, output_file: str = None):
        self.output_file = output_file
        super().__init__(f"视频合成失败: {message}")


class ConfigurationError(AIPPTConverterError):
    """配置错误"""
    pass


class FileNotFoundError(AIPPTConverterError):
    """文件未找到错误"""
    def __init__(self, file_path: str):
        super().__init__(f"文件未找到: {file_path}")


class UnsupportedFormatError(AIPPTConverterError):
    """不支持的格式错误"""
    def __init__(self, file_path: str, format_type: str = None):
        self.file_path = file_path
        self.format_type = format_type
        super().__init__(f"不支持的文件格式: {file_path}")


class AudioProcessingError(AIPPTConverterError):
    """音频处理错误"""
    pass


class TemporaryFileError(AIPPTConverterError):
    """临时文件错误"""
    pass


if __name__ == "__main__":
    # 测试代码
    try:
        raise PPTParseError("无法解析PPT文件", "test.pptx")
    except PPTParseError as e:
        print(f"捕获异常: {e}")
        print(f"PPT文件: {e.ppt_file}")
