# TalkBubble - Intelligent Voice Input Window

[English](#english) | [中文](#chinese)

<a name="english"></a>

## English

A lightweight, floating voice input tool that transcribes speech and intelligently repairs/formats text using Qwen models.

### Features
1.  **Voice to Text**: Uses state-of-the-art ASR (Qwen3-ASR-0.6B).
2.  **Logical Repair**: Uses LLM (Qwen3-0.6B) to fix grammar, segment text, and add logical connectives.
3.  **Real-time Streaming**: See your speech transcribed as you talk.
4.  **Thinking Process Visualization**: View the model's reasoning process in a collapsible section (supports `<think>` tags).
5.  **History Management**: Access and copy your last 3 results from the history menu.
6.  **Quick Actions**: One-click **Clear** to reset the screen and **Copy** to clipboard.
7.  **Enhanced Feedback**: Waveform reacts dynamically to text output for better visual confirmation.
8.  **Custom Presets**: Save your favorite prompts and instructions for quick reuse.
9.  **Model Loading Protection**: Prevents accidental recording before models are ready.
10. **Floating Window**: Always-on-top, unobtrusive UI.
11. **Global Hotkey**: Toggle recording with `F9`.

### Requirements
- macOS (tested) or Windows/Linux
- Python 3.9+
- Internet connection (for first-time model download)

### Installation

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: For Apple Silicon (M1/M2/M3), ensure you have the `mps` supported version of PyTorch.*

2.  **Run the Application**
    ```bash
    python src/main.py
    ```

### Usage
1.  Launch the app. It will take a moment to download/load the models on the first run.
2.  Wait for the status to say "Ready" (Recording is disabled until models are loaded).
3.  Press **F9** or click the **Microphone** button to start recording.
4.  Speak your text. You will see the text appear in real-time.
5.  Press **F9** again or click **Stop**.
6.  The transcribed and polished text will appear in the window.
7.  Click **Refine** to choose a preset or **Copy** to copy to clipboard.

### Managing Custom Presets
1.  Click the **Settings** (hamburger menu) icon.
2.  Select **Set Custom Prompt...** to enter a new instruction.
3.  To save it for later, select **Save Current as Preset...**.
4.  Give it a name, and it will appear in your **Refine** menu permanently.

### Models Used
- **ASR**: `Qwen/Qwen3-ASR-0.6B`
- **LLM**: `Qwen/Qwen3-0.6B`

---

<a name="chinese"></a>

## 中文 (Chinese)

一个轻量级的悬浮语音输入工具，使用 Qwen 模型进行语音转写和智能文本润色。

### 功能特性
1.  **语音转文字**: 使用最先进的 ASR 模型 (Qwen3-ASR-0.6B)。
2.  **智能润色**: 使用 LLM (Qwen3-0.6B) 修复语法、分段并添加逻辑连接词。
3.  **实时流式输出**: 边说边出字，实时查看转写结果。
4.  **思考过程可视化**: 支持折叠显示模型的推理思考过程 (`<think>` 标签)，点击可展开查看详情。
5.  **历史记录管理**: 在菜单中随时查看并复制最近的 3 条生成结果。
6.  **快捷操作**: 新增 **一键清屏** 按钮，快速重置对话状态；支持一键复制。
7.  **增强视觉反馈**: 波形图会根据文字输出动态跳动，提供更直观的录音反馈。
8.  **自定义预设**: 保存您常用的提示词指令，方便下次快速复用。
9.  **模型加载保护**: 在模型完全加载就绪前，防止误操作录音。
10. **悬浮窗口**: 置顶显示，不干扰工作。
11. **全局快捷键**: 使用 `F9` 一键切换录音。

### 环境要求
- macOS (已测试) 或 Windows/Linux
- Python 3.9+
- 网络连接 (首次运行需要下载模型)

### 安装步骤

1.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```
    *注意: 对于 Apple Silicon (M1/M2/M3) 用户，请确保安装支持 `mps` 加速的 PyTorch 版本。*

2.  **运行应用**
    ```bash
    python src/main.py
    ```

### 使用指南
1.  启动应用。首次运行需要下载模型，请耐心等待。
2.  等待状态栏显示 "TalkBubble" (模型加载期间录音功能将被禁用)。
3.  按 **F9** 或点击 **录音** 按钮开始说话。
4.  说话过程中，文字会实时显示在窗口中。
5.  再次按 **F9** 或点击 **停止**。
6.  转写和润色后的文本将显示在窗口中。
7.  点击 **润色** 选择预设指令，或点击 **复制** 将内容复制到剪贴板。

### 管理自定义预设
1.  点击标题栏右侧的 **设置** (汉堡菜单) 图标。
2.  选择 **设置自定义指令...** 输入新的指令内容。
3.  如需保存，选择 **保存当前为预设...**。
4.  输入名称后，该预设将永久保存在 **润色** 菜单中，方便随时调用。

### 使用模型
- **语音识别 (ASR)**: `Qwen/Qwen3-ASR-0.6B`
- **大语言模型 (LLM)**: `Qwen/Qwen3-0.6B`
