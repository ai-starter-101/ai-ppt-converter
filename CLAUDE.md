# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

此代码库包含一个**自动化教学课程录制系统**，用于将 PPTX 文件转换为视频。该系统通过提取 PowerPoint 幻灯片内容、生成解说脚本、文本转语音，并将所有内容合成为最终视频，实现教学视频创建过程的自动化。

**当前状态**：规划/设计阶段 - 尚无源代码，仅有文档（tech-stack.md 和 product-design-document.md）。

## 技术栈（规划中）

### 核心技术
- **Python 3.9+**：主要开发语言
- **python-pptx**：PPT 文件解析
- **FFmpeg**：视频处理和合成
- **gTTS** / **Coqui TTS**：文本转语音
- **Streamlit**：Web 界面（可选）

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     流程概览                                  │
├─────────────────────────────────────────────────────────────┤
│  PPTX → PPT解析器 → 脚本生成器 → TTS → 视频合成器             │
│   ↓          ↓            ↓            ↓         ↓         │
│  文本    结构化数据    教学脚本      音频     最终视频       │
└─────────────────────────────────────────────────────────────┘
```

### 模块划分

1. **PPT解析器** (`ppt_parser.py`)
   - 从 PPTX 文件中提取文本、图片和布局
   - 使用 `python-pptx` 库
   - 输出结构化 JSON 数据

2. **脚本生成器** (`script_generator.py`)
   - 将提取的文本转换为教学脚本
   - 第一阶段：基于规则的模板（零成本）
   - 第二阶段：本地 AI 模型（Ollama）或基于 API
   - 输出带有时间信息的解说文本

3. **文本转语音** (`tts_engine.py`)
   - 将脚本转换为音频
   - 第一阶段：Google TTS (gTTS)，备用 espeak
   - 第二阶段：Coqui TTS 更高质量
   - 输出 WAV/MP3 音频文件

4. **视频合成器** (`video_composer.py`)
   - 合并 PPT 幻灯片和音频
   - 使用 FFmpeg 进行视频处理
   - 同步幻灯片切换与音频
   - 输出 1080p MP4 视频

5. **主控制器** (`main.py`)
   - 编排整个流程
   - 处理错误恢复和进度跟踪

## 开发命令

### 设置和安装

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装系统依赖 (macOS)
brew install ffmpeg libreoffice

# 安装系统依赖 (Ubuntu/Debian)
sudo apt-get install ffmpeg libreoffice
```

### 运行应用程序

```bash
# 将单个 PPTX 文件转换为视频
python main.py input.pptx -o output.mp4

# 详细日志输出
python main.py input.pptx -o output.mp4 -v

# 批量处理多个文件
python batch_processor.py --input-dir /path/to/ppts --output-dir /path/to/videos
```

### 开发工作流

```bash
# 开发模式安装
pip install -e .

# 运行测试（实现后）
pytest tests/

# 运行特定测试
pytest tests/test_ppt_parser.py -v

# 运行代码检查（实现后）
flake8 .
# 或
pylint src/

# 代码格式化（实现后）
black .
# 或
autopep8 --in-place *.py
```

### 可选：Web 界面

```bash
# 启动 Streamlit Web 界面
streamlit run app.py

# 访问 http://localhost:8501
```

### 可选：AI 增强（第二阶段）

```bash
# 安装 Ollama 用于本地 AI 模型
brew install ollama  # macOS
# 或
curl -fsSL https://ollama.ai/install.sh | sh  # Linux

# 下载语言模型
ollama pull llama2
ollama pull chatglm3

# 使用 AI 运行脚本生成
python main.py --ai-enhanced input.pptx
```

## 项目结构（规划中）

```
ppt-to-video/
├── main.py                      # 入口点
├── config.py                    # 配置设置
├── ppt_parser.py                # PPT 提取模块
├── script_generator.py          # 脚本生成模块
├── tts_engine.py               # 文本转语音模块
├── video_composer.py           # 视频合成模块
├── batch_processor.py          # 批量处理工具
├── app.py                      # Streamlit Web UI
├── requirements.txt             # Python 依赖
├── requirements-minimal.txt     # 最小依赖（离线模式）
├── tests/                      # 单元测试
│   ├── test_ppt_parser.py
│   ├── test_script_generator.py
│   ├── test_tts_engine.py
│   └── test_video_composer.py
├── utils/                      # 实用工具
│   ├── __init__.py
│   ├── logger.py               # 日志配置
│   └── exceptions.py           # 自定义异常
└── templates/                  # 脚本模板
    └── teaching_script_template.txt
```

## 关键实现细节

### 依赖项（第一阶段 - 最小成本）

```
python-pptx==0.6.21      # PPT 解析
gtts==2.4.0              # Google 文本转语音
pydub==0.25.1            # 音频处理
ffmpeg-python==0.2.0     # 视频处理
Pillow==10.0.0           # 图像处理
colorama==0.4.6          # 彩色终端输出
tqdm==4.66.1             # 进度条
```

### 系统要求

- **Python**：3.9 或更高版本
- **FFmpeg**：视频处理必需
- **LibreOffice**：PPT 转 PDF 转换（备用方法）
- **存储**：每个视频约 500MB 临时文件
- **内存**：典型 PPT 文件 <2GB

### 成本考虑

| 阶段 | 成本 | 功能 |
|-------|------|----------|
| **第一阶段** | $0/月 | 基本功能、基于规则的脚本、gTTS |
| **第二阶段** | $0-50/月 | 增强 TTS、AI 脚本生成 |
| **离线** | $0/月 | 无需互联网，仅系统 TTS |

## 重要设计原则

1. **零/低成本**：优先选择免费和开源解决方案
2. **稳健性**：每个组件都有多个备用选项
3. **简单性**：最小可行产品方法
4. **模块化**：每个组件应可独立测试和替换

## 错误处理策略

系统实现多重备用机制：

1. **TTS 备用**：gTTS → espeak → 系统 TTS
2. **PPT 解析备用**：python-pptx → LibreOffice 转换
3. **脚本生成备用**：AI 模型 → 规则模板
4. **视频处理**：FFmpeg 全面错误日志记录

## 开发说明

### 当前阶段
- 代码库处于**规划/设计阶段**
- 文档完整（tech-stack.md, product-design-document.md）
- 尚未实现源代码
- 准备开始第一阶段实施

### 下一步
1. 使用 `src/` 目录设置项目结构
2. 实现 PPT 解析器模块
3. 实现基本脚本生成（基于规则）
4. 实现 TTS 引擎
5. 实现视频合成器
6. 在 main.py 中集成所有模块
7. 添加全面的错误处理
8. 编写单元测试

### 测试策略
- 每个模块的单元测试（目标：80% 覆盖率）
- 端到端流程的集成测试
- 大型 PPT 文件的性能测试
- 视频/音频输出的质量测试

## 参考文档

- **tech-stack.md**：详细技术实施指南
- **product-design-document.md**：完整产品需求和架构

## 环境设置

### 开发环境
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import pptx, ffmpeg, gtts; print('所有依赖安装成功')"
```

### 生产部署
- 使用 Docker 进行容器化部署
- 考虑第二阶段 AI 功能的 GPU 加速
- 为常用 TTS 语音实现缓存
- 为长时间运行进程设置监控和日志记录

## 已知限制

1. **第一阶段**：基于规则的脚本可能听起来不够自然
2. **复杂 PPT**：可能无法完美处理极其复杂的布局
3. **语言支持**：当前针对中文（zh-cn）优化
4. **视频质量**：取决于源 PPT 分辨率
5. **处理时间**：每张幻灯片约 30 秒（可能有所不同）

## 性能优化技巧

1. **并行处理**：同时处理多张幻灯片
2. **缓存**：为重复文本缓存生成的音频
3. **分块**：分块处理大型 PPT 文件
4. **临时存储**：对临时文件使用快速 SSD
5. **批处理模式**：夜间批量处理多个文件

## API 集成（第二阶段+）

如果使用外部 AI 服务：
- 实施速率限制和退避策略
- 缓存响应以减少 API 调用
- 为多个 API 提供程序提供配置
- 监控成本和使用情况

## 支持和维护

- 检查 `logs/` 目录中的日志以进行调试
- 临时文件存储在 `/tmp/ppt-to-video/`
- 通过 `config.py` 配置
- 通过 tqdm 进度条跟踪进度

# 重要提示：
# 写任何代码前必须完整阅读 memory-bank/@architecture.md（包含完整数据库结构）
# 写任何代码前必须完整阅读 memory-bank/@product-design-document.md
# 每完成一个重大功能或里程碑后，必须更新 memory-bank/@architecture.md