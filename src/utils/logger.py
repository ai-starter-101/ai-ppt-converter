#!/usr/bin/env python3
"""
日志工具模块 - 统一的日志系统

功能:
- 支持多级别输出（DEBUG, INFO, WARNING, ERROR）
- 同时输出到控制台和文件
- 按日期轮转日志文件
- 包含模块名称、行号、时间戳

作者: Claude Code
版本: v1.0
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(verbose: bool = False, log_dir: str = "logs") -> logging.Logger:
    """
    设置日志系统

    Args:
        verbose: 是否启用详细输出
        log_dir: 日志文件目录

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 创建logger
    logger = logging.getLogger("ai_ppt_converter")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # 清除已有处理器
    logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（按大小轮转）
    log_file = log_path / f"ai_ppt_converter_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 模块名称

    Returns:
        logging.Logger: 日志记录器实例
    """
    if name is None:
        name = "ai_ppt_converter"
    return logging.getLogger(name)


if __name__ == "__main__":
    # 测试代码
    logger = setup_logger(verbose=True)
    logger.info("日志系统测试")
    logger.debug("调试信息")
    logger.warning("警告信息")
    logger.error("错误信息")
