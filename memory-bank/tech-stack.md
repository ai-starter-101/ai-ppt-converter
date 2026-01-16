# 自动化教学课程录制系统 - 低成本技术栈方案

## 设计原则

### 1. 核心原则
- **零成本/最低成本**: 优先使用开源和免费组件
- **极简架构**: 最小可行产品，易于理解和维护
- **健壮性**: 完善的错误处理和恢复机制
- **可替代性**: 关键组件有多个备选方案

### 2. 实施优先级
```
Phase 1: 基础功能（最低成本）
Phase 2: 质量提升（适度优化）
Phase 3: 高级功能（可选扩展）
```

## 技术栈详细方案

### Phase 1: 基础功能实现（成本：$0/月）

#### 1.1 PPT解析模块
**技术选择**: `python-pptx` + `python-pptx2json`
```python
# 核心依赖
python-pptx==0.6.21        # PPT解析（开源免费）
```

**实现方式**:
```python
from pptx import Presentation
import json

def extract_text_from_ppt(ppt_path):
    """提取PPT文字内容"""
    prs = Presentation(ppt_path)
    slides_data = []

    for i, slide in enumerate(prs.slides):
        slide_text = {
            'page': i + 1,
            'title': '',
            'content': []
        }

        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text = shape.text.strip()
                if text:
                    # 判断是否为标题（第一个或较大的文本）
                    if not slide_text['title'] and len(text) < 100:
                        slide_text['title'] = text
                    else:
                        slide_text['content'].append(text)

        slides_data.append(slide_text)

    return slides_data
```

**成本**: $0（开源免费）
**优点**: 轻量级，依赖少，社区支持好
**缺点**: 复杂布局支持有限

#### 1.2 讲解脚本生成模块
**技术选择**: 规则模板 + 可选AI增强
```python
# 核心依赖
# 无需额外依赖（使用规则模板）
# 可选：openai==0.28（如果使用API）
```

**方案A: 规则模板生成（推荐-零成本）**
```python
def generate_script_from_text(slides_data):
    """使用规则模板生成讲解脚本"""
    scripts = []

    for slide in slides_data:
        script = {
            'page': slide['page'],
            'title': slide['title'],
            'content': slide['content']
        }

        # 生成讲解文本
        if slide['title'] and slide['content']:
            # 结构化内容
            explanation = f"现在我们来学习第{slide['page']}页的内容。"
            explanation += f"这一页的标题是：{slide['title']}。"
            explanation += " ".join(slide['content'])
            explanation += "请大家注意理解这个知识点。"
        elif slide['title']:
            explanation = f"接下来看第{slide['page']}页：{slide['title']}。"
        elif slide['content']:
            explanation = " ".join(slide['content'])

        script['explanation'] = explanation
        scripts.append(script)

    return scripts
```

**方案B: 本地开源模型（Ollama）**
```bash
# 安装Ollama
brew install ollama  # macOS
# 或
curl -fsSL https://ollama.ai/install.sh | sh  # Linux

# 下载模型
ollama pull llama2
ollama pull chatglm3
```

```python
# 可选增强模块
def generate_script_with_ai(slide_text, model="local"):
    """使用AI生成更自然的讲解"""
    if model == "local":
        # 使用Ollama本地模型
        import requests
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",
                "prompt": f"请将以下PPT内容转换为教学讲解脚本：{slide_text}",
                "stream": False
            }
        )
        return response.json()['response']
    else:
        # 回退到规则模板
        return generate_script_from_template(slide_text)
```

**成本**: $0（规则模板）或一次性本地部署
**优点**: 无API成本，响应速度快，可离线运行
**缺点**: 讲解自然度略低于大模型

#### 1.3 语音合成模块
**技术选择**: `gTTS` (Google Text-to-Speech)
```python
# 核心依赖
gtts==2.4.0                 # Google TTS（免费但有配额限制）
pydub==0.25.1              # 音频处理
```

**实现方式**:
```python
from gtts import gTTS
import io
from pydub import AudioSegment
import tempfile

def text_to_speech(text, lang='zh-cn', output_path=None):
    """将文字转换为语音"""
    try:
        # 使用Google TTS
        tts = gTTS(text=text, lang=lang, slow=False)

        if output_path:
            tts.save(output_path)
            return output_path
        else:
            # 保存到内存
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp

    except Exception as e:
        print(f"TTS错误: {e}")
        # 备用方案：使用espeak
        return text_to_speech_espeak(text, output_path)

def text_to_speech_espeak(text, output_path):
    """备用方案：使用espeak"""
    import subprocess
    try:
        subprocess.run([
            'espeak', '-s', '150', '-v', 'zh', '-w', output_path, text
        ], check=True, capture_output=True)
        return output_path
    except:
        print("错误：无法生成语音")
        return None
```

**备用方案**: 系统自带TTS
```python
# macOS: 使用内置say命令
def tts_macos(text, output_path):
    import subprocess
    subprocess.run(['say', '-o', output_path, text])

# Linux: 使用espeak
def tts_linux(text, output_path):
    import subprocess
    subprocess.run(['espeak', '-s', '150', '-w', output_path, text])
```

**成本**: $0（有免费配额）或$0（使用系统TTS）
**优点**: 免费，易于使用
**缺点**: 需要网络（gTTS），音质一般

#### 1.4 视频合成模块
**技术选择**: `FFmpeg`
```python
# 核心依赖
ffmpeg-python==0.2.0       # FFmpeg Python绑定
Pillow==10.0.0              # 图片处理
```

**实现方式**:
```python
import ffmpeg
from PIL import Image
import tempfile
import os

def create_video_from_ppt_and_audio(ppt_path, audio_segments, output_path):
    """将PPT和语音合成为视频"""

    # 1. 转换PPT为图片
    slide_images = convert_ppt_to_images(ppt_path)

    # 2. 合并音频
    combined_audio = merge_audio_segments(audio_segments)

    # 3. 为每张图片分配时长
    video_segments = []
    total_duration = len(combined_audio) / 1000  # 转换为秒

    for i, (image_path, duration) in enumerate(zip(slide_images, audio_segments)):
        temp_video = f"/tmp/segment_{i}.mp4"
        (
            ffmpeg
            .input(image_path, loop=1, t=duration)
            .output(temp_video, vcodec='libx264', r=30, s='1920x1080')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        video_segments.append(temp_video)

    # 4. 合并视频
    concat_list = "/tmp/concat.txt"
    with open(concat_list, 'w') as f:
        for segment in video_segments:
            f.write(f"file '{segment}'\n")

    # 5. 添加音频轨道
    (
        ffmpeg
        .input(concat_list, format='concat', safe=0)
        .input(combined_audio)
        .output(output_path, vcodec='copy', acodec='aac', strict='experimental')
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )

    return output_path

def convert_ppt_to_images(ppt_path):
    """将PPT转换为图片（需要手动或使用库）"""
    # 方法1: 使用LibreOffice命令行转换（开源免费）
    import subprocess

    # 转换为PDF
    pdf_path = ppt_path.replace('.pptx', '.pdf')
    subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'pdf',
        '--outdir', '/tmp', ppt_path
    ], check=True)

    # 转换PDF为图片
    images = []
    (
        ffmpeg
        .input(pdf_path)
        .output('/tmp/slide_%03d.png', vf='fps=1')
        .run(capture_stdout=True)
    )

    # 收集图片路径
    for i in range(1, 100):  # 假设最多99页
        img_path = f'/tmp/slide_{i:03d}.png'
        if os.path.exists(img_path):
            images.append(img_path)
        else:
            break

    return images
```

**系统要求**:
```bash
# 安装FFmpeg
brew install ffmpeg  # macOS
# 或
sudo apt-get install ffmpeg  # Ubuntu/Debian

# 安装LibreOffice（PPT转PDF）
brew install --cask libreoffice  # macOS
# 或
sudo apt-get install libreoffice  # Ubuntu/Debian
```

**成本**: $0（开源免费）
**优点**: 行业标准，功能强大，完全免费
**缺点**: 学习曲线陡峭

### Phase 1 完整实现

#### 核心文件结构
```
ppt-to-video/
├── requirements.txt
├── config.py
├── ppt_parser.py
├── script_generator.py
├── tts_engine.py
├── video_composer.py
├── main.py
└── utils/
    ├── __init__.py
    ├── logger.py
    └── exceptions.py
```

#### requirements.txt
```
python-pptx==0.6.21
gtts==2.4.0
pydub==0.25.1
ffmpeg-python==0.2.0
Pillow==10.0.0
colorama==0.4.6
tqdm==4.66.1
```

#### 主程序 main.py
```python
#!/usr/bin/env python3
"""自动化教学课程录制系统 - 主程序"""

import argparse
import logging
from pathlib import Path
from ppt_parser import extract_text_from_ppt
from script_generator import generate_script
from tts_engine import text_to_speech_batch
from video_composer import create_video
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description='PPT转视频工具')
    parser.add_argument('ppt_path', help='PPT文件路径')
    parser.add_argument('-o', '--output', default='output.mp4', help='输出视频路径')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    args = parser.parse_args()

    # 设置日志
    logger = setup_logger(args.verbose)

    try:
        logger.info(f"开始处理PPT文件: {args.ppt_path}")

        # 步骤1: 解析PPT
        logger.info("步骤1: 提取PPT文字内容")
        slides_data = extract_text_from_ppt(args.ppt_path)
        logger.info(f"共提取 {len(slides_data)} 页内容")

        # 步骤2: 生成脚本
        logger.info("步骤2: 生成讲解脚本")
        scripts = generate_script(slides_data)

        # 步骤3: 转换为语音
        logger.info("步骤3: 生成语音文件")
        audio_files = text_to_speech_batch(scripts)

        # 步骤4: 合成视频
        logger.info("步骤4: 合成最终视频")
        create_video(args.ppt_path, audio_files, args.output)

        logger.info(f"完成！视频保存到: {args.output}")

    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise

if __name__ == "__main__":
    main()
```

#### 使用方法
```bash
# 安装依赖
pip install -r requirements.txt

# 安装系统依赖
brew install ffmpeg libreoffice  # macOS
# 或
sudo apt-get install ffmpeg libreoffice  # Ubuntu/Debian

# 运行程序
python main.py input.pptx -o output.mp4
```

### Phase 2: 质量提升（成本：$0-50/月）

#### 2.1 增强语音合成
**升级方案**: Coqui TTS（开源高质量TTS）
```bash
pip install TTS
```

```python
from TTS.api import TTS

# 使用预训练的中文模型
tts = TTS("tts_models/zh-CN/wavlm/tts_wavlm_base_plus_zh")

def text_to_speech_enhanced(text, output_path):
    """使用Coqui TTS生成高质量语音"""
    tts.tts_to_file(text=text, file_path=output_path)

# 使用示例
tts.tts_to_file("你好，这是测试。", "test.wav")
```

**成本**: $0（本地运行）
**优点**: 音质好，可本地运行，无API限制
**缺点**: 需要GPU加速（可选）

#### 2.2 改进脚本生成
**升级方案**: 轻量级本地模型
```python
# 安装轻量级模型
pip install transformers torch

from transformers import pipeline

def generate_script_enhanced(slides_data):
    """使用轻量级模型生成更自然的脚本"""
    generator = pipeline('text-generation', model='gpt2')

    scripts = []
    for slide in slides_data:
        prompt = f"教学讲解：{slide['title']} {slide['content']}"
        script = generator(prompt, max_length=200, num_return_sequences=1)[0]['generated_text']
        scripts.append(script)

    return scripts
```

**成本**: $0（本地模型）
**优点**: 无API调用成本，可离线运行
**缺点**: 占用磁盘空间（~1GB）

### Phase 3: 高级功能（可选）

#### 3.1 Web界面
```python
# 使用Streamlit构建简单的Web UI
streamlit==1.28.0

# app.py
import streamlit as st
from main import main as process_ppt

st.title("PPT转视频工具")

uploaded_file = st.file_uploader("上传PPT文件", type=['pptx'])
output_name = st.text_input("输出文件名", "output.mp4")

if uploaded_file and st.button("开始转换"):
    with st.spinner("处理中..."):
        # 调用主程序
        process_ppt(uploaded_file.name, output_name)
        st.success("完成！")

# 运行
streamlit run app.py
```

#### 3.2 批量处理
```python
def batch_process(ppt_folder, output_folder):
    """批量处理多个PPT文件"""
    for ppt_file in Path(ppt_folder).glob("*.pptx"):
        output_file = Path(output_folder) / f"{ppt_file.stem}.mp4"
        main(str(ppt_file), str(output_file))
```

## 备选技术栈（完全离线）

### 完全离线方案
如果需要完全离线运行（无网络依赖）：

```python
# requirements-minimal.txt
python-pptx==0.6.21
pydub==0.25.1
ffmpeg-python==0.2.0
Pillow==10.0.0
```

**语音合成**:
- 使用系统TTS（espeak/say）
- 或预录制的语音片段拼接

**脚本生成**:
- 完全基于规则模板
- 无AI依赖

**成本**: $0（无需网络）

## 成本对比

| 方案 | 开发成本 | 运营成本 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **Phase 1 (推荐)** | $0 | $0/月 | 零成本，快速实现 | 功能基础 |
| **Phase 2** | $0 | $0-50/月 | 质量提升 | 资源占用高 |
| **完全离线** | $0 | $0/月 | 无网络依赖 | 灵活性差 |

## 推荐方案：Phase 1 + 关键增强

### 最终推荐技术栈
```
✅ PPT解析: python-pptx
✅ 脚本生成: 规则模板 + 可选Ollama
✅ 语音合成: gTTS + espeak备用
✅ 视频合成: FFmpeg
✅ UI: 命令行 + 可选Streamlit
✅ 部署: Docker（可选）
```

### 优势
1. **零成本**: 无API费用
2. **高可用**: 多重备用方案
3. **易部署**: 纯Python，依赖少
4. **可扩展**: 模块化设计

### 预计开发时间
- **MVP版本**: 1-2周
- **完整功能**: 3-4周
- **优化增强**: 2-3周

---

**文档版本**: v1.0
**创建日期**: 2026-01-16
**作者**: Claude Code