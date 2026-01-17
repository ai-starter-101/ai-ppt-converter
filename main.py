#!/usr/bin/env python3
"""
自动化教学课程录制系统 - 主程序入口

Usage:
    python main.py input.pptx -o output.mp4
    python main.py --batch --input-dir ./ppt_files --output-dir ./videos
"""

import argparse
import sys
import signal
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm

# Import all modules
from src.modules.ppt_parser import extract_text_from_ppt, convert_ppt_to_images
from src.modules.script_generator_natural import generate_natural_script
from src.modules.tts_engine import text_to_speech_batch
from src.modules.video_composer import create_video
from src.utils.logger import setup_logger, get_logger
from config.settings import config

# Global variables for signal handling
interrupted = False
logger = None


def signal_handler(signum, frame):
    """信号处理器 - 优雅退出"""
    global interrupted
    interrupted = True
    if logger:
        logger.warning("收到中断信号，正在优雅退出...")
    print("\n正在清理临时文件并退出...")
    sys.exit(1)


def setup_signal_handlers():
    """设置信号处理器"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def validate_input_file(ppt_path: str) -> bool:
    """
    验证输入文件

    Args:
        ppt_path: PPT文件路径

    Returns:
        bool: 文件是否存在且为PPT格式
    """
    path = Path(ppt_path)
    if not path.exists():
        logger.error(f"文件不存在: {ppt_path}")
        return False

    if not path.suffix.lower() in ['.ppt', '.pptx']:
        logger.error(f"不支持的文件格式: {path.suffix}")
        return False

    return True


def process_single_ppt(
    ppt_path: str,
    output_path: str,
    verbose: bool = False,
    keep_temp: bool = False
) -> bool:
    """
    处理单个PPT文件

    Args:
        ppt_path: PPT文件路径
        output_path: 输出视频路径
        verbose: 是否显示详细日志
        keep_temp: 是否保留临时文件

    Returns:
        bool: 处理是否成功
    """
    global interrupted, logger

    # 如果logger未初始化，使用默认logger
    if logger is None:
        from src.utils.logger import setup_logger
        logger = setup_logger(verbose=verbose)

    # 设置进度条
    progress_steps = [
        "解析PPT文件",
        "生成脚本",
        "转换语音",
        "合成视频"
    ]

    with tqdm(total=len(progress_steps), desc="处理进度") as pbar:
        try:
            # 步骤1: 解析PPT
            if interrupted:
                return False
            pbar.set_description(progress_steps[0])
            logger.info(f"开始解析PPT: {ppt_path}")
            slides_data = extract_text_from_ppt(ppt_path)
            logger.info(f"成功解析 {len(slides_data)} 张幻灯片")
            pbar.update(1)

            # 步骤2: 转换PPT为图片
            if interrupted:
                return False
            logger.info("转换PPT为图片...")
            temp_dir = Path("./tmp") / f"ppt_{int(time.time())}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 从PPT中提取图片
            ppt_images = convert_ppt_to_images(ppt_path, str(temp_dir))
            logger.info(f"生成 {len(ppt_images)} 张图片")
            pbar.update(1)

            # 步骤3: 生成脚本
            if interrupted:
                return False
            pbar.set_description(progress_steps[1])
            logger.info("生成教学脚本...")
            course_name = Path(ppt_path).stem
            scripts = generate_natural_script(slides_data, course_name)
            logger.info(f"生成 {len(scripts)} 个脚本片段")
            pbar.update(1)

            # 步骤4: 文本转语音
            if interrupted:
                return False
            pbar.set_description(progress_steps[2])
            logger.info("转换文本为语音...")
            audio_dir = temp_dir / "audio"
            audio_files = text_to_speech_batch(scripts, str(audio_dir))
            logger.info(f"生成 {len(audio_files)} 个音频文件")
            pbar.update(1)

            # 步骤5: 合成视频（每页音频时长独立，确保同步）
            if interrupted:
                return False
            pbar.set_description(progress_steps[3])
            logger.info("合成最终视频...")
            video_result = create_video(
                ppt_images=ppt_images,
                audio_files=audio_files,
                output_path=output_path,
                title=course_name
            )

            if not video_result:
                logger.error("视频合成失败")
                return False

            logger.info(f"视频合成完成: {output_path}")
            pbar.update(1)

            # 清理临时文件
            if not keep_temp:
                logger.info("清理临时文件...")
                import shutil
                shutil.rmtree(temp_dir)
                logger.info("临时文件清理完成")

            return True

        except Exception as e:
            logger.error(f"处理失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


def main():
    """主函数 - 编排整个PPT转视频流程"""
    global logger

    # 设置信号处理
    setup_signal_handlers()

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='自动化教学课程录制系统 - 将PPT转换为教学视频',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.pptx                          # 基本转换
  %(prog)s input.pptx -o output.mp4           # 指定输出文件
  %(prog)s input.pptx -v                      # 详细日志
  %(prog)s input.pptx --keep-temp             # 保留临时文件
        """
    )
    parser.add_argument('ppt_path', nargs='?', help='PPT文件路径')
    parser.add_argument(
        '-o', '--output',
        default='output.mp4',
        help='输出视频路径 (默认: output.mp4)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细日志输出'
    )
    parser.add_argument(
        '--keep-temp',
        action='store_true',
        help='保留临时文件（用于调试）'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    args = parser.parse_args()

    # 设置日志
    logger = setup_logger(verbose=args.verbose)
    logger.info("="*60)
    logger.info("自动化教学课程录制系统启动")
    logger.info("="*60)

    # 验证输入
    if not args.ppt_path:
        parser.print_help()
        return 1

    if not validate_input_file(args.ppt_path):
        return 1

    # 开始处理
    logger.info(f"输入文件: {args.ppt_path}")
    logger.info(f"输出文件: {args.output}")

    start_time = time.time()

    try:
        success = process_single_ppt(
            args.ppt_path,
            args.output,
            verbose=args.verbose,
            keep_temp=args.keep_temp
        )

        end_time = time.time()
        duration = end_time - start_time

        logger.info("="*60)
        if success:
            logger.info(f"处理完成! 用时: {duration:.2f}秒")
            logger.info(f"输出文件: {args.output}")
            logger.info("="*60)
            return 0
        else:
            logger.error("处理失败!")
            logger.error(f"用时: {duration:.2f}秒")
            logger.error("="*60)
            return 1

    except KeyboardInterrupt:
        logger.warning("用户中断操作")
        return 1
    except Exception as e:
        logger.error(f"未处理的异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
