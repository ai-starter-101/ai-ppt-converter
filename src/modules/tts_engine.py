#!/usr/bin/env python3
"""
文本转语音模块 - 将脚本文字转换为中文女声语音

功能:
- 使用gTTS生成中文语音
- 多重备用方案（espeak, 系统TTS）
- 批量处理和并行生成
- 音频后处理和优化

作者: Claude Code
版本: v1.0
"""

import os
import io
import asyncio
import subprocess
import hashlib
from typing import List, Optional, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

try:
    from pydub.effects import normalize
except ImportError:
    normalize = None

from src.utils.logger import get_logger
from src.utils.exceptions import TTSError
from config.settings import config

# 配置常量
TTS_LANGUAGE = config.get('tts.language', 'zh-cn')
TTS_SPEED = config.get('tts.speed', 0.9)
TTS_CACHE_ENABLED = config.get('tts.cache_enabled', True)
CACHE_DIR = Path(config.get('tts.cache_dir', './cache/audio'))
RETRY_ATTEMPTS = config.get('error_handling.retry_attempts', 3)
RETRY_DELAY = config.get('error_handling.retry_delay', 5)
MAX_WORKERS = config.get('performance.max_workers', 4)

# 创建缓存目录
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 设置日志
logger = get_logger(__name__)


def _get_cache_key(text: str, lang: str) -> str:
    """
    生成缓存键

    Args:
        text: 文本内容
        lang: 语言代码

    Returns:
        str: 缓存键（MD5哈希）
    """
    return hashlib.md5(f"{text}_{lang}".encode('utf-8')).hexdigest()


def _get_cache_path(text: str, lang: str) -> Path:
    """
    获取缓存文件路径

    Args:
        text: 文本内容
        lang: 语言代码

    Returns:
        Path: 缓存文件路径
    """
    cache_key = _get_cache_key(text, lang)
    return CACHE_DIR / f"{cache_key}.mp3"


def text_to_speech(text: str, output_path: str, lang: str = TTS_LANGUAGE) -> Optional[str]:
    """
    将文字转换为语音

    Args:
        text: 要转换的文字
        output_path: 输出音频文件路径
        lang: 语言代码（默认: zh-cn）

    Returns:
        Optional[str]: 成功返回音频文件路径，失败返回None

    Raises:
        TTSError: TTS转换失败
    """
    if not text or not text.strip():
        logger.warning("文本为空，跳过TTS转换")
        return None

    text = text.strip()
    output_path = Path(output_path)

    # 清理 {pause} 等标记，这些是控制标记不应该被读出来
    text = _clean_script_markers(text)
    if not text:
        logger.warning("清理后文本为空，跳过TTS转换")
        return None

    # 检查缓存
    if TTS_CACHE_ENABLED:
        cache_key = _get_cache_key(text, lang)
        cache_path = CACHE_DIR / f"{cache_key}.mp3"
        if cache_path.exists():
            logger.debug(f"使用缓存音频: {cache_path}")
            # 复制缓存文件到目标位置
            import shutil
            shutil.copy2(cache_path, output_path)
            return str(output_path)

    # 优先使用 macOS say 命令（本地，无需网络）
    import platform
    if platform.system() == "Darwin":
        say_result = _text_to_speech_say(text, output_path, lang)
        if say_result:
            return say_result

    # 尝试使用 Edge TTS (更自然的语音)
    edge_result = _text_to_speech_edge(text, output_path, lang)
    if edge_result:
        return edge_result

    # 尝试使用 gTTS
    if gTTS is not None:
        try:
            logger.debug(f"使用gTTS转换文本: {text[:50]}...")
            tts = gTTS(text=text, lang=lang, slow=False)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tts.save(str(output_path))

            # 保存到缓存
            if TTS_CACHE_ENABLED:
                cache_path = _get_cache_path(text, lang)
                import shutil
                shutil.copy2(output_path, cache_path)

            logger.info(f"TTS转换成功: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.warning(f"gTTS转换失败: {e}")
            # 继续尝试备用方案
    else:
        logger.warning("gTTS未安装，将使用备用方案")

    # 备用方案：使用系统TTS
    return _text_to_speech_fallback(text, output_path, lang)


def _clean_script_markers(text: str) -> str:
    """
    清理脚本中的控制标记

    Args:
        text: 原始脚本文本

    Returns:
        str: 清理后的文本
    """
    import re

    # 移除所有 {xxx} 格式的标记
    text = re.sub(r'\{[^}]+\}', '', text)

    # 移除多余的空格
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def _text_to_speech_say(text: str, output_path: Path, lang: str) -> Optional[str]:
    """
    使用 macOS say 命令生成语音

    Args:
        text: 文本内容
        output_path: 输出路径
        lang: 语言代码

    Returns:
        Optional[str]: 成功返回音频路径，失败返回None
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # macOS say 命令支持中文语音
    voice = "Ting-Ting"  # 中文女声

    try:
        logger.info(f"使用 macOS say 命令生成语音，语音: {voice}")

        # 先保存为 aiff 格式（say 命令原生支持）
        aiff_path = output_path.with_suffix('.aiff')
        subprocess.run(
            ['say', '-v', voice, '-o', str(aiff_path), text],
            check=True,
            capture_output=True
        )

        # 转换为 mp3
        if AudioSegment is not None:
            audio = AudioSegment.from_file(str(aiff_path))
            audio.export(str(output_path), format="mp3")
            # 删除临时文件
            aiff_path.unlink()
        else:
            # 如果没有 pydub，直接重命名
            import shutil
            shutil.move(str(aiff_path), str(output_path))

        logger.info(f"macOS TTS 转换成功: {output_path}")
        return str(output_path)

    except subprocess.CalledProcessError as e:
        logger.warning(f"macOS say 命令执行失败: {e}")
        return None
    except FileNotFoundError:
        logger.warning("macOS say 命令未找到")
        return None
    except Exception as e:
        logger.warning(f"macOS TTS 转换失败: {e}")
        return None


def _text_to_speech_edge(text: str, output_path: Path, lang: str) -> Optional[str]:
    """
    使用 Edge TTS 生成更自然的语音

    Args:
        text: 文本内容
        output_path: 输出路径
        lang: 语言代码

    Returns:
        Optional[str]: 成功返回音频路径，失败返回None
    """
    try:
        import edge_tts
    except ImportError:
        logger.debug("edge-tts 未安装，跳过")
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 映射语言到 Edge TTS 语音
    voice_map = {
        'zh-cn': 'zh-CN-XiaoxiaoNeural',
        'zh-tw': 'zh-TW-HsiaoYuNeural',
        'en': 'en-US-AriaNeural',
    }

    voice = voice_map.get(lang, voice_map['zh-cn'])

    # Edge TTS 有长度限制，需要分割长文本
    MAX_CHARS = 3000
    if len(text) > MAX_CHARS:
        logger.info(f"文本过长({len(text)}字符)，将分割处理")
        return _text_to_speech_edge_long(text, output_path, voice)

    try:
        logger.info(f"使用 Edge TTS 生成语音，语音: {voice}")

        # 使用新的 edge-tts API
        async def save_audio():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))

        asyncio.run(save_audio())

        logger.info(f"Edge TTS 转换成功: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.warning(f"Edge TTS 转换失败: {e}")
        return None


def _text_to_speech_edge_long(text: str, output_path: Path, voice: str) -> Optional[str]:
    """
    处理长文本的 Edge TTS（分段处理）

    Args:
        text: 文本内容
        output_path: 输出路径
        voice: 语音名称

    Returns:
        Optional[str]: 成功返回音频路径，失败返回None
    """
    try:
        import edge_tts
        from pydub import AudioSegment
    except ImportError as e:
        logger.warning(f"缺少依赖: {e}")
        return None

    # 按句子分割
    import re
    sentences = re.split(r'([。！？.!?])', text)
    segments = []
    current = ""

    for part in sentences:
        if len(current) + len(part) < 2800:  # 留出余量
            current += part
        else:
            if current:
                segments.append(current)
            current = part

    if current:
        segments.append(current)

    audio_segments = []

    for i, segment in enumerate(segments):
        segment = segment.strip()
        if not segment:
            continue

        try:
            segment_path = output_path.with_suffix(f'.part{i}.mp3')

            async def save_segment():
                communicate = edge_tts.Communicate(segment, voice)
                await communicate.save(str(segment_path))

            asyncio.run(save_segment())

            if segment_path.exists():
                audio = AudioSegment.from_mp3(str(segment_path))
                audio_segments.append(audio)
                segment_path.unlink()  # 删除临时文件

        except Exception as e:
            logger.warning(f"处理片段 {i} 失败: {e}")
            continue

    if not audio_segments:
        return None

    # 合并所有片段
    merged = audio_segments[0]
    for audio in audio_segments[1:]:
        # 添加短暂静音
        silence = AudioSegment.silent(duration=200)
        merged = merged + silence + audio

    merged.export(str(output_path), format="mp3")
    logger.info(f"长文本 Edge TTS 转换成功: {output_path}")
    return str(output_path)


def _text_to_speech_fallback(text: str, output_path: Path, lang: str) -> Optional[str]:
    """
    备用TTS方案（使用系统命令）

    Args:
        text: 文本内容
        output_path: 输出路径
        lang: 语言代码

    Returns:
        Optional[str]: 成功返回音频文件路径，失败返回None
    """
    import platform

    system = platform.system()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # macOS: 使用say命令
        if system == "Darwin":
            logger.info("使用macOS say命令进行TTS转换")
            subprocess.run(
                ['say', '-o', str(output_path.with_suffix('.aiff')), text],
                check=True,
                capture_output=True,
                text=True
            )
            # 转换为MP3
            _convert_audio_format(output_path.with_suffix('.aiff'), output_path, 'mp3')
            return str(output_path)

        # Linux: 使用espeak
        elif system == "Linux":
            logger.info("使用espeak进行TTS转换")
            subprocess.run(
                ['espeak', '-s', '150', '-v', 'zh', '-w', str(output_path.with_suffix('.wav')), text],
                check=True,
                capture_output=True,
                text=True
            )
            # 转换为MP3
            _convert_audio_format(output_path.with_suffix('.wav'), output_path, 'mp3')
            return str(output_path)

        # Windows: 使用PowerShell
        elif system == "Windows":
            logger.info("使用Windows PowerShell进行TTS转换")
            ps_script = f"""
            Add-Type -AssemblyName System.Speech;
            $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            $speak.SelectVoice('Microsoft Xiaoxiao');
            $speak.Rate = 0;
            $speak.SpeakToFile('{output_path.with_suffix('.wav')}');
            """
            subprocess.run(
                ['powershell', '-Command', ps_script],
                check=True,
                capture_output=True,
                text=True
            )
            # 转换为MP3
            _convert_audio_format(output_path.with_suffix('.wav'), output_path, 'mp3')
            return str(output_path)

        else:
            logger.error(f"不支持的操作系统: {system}")
            return None

    except FileNotFoundError as e:
        logger.error(f"系统TTS工具未找到: {e}")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"系统TTS执行失败: {e}")
        return None
    except Exception as e:
        logger.error(f"备用TTS方案失败: {e}")
        return None


def _convert_audio_format(input_path: Path, output_path: Path, target_format: str) -> None:
    """
    转换音频格式

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        target_format: 目标格式（如 'mp3'）
    """
    if AudioSegment is None:
        logger.warning("pydub未安装，跳过音频格式转换")
        return

    try:
        audio = AudioSegment.from_file(str(input_path))
        output_path = output_path.with_suffix(f'.{target_format}')
        audio.export(str(output_path), format=target_format)
        logger.debug(f"音频格式转换完成: {output_path}")

        # 删除临时文件
        if input_path.exists():
            input_path.unlink()

    except Exception as e:
        logger.warning(f"音频格式转换失败: {e}")


def text_to_speech_batch(scripts: List[Dict[str, Any]], output_dir: str = "./output/audio") -> List[str]:
    """
    批量转换文字为语音

    Args:
        scripts: 脚本列表，每个字典包含 'page', 'title', 'script' 等键
        output_dir: 输出目录

    Returns:
        List[str]: 生成的音频文件路径列表
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_files = []
    tasks = []

    logger.info(f"开始批量TTS转换，共 {len(scripts)} 个任务")

    # 准备任务列表
    for idx, script_data in enumerate(scripts):
        script_text = script_data.get('script', '') or script_data.get('content', '')
        if not script_text:
            logger.warning(f"第 {idx+1} 个脚本为空，跳过")
            continue

        page_num = script_data.get('page', idx + 1)
        output_path = output_dir / f"audio_{page_num:03d}.mp3"
        tasks.append((script_text, str(output_path), idx + 1))

    # 并行处理
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {
            executor.submit(text_to_speech, text, output_path, TTS_LANGUAGE): (idx, output_path)
            for idx, (text, output_path, page_num) in enumerate(tasks)
        }

        for future in as_completed(future_to_task):
            idx, output_path = future_to_task[future]
            try:
                result = future.result()
                if result:
                    audio_files.append(result)
                    logger.info(f"完成音频生成 {idx+1}/{len(tasks)}: {Path(result).name}")
                else:
                    logger.warning(f"音频生成失败 {idx+1}: {output_path}")
            except Exception as e:
                logger.error(f"批量TTS任务失败 {idx+1}: {e}")

    # 按页码排序
    audio_files.sort(key=lambda x: int(Path(x).stem.split('_')[1]))

    logger.info(f"批量TTS转换完成，成功 {len(audio_files)}/{len(tasks)} 个")

    return audio_files


def merge_audio_segments(audio_files: List[str], output_path: str) -> str:
    """
    合并多个音频片段

    Args:
        audio_files: 音频文件路径列表
        output_path: 输出文件路径

    Returns:
        str: 合并后的音频文件路径

    Raises:
        TTSError: 音频合并失败
    """
    if not audio_files:
        raise TTSError("没有音频文件需要合并")

    if AudioSegment is None:
        raise TTSError("pydub未安装，无法合并音频")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"开始合并 {len(audio_files)} 个音频片段")

    try:
        # 加载所有音频片段
        segments = []
        for audio_file in audio_files:
            audio_path = Path(audio_file)
            if not audio_path.exists():
                logger.warning(f"音频文件不存在: {audio_path}")
                continue

            segment = AudioSegment.from_file(str(audio_path))
            segments.append(segment)
            logger.debug(f"加载音频: {audio_path.name}, 时长: {len(segment)/1000:.2f}秒")

        if not segments:
            raise TTSError("没有有效的音频片段")

        # 合并音频
        merged = segments[0]
        for segment in segments[1:]:
            # 添加短暂停顿（500ms）
            silence = AudioSegment.silent(duration=500)
            merged = merged + silence + segment

        # 导出合并后的音频
        merged.export(str(output_path), format="mp3", bitrate="128k")

        total_duration = len(merged) / 1000
        logger.info(f"音频合并完成: {output_path}, 总时长: {total_duration:.2f}秒")

        return str(output_path)

    except Exception as e:
        logger.error(f"音频合并失败: {e}")
        raise TTSError(f"合并音频时发生错误: {e}")


def optimize_audio(audio_path: str, output_path: str) -> str:
    """
    优化音频质量

    Args:
        audio_path: 输入音频路径
        output_path: 输出音频路径

    Returns:
        str: 优化后的音频文件路径

    Raises:
        TTSError: 音频优化失败
    """
    if AudioSegment is None:
        raise TTSError("pydub未安装，无法优化音频")

    audio_path = Path(audio_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"开始优化音频: {audio_path}")

    try:
        # 加载音频
        audio = AudioSegment.from_file(str(audio_path))

        original_duration = len(audio)
        original_volume = audio.dBFS

        # 标准化音量
        if normalize is not None:
            audio = normalize(audio)
            logger.debug("音量标准化完成")
        else:
            logger.warning("normalize函数不可用，跳过音量标准化")

        # 调整语速（如果需要）
        if TTS_SPEED != 1.0:
            # 语速调整：播放速度 = TTS_SPEED
            # pydub调整语速的方法
            new_sample_rate = int(audio.frame_rate * TTS_SPEED)
            audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})
            audio = audio.set_frame_rate(audio.frame_rate)
            logger.debug(f"语速调整完成: {TTS_SPEED}x")

        # 导出优化后的音频
        audio.export(
            str(output_path),
            format="mp3",
            bitrate="128k",
            parameters=["-q:a", "2"]  # 高质量
        )

        new_duration = len(audio)
        new_volume = audio.dBFS

        logger.info(
            f"音频优化完成:\n"
            f"  输入: {audio_path.name}\n"
            f"  输出: {output_path.name}\n"
            f"  时长变化: {original_duration/1000:.2f}s -> {new_duration/1000:.2f}s\n"
            f"  音量变化: {original_volume:.2f}dBFS -> {new_volume:.2f}dBFS"
        )

        return str(output_path)

    except Exception as e:
        logger.error(f"音频优化失败: {e}")
        raise TTSError(f"优化音频时发生错误: {e}")


if __name__ == "__main__":
    print("TTS引擎模块已加载")
    print(f"配置信息:")
    print(f"  语言: {TTS_LANGUAGE}")
    print(f"  语速: {TTS_SPEED}x")
    print(f"  缓存: {'启用' if TTS_CACHE_ENABLED else '禁用'}")
