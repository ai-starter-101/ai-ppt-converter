#!/usr/bin/env python3
"""
视频合成模块 - 将PPT图片和音频合成为教学视频

功能:
- 使用FFmpeg合成视频
- 同步音频和视频轨道
- 支持1080p输出
- 自动计算图片显示时长

作者: Claude Code
版本: v1.0
"""

import os
import subprocess
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

try:
    import ffmpeg
except ImportError:
    ffmpeg = None

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

from src.utils.logger import get_logger
from src.utils.exceptions import VideoCompositionError
from config.settings import config

# 配置常量
VIDEO_RESOLUTION = config.get('video.resolution', '1920x1080')
VIDEO_FRAME_RATE = config.get('video.frame_rate', 30)
VIDEO_CODEC = config.get('video.codec', 'libx264')
VIDEO_BITRATE = config.get('video.bitrate', '5M')
VIDEO_AUDIO_CODEC = config.get('video.audio_codec', 'aac')
VIDEO_AUDIO_BITRATE = config.get('video.audio_bitrate', '128k')
PATH_TEMP_DIR = config.get('paths.temp_dir')

# 设置日志
logger = get_logger(__name__)


def create_video(
    ppt_images: List[str],
    audio_files: List[str],
    output_path: str,
    resolution: str = VIDEO_RESOLUTION,
    frame_rate: int = VIDEO_FRAME_RATE,
    title: str = None
) -> Optional[str]:
    """
    创建教学视频

    Args:
        ppt_images: PPT图片文件路径列表
        audio_files: 音频文件路径列表（每页一个）
        output_path: 输出视频文件路径
        resolution: 视频分辨率（默认: 1920x1080）
        frame_rate: 帧率（默认: 30）
        title: 视频标题（用于元数据）

    Returns:
        Optional[str]: 成功返回视频文件路径，失败返回None

    Raises:
        VideoCompositionError: 视频合成失败
    """
    if ffmpeg is None:
        raise VideoCompositionError("ffmpeg-python未安装，无法合成视频")

    if not ppt_images:
        raise VideoCompositionError("PPT图片列表为空")

    if len(audio_files) != len(ppt_images):
        logger.warning(f"音频文件数量({len(audio_files)})与图片数量({len(ppt_images)})不匹配，将使用平均分配")
        audio_files = audio_files + [audio_files[-1]] * (len(ppt_images) - len(audio_files))
        audio_files = audio_files[:len(ppt_images)]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"开始合成视频: {len(ppt_images)}张图片, {len(audio_files)}个音频")

    try:
        # 计算每张图片的显示时长（基于实际音频时长）
        durations = _calculate_durations_from_audio(audio_files)
        logger.info(f"图片显示时长分配: {durations}")

        # 创建临时目录
        temp_dir = Path(PATH_TEMP_DIR) / "video_segments"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 为每张图片创建视频段
        video_segments = []
        for idx, (image_path, duration, audio_path) in enumerate(zip(ppt_images, durations, audio_files)):
            segment_path = temp_dir / f"segment_{idx:03d}.mp4"

            # 创建视频段（带音频）
            _create_video_segment_with_audio(
                image_path, audio_path, duration, segment_path, resolution, frame_rate
            )
            video_segments.append(segment_path)

            logger.debug(f"创建视频段 {idx+1}/{len(ppt_images)}: {segment_path.name} (时长: {duration:.2f}s)")

        # 合并视频段
        final_video = temp_dir / "final_video.mp4"
        _merge_video_segments(video_segments, final_video)

        # 移动到目标位置
        import shutil
        shutil.move(str(final_video), str(output_path))

        # 添加元数据
        if title:
            add_metadata(str(output_path), title=title, author="AI PPT Converter")

        # 清理临时文件
        _cleanup_temp_files(temp_dir)

        logger.info(f"视频合成完成: {output_path}")

        # 验证输出文件
        if output_path.exists() and output_path.stat().st_size > 0:
            return str(output_path)
        else:
            raise VideoCompositionError("输出视频文件无效")

    except Exception as e:
        logger.error(f"视频合成失败: {e}")
        raise VideoCompositionError(f"视频合成过程中发生错误: {e}")


def _calculate_durations_from_audio(audio_files: List[str]) -> List[float]:
    """
    从音频文件获取每页的时长

    Args:
        audio_files: 音频文件路径列表

    Returns:
        List[float]: 每页的时长（秒）
    """
    durations = []

    for audio_file in audio_files:
        if not Path(audio_file).exists():
            durations.append(3.0)  # 默认3秒
            continue

        try:
            if AudioSegment is not None:
                audio = AudioSegment.from_file(audio_file)
                duration = len(audio) / 1000.0  # 转换为秒
                # 至少1秒，最多30秒
                duration = max(1.0, min(30.0, duration))
            else:
                probe = ffmpeg.probe(audio_file)
                duration = float(probe['streams'][0]['duration'])
                duration = max(1.0, min(30.0, duration))
        except Exception as e:
            logger.warning(f"获取音频时长失败: {e}")
            duration = 3.0  # 默认3秒

        durations.append(duration)

    return durations


def calculate_image_durations(audio_file: str, num_images: int) -> List[float]:
    """
    计算每张图片的显示时长

    Args:
        audio_file: 音频文件路径
        num_images: 图片数量

    Returns:
        List[float]: 每张图片的显示时长（秒）

    Raises:
        VideoCompositionError: 无法获取音频时长
    """
    if num_images <= 0:
        return []

    if AudioSegment is None:
        # 使用ffprobe获取音频时长
        try:
            probe = ffmpeg.probe(audio_file)
            total_duration = float(probe['streams'][0]['duration'])
        except Exception as e:
            logger.error(f"无法获取音频时长: {e}")
            raise VideoCompositionError(f"无法获取音频时长: {e}")
    else:
        # 使用pydub获取音频时长
        audio = AudioSegment.from_file(audio_file)
        total_duration = len(audio) / 1000.0  # 转换为秒

    # 平均分配时长
    avg_duration = total_duration / num_images

    # 为每张图片分配时长（添加微小随机变化使切换更自然）
    import random
    random.seed(42)  # 固定种子确保结果可重现

    durations = []
    remaining = total_duration

    for i in range(num_images):
        if i == num_images - 1:
            # 最后一张图片使用剩余时间
            duration = remaining
        else:
            # 添加±10%的随机变化
            variation = avg_duration * 0.1
            duration = avg_duration + random.uniform(-variation, variation)
            duration = max(duration, 1.0)  # 最少1秒
            remaining -= duration

        durations.append(duration)

    return durations


def _create_video_segment(
    image_path: str,
    duration: float,
    output_path: Path,
    resolution: str,
    frame_rate: int
) -> None:
    """
    创建单个视频段

    Args:
        image_path: 图片路径
        duration: 显示时长（秒）
        output_path: 输出路径
        resolution: 分辨率
        frame_rate: 帧率
    """
    # 解析分辨率
    width, height = map(int, resolution.split('x'))

    (
        ffmpeg
        .input(image_path, loop=1, t=duration)
        .filter('scale', width, height)
        .filter('pad', width, height, '(ow-iw)/2', '(oh-ih)/2')  # 居中显示
        .output(
            str(output_path),
            vcodec=VIDEO_CODEC,
            r=frame_rate,
            bitrate=VIDEO_BITRATE,
            pix_fmt='yuv420p'  # 兼容性
        )
        .overwrite_output()
        .run(quiet=True)
    )


def _create_video_segment_with_audio(
    image_path: str,
    audio_path: str,
    duration: float,
    output_path: Path,
    resolution: str,
    frame_rate: int
) -> None:
    """
    创建单个视频段（带音频）

    Args:
        image_path: 图片路径
        audio_path: 音频路径
        duration: 显示时长（秒）
        output_path: 输出路径
        resolution: 分辨率
        frame_rate: 帧率
    """
    # 解析分辨率
    width, height = map(int, resolution.split('x'))

    # 使用ffmpeg命令直接处理
    import subprocess

    cmd = [
        'ffmpeg',
        '-y',  # 覆盖输出文件
        '-loop', '1',
        '-t', str(duration),
        '-i', str(image_path),
        '-i', str(audio_path),
        '-vf', f'scale={width}:{height},pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
        '-c:v', VIDEO_CODEC,
        '-r', str(frame_rate),
        '-b:v', VIDEO_BITRATE,
        '-pix_fmt', 'yuv420p',
        '-c:a', VIDEO_AUDIO_CODEC,
        '-b:a', VIDEO_AUDIO_BITRATE,
        '-shortest',  # 以音频时长为准
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"ffmpeg错误: {result.stderr}")
        raise VideoCompositionError(f"创建视频段失败: {result.stderr}")


def _merge_video_segments(video_segments: List[Path], output_path: Path) -> None:
    """
    合并视频段

    Args:
        video_segments: 视频段路径列表
        output_path: 输出路径
    """
    # 创建concat文件
    concat_file = output_path.parent / "concat.txt"
    with open(concat_file, 'w') as f:
        for segment in video_segments:
            f.write(f"file '{segment.absolute()}'\n")

    # 合并视频
    (
        ffmpeg
        .input(str(concat_file), format='concat', safe=0)
        .output(str(output_path), vcodec='copy')
        .overwrite_output()
        .run(quiet=True)
    )


def _add_audio_track(video_path: Path, audio_path: str, output_path: Path) -> None:
    """
    添加音频轨道

    Args:
        video_path: 视频路径
        audio_path: 音频路径
        output_path: 输出路径
    """
    # 使用ffmpeg命令直接处理，避免ffmpeg-python API问题
    import subprocess

    cmd = [
        'ffmpeg',
        '-y',  # 覆盖输出文件
        '-i', str(video_path),
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', VIDEO_AUDIO_CODEC,
        '-b:a', VIDEO_AUDIO_BITRATE,
        '-shortest',  # 以较短的音频/视频为准
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"ffmpeg错误: {result.stderr}")
        raise VideoCompositionError(f"添加音频轨道失败: {result.stderr}")


def add_transition_effects(
    input_video: str,
    output_video: str,
    effect_type: str = "fade"
) -> Optional[str]:
    """
    添加视频过渡效果

    Args:
        input_video: 输入视频路径
        output_video: 输出视频路径
        effect_type: 过渡效果类型（fade, slide等）

    Returns:
        Optional[str]: 成功返回视频文件路径，失败返回None

    Raises:
        VideoCompositionError: 添加过渡效果失败
    """
    if ffmpeg is None:
        raise VideoCompositionError("ffmpeg-python未安装，无法添加过渡效果")

    input_path = Path(input_video)
    output_path = Path(output_video)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"添加过渡效果: {effect_type}")

    try:
        if effect_type == "fade":
            # 淡入淡出效果
            (
                ffmpeg
                .input(str(input_path))
                .filter('fade', type='in', start_time=0, duration=0.5)
                .filter('fade', type='out', start_time=2, duration=0.5)
                .output(
                    str(output_path),
                    vcodec=VIDEO_CODEC,
                    acodec=VIDEO_AUDIO_CODEC
                )
                .overwrite_output()
                .run(quiet=True)
            )

        elif effect_type == "slide":
            # 滑动效果（简化实现）
            (
                ffmpeg
                .input(str(input_path))
                .filter('slide', slide=0, direction='right', duration=1)
                .output(
                    str(output_path),
                    vcodec=VIDEO_CODEC,
                    acodec=VIDEO_AUDIO_CODEC
                )
                .overwrite_output()
                .run(quiet=True)
            )

        else:
            logger.warning(f"未知的过渡效果类型: {effect_type}")
            # 如果效果类型未知，直接复制文件
            import shutil
            shutil.copy2(str(input_path), str(output_path))

        logger.info(f"过渡效果添加完成: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"添加过渡效果失败: {e}")
        raise VideoCompositionError(f"添加过渡效果失败: {e}")


def add_metadata(
    video_path: str,
    title: str = None,
    author: str = "AI PPT Converter",
    description: str = None,
    creation_time: str = None
) -> bool:
    """
    添加视频元数据

    Args:
        video_path: 视频文件路径
        title: 视频标题
        author: 作者
        description: 描述
        creation_time: 创建时间（ISO格式）

    Returns:
        bool: 成功返回True，失败返回False

    Raises:
        VideoCompositionError: 添加元数据失败
    """
    if ffmpeg is None:
        raise VideoCompositionError("ffmpeg-python未安装，无法添加元数据")

    video_path = Path(video_path)

    if not video_path.exists():
        raise VideoCompositionError(f"视频文件不存在: {video_path}")

    logger.info(f"添加视频元数据: {video_path.name}")

    try:
        # 构建metadata参数
        metadata = []
        if title:
            metadata.extend(['-metadata', f'title={title}'])
        if author:
            metadata.extend(['-metadata', f'artist={author}'])
        if description:
            metadata.extend(['-metadata', f'comment={description}'])
        if creation_time:
            metadata.extend(['-metadata', f'creation_time={creation_time}'])
        else:
            # 使用当前时间
            now = datetime.now().isoformat()
            metadata.extend(['-metadata', f'creation_time={now}'])

        # 使用ffmpeg添加元数据
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            *metadata,
            '-c', 'copy',  # 复制流不重新编码
            str(video_path.parent / f"{video_path.stem}_temp{video_path.suffix}")
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # 替换原文件
            import shutil
            temp_file = video_path.parent / f"{video_path.stem}_temp{video_path.suffix}"
            shutil.move(str(temp_file), str(video_path))
            logger.info(f"元数据添加成功: {video_path}")
            return True
        else:
            logger.error(f"ffmpeg添加元数据失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"添加元数据失败: {e}")
        raise VideoCompositionError(f"添加元数据失败: {e}")


def _cleanup_temp_files(temp_dir: Path) -> None:
    """
    清理临时文件

    Args:
        temp_dir: 临时目录路径
    """
    try:
        import shutil
        shutil.rmtree(temp_dir)
        logger.debug(f"清理临时目录: {temp_dir}")
    except Exception as e:
        logger.warning(f"清理临时目录失败: {e}")


def get_video_info(video_path: str) -> Dict[str, Any]:
    """
    获取视频信息

    Args:
        video_path: 视频文件路径

    Returns:
        Dict[str, Any]: 视频信息字典

    Raises:
        VideoCompositionError: 获取视频信息失败
    """
    if ffmpeg is None:
        raise VideoCompositionError("ffmpeg-python未安装，无法获取视频信息")

    try:
        probe = ffmpeg.probe(video_path)

        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

        info = {
            'duration': float(probe['format']['duration']),
            'size': int(probe['format']['size']),
            'bit_rate': int(probe['format']['bit_rate']),
            'video': {
                'codec': video_stream['codec_name'] if video_stream else None,
                'resolution': f"{video_stream['width']}x{video_stream['height']}" if video_stream else None,
                'fps': eval(video_stream['r_frame_rate']) if video_stream else None,
            },
            'audio': {
                'codec': audio_stream['codec_name'] if audio_stream else None,
                'sample_rate': audio_stream['sample_rate'] if audio_stream else None,
                'channels': audio_stream['channels'] if audio_stream else None,
            }
        }

        return info

    except Exception as e:
        logger.error(f"获取视频信息失败: {e}")
        raise VideoCompositionError(f"获取视频信息失败: {e}")


if __name__ == "__main__":
    print("视频合成模块已加载")
    print(f"配置信息:")
    print(f"  分辨率: {VIDEO_RESOLUTION}")
    print(f"  帧率: {VIDEO_FRAME_RATE}fps")
    print(f"  编码: {VIDEO_CODEC}")
    print(f"  码率: {VIDEO_BITRATE}")
