# 系统架构文档

## 文件结构及作用

### 根目录文件

#### main.py
- **作用**: 主程序入口，负责编排整个PPT转视频流程
- **主要功能**:
  - 命令行参数解析
  - 流程编排和模块调用
  - 进度显示和日志记录
  - 错误处理和异常捕获
- **输入**: PPT文件路径、输出路径
- **输出**: 完整的MP4视频文件
- **依赖**: 所有核心模块

#### batch_processor.py
- **作用**: 批量处理工具，支持并行处理多个PPT文件
- **主要功能**:
  - 扫描输入目录中的所有PPT文件
  - 多线程并行处理
  - 进度跟踪和结果统计
  - 错误隔离（单个文件失败不影响整体）
- **输入**: 输入目录路径、输出目录路径
- **输出**: 多个MP4视频文件
- **依赖**: 主程序逻辑

#### requirements.txt
- **作用**: 完整的Python依赖列表
- **包含**:
  - 核心依赖: python-pptx, gtts, ffmpeg-python, pydub
  - 辅助依赖: Pillow, colorama, tqdm, PyYAML
  - 可选依赖: openai, streamlit (用于第二阶段)
- **用途**: `pip install -r requirements.txt`

#### requirements-minimal.txt
- **作用**: 最小依赖列表，用于离线模式或完全离线环境
- **特点**: 不包含gTTS（需要网络），使用系统TTS
- **适用场景**: 无网络环境、完全离线运行

#### .gitignore
- **作用**: Git版本控制忽略文件配置
- **忽略内容**:
  - Python编译文件: __pycache__/, *.pyc
  - 项目输出: output/, logs/, *.mp4, *.pdf
  - 临时文件: tmp/, cache/
  - IDE配置: .vscode/, .idea/

#### README.md
- **作用**: 项目说明文档
- **包含**:
  - 项目概述和功能特性
  - 安装和使用说明
  - 开发进度跟踪
  - 配置选项说明

---

### 核心模块 (src/modules/)

#### ppt_parser.py
- **作用**: PPT文件解析，提取文字、图片、布局信息
- **主要函数**:
  - `extract_text_from_ppt()`: 提取文本内容
    - 输入: PPTX文件路径
    - 输出: 结构化数据（页面号、标题、内容列表）
    - 依赖: python-pptx
  - `convert_ppt_to_images()`: 转换PPT为图片序列
    - 输入: PPT路径、输出目录
    - 输出: PNG图片文件列表
    - 依赖: LibreOffice/FFmpeg
  - `extract_images_from_ppt()`: 提取图片元素
  - `extract_tables_from_ppt()`: 提取表格数据
- **技术方案**:
  - 文本提取: 使用python-pptx库遍历形状
  - 图片转换: 方法待调研（LibreOffice/FFmpeg）
  - 结构化输出: JSON格式

#### script_generator.py
- **作用**: 基于PPT内容生成教学讲解脚本
- **主要函数**:
  - `generate_script()`: 生成教学脚本
    - 输入: PPT解析数据
    - 输出: 讲解脚本列表
    - 依赖: 规则模板系统
  - `optimize_script()`: 优化脚本质量
  - `generate_script_with_ai()`: AI增强生成（可选）
- **技术方案**:
  - Phase 1: 基于规则的模板系统
  - Phase 2: 可选Ollama本地模型
  - 模板类型: 开场白、知识点讲解、过渡语、结尾
- **输出格式**:
  ```python
  {
    'page': 1,
    'title': '幻灯片标题',
    'content': ['内容1', '内容2'],
    'script': '生成的讲解文本'
  }
  ```

#### tts_engine.py
- **作用**: 文本转语音，生成中文女声音频
- **主要函数**:
  - `text_to_speech()`: 单次TTS转换
    - 输入: 文本内容、输出路径、语言
    - 输出: 音频文件路径
    - 依赖: gTTS
  - `text_to_speech_batch()`: 批量转换
  - `merge_audio_segments()`: 合并音频片段
  - `optimize_audio()`: 音频后处理
- **备用方案**:
  1. gTTS (Google) - 优先使用
  2. espeak (Linux) - 备用1
  3. say (macOS) - 备用2
- **音频优化**:
  - 标准化音量
  - 去除背景噪音
  - 调整语速（0.9x适合教学）

#### video_composer.py
- **作用**: 将PPT图片和音频合成为教学视频
- **主要函数**:
  - `create_video()`: 创建教学视频
    - 输入: 图片列表、音频文件、输出路径
    - 输出: MP4视频文件
    - 依赖: FFmpeg
  - `calculate_image_durations()`: 计算图片显示时长
  - `add_transition_effects()`: 添加过渡效果
  - `add_metadata()`: 添加视频元数据
- **技术规格**:
  - 分辨率: 1920x1080
  - 帧率: 30fps
  - 编码: H.264 (libx264)
  - 音频: AAC
- **同步算法**:
  - 根据音频时长分配图片显示时间
  - 精确计算切换时间点
  - 误差控制在0.5秒以内

---

### 工具模块 (src/utils/)

#### logger.py
- **作用**: 统一的日志系统，支持多级别输出和文件轮转
- **主要功能**:
  - `setup_logger()`: 初始化日志系统
    - 输入: 详细模式、日志目录
    - 输出: 配置好的Logger实例
  - `get_logger()`: 获取模块特定Logger
- **日志特性**:
  - 级别: DEBUG, INFO, WARNING, ERROR
  - 输出: 控制台 + 文件
  - 轮转: 按大小（10MB）和数量（5个）轮转
  - 格式: 时间戳 + 模块名 + 级别 + 文件行号 + 消息
- **配置**:
  ```python
  '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
  ```

#### exceptions.py
- **作用**: 定义项目特定的异常类型，便于错误处理和调试
- **异常层次**:
  ```
  AIPPTConverterError (基础异常)
    ├── PPTParseError (PPT解析错误)
    ├── ScriptGenerationError (脚本生成错误)
    ├── TTSError (文本转语音错误)
    ├── VideoCompositionError (视频合成错误)
    ├── ConfigurationError (配置错误)
    ├── AudioProcessingError (音频处理错误)
    ├── FileNotFoundError (文件未找到)
    └── UnsupportedFormatError (不支持的格式)
  ```
- **设计原则**:
  - 每个异常包含上下文信息（文件路径、页码等）
  - 层次化设计，便于捕获特定类型错误
  - 与日志系统配合使用

---

### 测试模块 (tests/)

#### 单元测试 (tests/unit/)
- **test_ppt_parser.py**: 测试PPT解析功能
  - 空PPT、单页PPT、多页PPT
  - 复杂布局、特殊字符、损坏文件
- **test_script_generator.py**: 测试脚本生成功能
  - 不同内容类型、多语言、边界情况
- **test_tts_engine.py**: 测试TTS功能
  - 不同文本长度、缓存机制、备用方案
- **test_video_composer.py**: 测试视频合成功能
  - 不同页数、不同分辨率、音画同步

#### 集成测试 (tests/integration/)
- **test_end_to_end.py**: 端到端测试
  - 完整流程测试
  - 批量处理测试
  - 性能基准测试

#### 测试数据 (tests/test_ppts/)
- **作用**: 存放测试用PPT文件
- **建议类型**:
  - sample_1.pptx: 简单测试（3-5页）
  - sample_2.pptx: 中等复杂度（10-15页）
  - complex_layout.pptx: 复杂布局（20+页）
  - special_chars.pptx: 特殊字符测试
  - corrupted.pptx: 损坏文件测试

---

### 配置模块 (config/)

#### __init__.py
- **作用**: 配置包入口

**注**: config/default.yaml 尚未创建，将在步骤1.4中实现

**预期配置结构**:
```yaml
paths:
  input_dir: "./input"
  output_dir: "./output"
  temp_dir: "./tmp"
  logs_dir: "./logs"

tts:
  primary_engine: "gtts"
  language: "zh-cn"
  speed: 0.9

video:
  resolution: "1920x1080"
  frame_rate: 30
  codec: "libx264"

script:
  mode: "template"
  template_file: "./templates/teaching_script.txt"

logging:
  level: "INFO"
  console_output: true
  file_output: true
```

---

### 模板模块 (templates/)

#### teaching_script.txt (待创建)
- **作用**: 教学脚本模板文件
- **模板类型**:
  - 开场白模板
  - 知识点讲解模板
  - 过渡语模板
  - 结尾模板
- **变量替换**:
  - {title}: 幻灯片标题
  - {content}: 幻灯片内容
  - {page}: 页码
  - {chapter}: 章节号

---

### 输出目录 (output/)

- **作用**: 存放生成的视频文件
- **子目录结构**:
  ```
  output/
    ├── videos/          # 最终视频文件
    ├── temp/            # 临时文件
    ├── audio/           # 音频片段
    └── images/          # PPT转换的图片
  ```

### 日志目录 (logs/)

- **作用**: 存放日志文件
- **日志文件**:
  - ai_ppt_converter_YYYYMMDD.log: 主日志文件
  - ai_ppt_converter_YYYYMMDD.log.1: 轮转日志1
  - ai_ppt_converter_YYYYMMDD.log.2: 轮转日志2
  - ... (最多5个轮转文件)

---

## 数据流

### 完整流程
```
PPT文件
  ↓
ppt_parser.py (解析)
  ↓  JSON结构化数据
script_generator.py (生成脚本)
  ↓  讲解文本
tts_engine.py (语音合成)
  ↓  音频文件
video_composer.py (视频合成)
  ↓
最终视频 (MP4)
```

### 中间数据格式

#### PPT解析输出
```python
[
  {
    'page': 1,
    'title': '标题',
    'content': ['要点1', '要点2'],
    'images': ['image1.png'],
    'tables': [{'headers': [], 'rows': []}]
  }
]
```

#### 脚本生成输出
```python
[
  {
    'page': 1,
    'title': '标题',
    'script': '现在我们来学习第1页的内容...'
  }
]
```

#### TTS输出
```
音频文件列表:
- audio_001.mp3
- audio_002.mp3
- ...
```

---

## 模块依赖关系

### 依赖图
```
main.py
  ├─ ppt_parser.py
  ├─ script_generator.py
  ├─ tts_engine.py
  └─ video_composer.py
       ↓
  utils/
  ├─ logger.py (所有模块)
  └─ exceptions.py (所有模块)
```

### 跨模块交互
1. **ppt_parser** → **script_generator**: JSON数据传递
2. **script_generator** → **tts_engine**: 文本字符串传递
3. **tts_engine** → **video_composer**: 音频文件路径传递
4. **ppt_parser** → **video_composer**: 图片文件路径传递

---

## 阶段完成记录

### ✅ 阶段1: 环境搭建和项目初始化 (2026-01-16)
- **完成时间**: 2026-01-16 15:40
- **完成内容**:
  - 项目目录结构创建
  - 核心模块代码框架
  - 依赖配置文件
  - 测试框架
  - 日志和异常处理
  - README文档
- **创建文件数**: 22个
- **状态**: 已完成，等待后续步骤实施

### 🔄 阶段2: PPT解析模块 (待开始)
- **预计开始**: 2026-01-17
- **任务**: 实现ppt_parser.py的具体功能
- **关键**: PPT到图片转换方案调研

### 📋 阶段3-7: 待实施
- 脚本生成模块
- TTS模块
- 视频合成模块
- 系统集成
- 验收测试

---

## 架构设计原则

### 1. 模块化设计
- 每个模块职责单一
- 清晰的输入输出定义
- 低耦合、高内聚

### 2. 可扩展性
- 支持AI增强（可选）
- 支持多种TTS引擎
- 支持不同视频格式

### 3. 健壮性
- 多重备用方案
- 全面的错误处理
- 详细的日志记录

### 4. 零成本优先
- Phase 1: 完全免费开源方案
- 无API依赖
- 可离线运行

### 5. 易于测试
- 单元测试覆盖每个函数
- 集成测试覆盖完整流程
- 模拟数据和真实数据结合

---

## 性能考虑

### 处理速度目标
- 单页PPT < 30秒
- 10页PPT < 5分钟
- 50页PPT < 20分钟

### 资源使用限制
- 内存 < 2GB
- 临时空间 < 1GB
- CPU < 80%

### 优化策略
- 并行处理: TTS音频生成
- 缓存: 相同文本的音频
- 流式处理: 大文件分块处理

---

## 错误处理策略

### 错误分类
1. **输入错误**: 文件不存在、格式错误
2. **解析错误**: PPT损坏、无法读取
3. **处理错误**: 内存不足、磁盘空间不足
4. **外部依赖错误**: FFmpeg未安装、网络中断

### 处理机制
- **重试**: 指数退避重试（最多3次）
- **回退**: 备用TTS引擎
- **恢复**: 断点续传（从失败步骤恢复）
- **清理**: 失败后清理临时文件

---

## 安全考虑

### 数据安全
- 本地处理，不上传敏感数据
- 临时文件自动清理
- 支持完全离线模式

### 系统安全
- 验证输入文件类型
- 限制资源使用
- 防止路径遍历攻击

---

**文档版本**: v1.0
**创建日期**: 2026-01-16
**最后更新**: 2026-01-16
**作者**: Claude Code
**适用范围**: Phase 1 基础架构
