# 自动化教学课程录制系统 - 配置管理

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """配置管理类，支持从YAML文件和环境变量加载配置"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为当前目录下的 default.yaml
        """
        if config_path is None:
            # 获取当前文件的父目录的父目录（项目根目录）
            current_dir = Path(__file__).parent
            project_root = current_dir.parent
            config_path = project_root / "config" / "default.yaml"

        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        从YAML文件加载配置

        Returns:
            配置字典
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 转换为绝对路径
        config = self._resolve_paths(config)

        # 环境变量覆盖
        config = self._apply_env_overrides(config)

        return config

    def _resolve_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析配置文件中的路径为绝对路径

        Args:
            config: 配置字典

        Returns:
            解析后的配置字典
        """
        project_root = Path(__file__).parent.parent

        paths_to_resolve = [
            'paths.input_dir',
            'paths.output_dir',
            'paths.temp_dir',
            'paths.logs_dir',
            'paths.test_ppts_dir',
            'tts.cache_dir',
            'script.template_file'
        ]

        for path_key in paths_to_resolve:
            keys = path_key.split('.')
            current = config
            for key in keys[:-1]:
                current = current.get(key, {})
            if keys[-1] in current:
                path_value = current[keys[-1]]
                if isinstance(path_value, str):
                    current[keys[-1]] = str(project_root / path_value)

        return config

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用环境变量覆盖配置

        Args:
            config: 原始配置字典

        Returns:
            覆盖后的配置字典
        """
        # 环境变量映射
        env_mappings = {
            'TTS_LANGUAGE': ('tts', 'language'),
            'TTS_SPEED': ('tts', 'speed'),
            'TTS_VOLUME': ('tts', 'volume'),
            'VIDEO_RESOLUTION': ('video', 'resolution'),
            'VIDEO_FRAME_RATE': ('video', 'frame_rate'),
            'VIDEO_BITRATE': ('video', 'bitrate'),
            'LOG_LEVEL': ('logging', 'level'),
            'PERFORMANCE_MAX_WORKERS': ('performance', 'max_workers'),
            'PERFORMANCE_MEMORY_LIMIT_MB': ('performance', 'memory_limit_mb'),
            'ERROR_RETRY_ATTEMPTS': ('error_handling', 'retry_attempts'),
            'ERROR_RETRY_DELAY': ('error_handling', 'retry_delay'),
        }

        for env_key, (config_path, config_key) in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # 类型转换
                if env_key in ['TTS_SPEED', 'TTS_VOLUME', 'VIDEO_FRAME_RATE',
                              'PERFORMANCE_MAX_WORKERS', 'PERFORMANCE_MEMORY_LIMIT_MB',
                              'ERROR_RETRY_ATTEMPTS', 'ERROR_RETRY_DELAY']:
                    try:
                        env_value = float(env_value) if '.' in env_value else int(env_value)
                    except ValueError:
                        pass
                elif env_key == 'VIDEO_BITRATE':
                    # 保持字符串格式 (如 "5M")
                    pass

                # 设置配置值
                if config_path in config and config_key in config[config_path]:
                    config[config_path][config_key] = env_value

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        支持点号分隔的嵌套键，如 'tts.language'

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        current = self._config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.get(key) is not None

    def to_dict(self) -> Dict[str, Any]:
        """
        获取完整配置字典

        Returns:
            配置字典的副本
        """
        return self._config.copy()

    def reload(self) -> None:
        """重新加载配置文件"""
        self._config = self._load_config()


# 创建全局配置实例
config = Config()


# 便捷访问方法
def get_config() -> Config:
    """获取全局配置实例"""
    return config


def reload_config() -> None:
    """重新加载配置"""
    global config
    config.reload()


# 导出常用配置常量
TTS_LANGUAGE = config.get('tts.language', 'zh-cn')
TTS_SPEED = config.get('tts.speed', 0.9)
TTS_VOLUME = config.get('tts.volume', 1.0)
TTS_CACHE_ENABLED = config.get('tts.cache_enabled', True)

VIDEO_RESOLUTION = config.get('video.resolution', '1920x1080')
VIDEO_FRAME_RATE = config.get('video.frame_rate', 30)
VIDEO_CODEC = config.get('video.codec', 'libx264')
VIDEO_BITRATE = config.get('video.bitrate', '5M')
VIDEO_AUDIO_CODEC = config.get('video.audio_codec', 'aac')
VIDEO_AUDIO_BITRATE = config.get('video.audio_bitrate', '128k')

SCRIPT_MODE = config.get('script.mode', 'template')
SCRIPT_TEMPLATE_FILE = config.get('script.template_file')
SCRIPT_AI_ENABLED = config.get('script.ai_enabled', False)

LOG_LEVEL = config.get('logging.level', 'INFO')
LOG_CONSOLE_OUTPUT = config.get('logging.console_output', True)
LOG_FILE_OUTPUT = config.get('logging.file_output', True)

PERFORMANCE_MAX_WORKERS = config.get('performance.max_workers', 4)
PERFORMANCE_BATCH_SIZE = config.get('performance.batch_size', 5)
PERFORMANCE_MEMORY_LIMIT_MB = config.get('performance.memory_limit_mb', 2048)

ERROR_RETRY_ATTEMPTS = config.get('error_handling.retry_attempts', 3)
ERROR_RETRY_DELAY = config.get('error_handling.retry_delay', 5)
ERROR_FALLBACK_ENABLED = config.get('error_handling.fallback_enabled', True)

# 路径配置
PATH_INPUT_DIR = config.get('paths.input_dir')
PATH_OUTPUT_DIR = config.get('paths.output_dir')
PATH_TEMP_DIR = config.get('paths.temp_dir')
PATH_LOGS_DIR = config.get('paths.logs_dir')
PATH_TEST_PPTs_DIR = config.get('paths.test_ppts_dir')
