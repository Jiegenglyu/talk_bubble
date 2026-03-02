# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TalkBubble is a lightweight, floating voice input tool that transcribes speech and intelligently repairs/formats text using Qwen models. The application provides real-time voice-to-text conversion with post-processing using LLMs to improve grammar, structure, and clarity.

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **GUI Layer** ([src/gui/floating_window.py](src/gui/floating_window.py)): PySide6-based floating window interface with drag support, system tray integration, and waveform visualization
- **Logic Layer** ([src/logic/](src/logic/)):
  - ASR Engine: Handles speech-to-text conversion using Qwen3-ASR-0.6B model
  - LLM Engine: Processes and refines text using Qwen3-0.6B model
  - Audio Capture: Records audio with real-time level monitoring
- **Main Application** ([src/main.py](src/main.py)): Orchestrates threads and manages global hotkeys (F9)

## Key Features

- Voice-to-text transcription with Qwen ASR models
- Text refinement using Qwen LLM models
- Context-aware processing (can use clipboard content)
- Floating window with macOS-style controls
- Real-time audio waveform visualization
- Multi-language support (Chinese/English)
- Global hotkey (F9) for recording toggle
- Prompt presets for different use cases (emails, meetings, code comments, etc.)

## Development Commands

### Setup & Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Models Used
- ASR: `Qwen/Qwen3-ASR-0.6B` (Fallback: `iic/SenseVoiceSmall`)
- LLM: `Qwen/Qwen3-0.6B` (Fallback: `Qwen/Qwen3-Coder-0.6B`)

## Key Components

### Floating Window ([src/gui/floating_window.py](src/gui/floating_window.py))
- Implements draggable floating UI with macOS-style traffic light controls
- Supports bilingual interface (Chinese/English)
- Contains waveform visualization during recording
- Provides preset prompt options for text refinement

### ASR Engine ([src/logic/asr_engine.py](src/logic/asr_engine.py))
- Uses Qwen3-ASR-0.6B model from Alibaba Cloud's ModelScope
- Handles audio file processing and transcription
- Runs on CPU by default (with MPS/CUDA fallback option)

### LLM Engine ([src/logic/llm_engine.py](src/logic/llm_engine.py))
- Uses Qwen3-0.6B model for text refinement
- Implements streaming generation for real-time text updates
- Supports custom prompts and context-aware processing

### Audio Capture ([src/logic/audio_capture.py](src/logic/audio_capture.py))
- Records audio using sounddevice
- Provides real-time audio level feedback for UI
- Uses queues for thread-safe audio buffer handling

## Threading Model

The application uses Qt's threading system:
- Main UI thread handles GUI updates
- Worker thread manages model loading and inference
- Global hotkey listener runs in background thread
- Audio capture operates independently with callbacks

## Testing

There are no explicit test files in the current codebase. When adding new functionality, consider implementing tests that cover:
- Audio capture functionality
- ASR transcription accuracy
- LLM processing with different inputs
- UI interaction flows