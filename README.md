# TalkBubble - Intelligent Voice Input Window

A lightweight, floating voice input tool that transcribes speech and intelligently repairs/formats text using Qwen models.

## Features
1.  **Voice to Text**: Uses state-of-the-art ASR (Qwen3-ASR-0.6B or SenseVoiceSmall).
2.  **Logical Repair**: Uses LLM (Qwen3-0.6B) to fix grammar, segment text, and add logical connectives.
3.  **Context Aware**: Can use selected text (clipboard) as context for the repair.
4.  **Floating Window**: Always-on-top, unobtrusive UI.
5.  **Global Hotkey**: Toggle recording with `F9`.

## Requirements
- macOS (tested) or Windows/Linux
- Python 3.9+
- Internet connection (for first-time model download)

## Installation

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: For Apple Silicon (M1/M2/M3), ensure you have the `mps` supported version of PyTorch.*

2.  **Run the Application**
    ```bash
    python src/main.py
    ```

## Usage
1.  Launch the app. It will take a moment to download/load the models on the first run.
2.  Wait for the status to say "Ready".
3.  Press **F9** or click the **Microphone** button to start recording.
4.  Speak your text.
5.  Press **F9** again or click **Stop**.
6.  The transcribed and polished text will appear in the window.
7.  Click **Copy** to copy to clipboard.

## Models Used
- **ASR**: `Qwen/Qwen3-ASR-0.6B` (Fallback: `iic/SenseVoiceSmall`)
- **LLM**: `Qwen/Qwen3-0.6B` (Fallback: `Qwen/Qwen3-Coder-0.6B`)
