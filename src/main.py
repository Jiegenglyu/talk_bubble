import sys
import threading
import queue
import time
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot, QThread, Qt, QTimer

# Import our modules
from gui.floating_window import FloatingWindow
from logic.audio_capture import AudioCapture
from logic.asr_engine import ASREngine
from logic.llm_engine import LLMEngine

import pyperclip
from pynput import keyboard

class WorkerSignals(QObject):
    finished = Signal(str)
    error = Signal(str)
    status_update = Signal(str)

class ModelWorker(QObject):
    """
    Worker thread to handle model loading and inference
    to keep the UI responsive.
    """
    finished = Signal(str)
    error = Signal(str)
    status_update = Signal(str)
    audio_level = Signal(float)
    model_loaded = Signal(str)
    active_model = Signal(str)
    stream_text = Signal(str)

    def __init__(self):
        super().__init__()
        self.asr_engine = None
        self.llm_engine = None
        self.audio_capture = AudioCapture(level_callback=self.on_audio_level)
        self.is_recording = False
        
        # Streaming Setup
        self.stream_timer = QTimer(self)
        self.stream_timer.setInterval(1000) # 1 second interval
        self.stream_timer.timeout.connect(self.process_stream_audio)
        self.stream_buffer = []
        
    def on_audio_level(self, level):
        self.audio_level.emit(level)

    @Slot()
    def process_stream_audio(self):
        if not self.is_recording or not self.audio_capture:
            return

        new_audio = self.audio_capture.read_available_audio()
        if new_audio is not None and len(new_audio) > 0:
             self.stream_buffer.append(new_audio)
             
             # Transcribe full buffer so far
             try:
                 full_audio = np.concatenate(self.stream_buffer)
                 if self.asr_engine:
                     text = self.asr_engine.transcribe(full_audio)
                     if text:
                         self.stream_text.emit(text)
             except Exception as e:
                 print(f"Stream Error: {e}")

    @Slot()
    def load_models(self):
        self.status_update.emit("Loading ASR...")
        # Load ASR (Qwen3-ASR-0.6B)
        try:
            self.asr_engine = ASREngine()
        except Exception as e:
            self.error.emit(f"ASR Load Failed: {e}")
            return

        self.status_update.emit("Loading LLM...")
        # Load LLM (Qwen3-0.6B)
        try:
            self.llm_engine = LLMEngine()
            self.model_loaded.emit(f"LLM: {self.llm_engine.model_name}")
        except Exception as e:
            self.error.emit(f"LLM Load Failed: {e}")
            return
            
        self.status_update.emit("Ready")

    @Slot()
    def start_recording(self):
        if not self.audio_capture:
             self.audio_capture = AudioCapture(level_callback=self.on_audio_level)
        
        # Ensure callback is set if recreated
        self.audio_capture.level_callback = self.on_audio_level
        
        # Signal active ASR model
        if self.asr_engine:
             self.active_model.emit(f"ASR: {self.asr_engine.model_name}")
        
        self.stream_buffer = []
        self.audio_capture.start_recording()
        self.is_recording = True
        self.stream_timer.start()
        
    @Slot()
    def stop_recording_and_process(self):
        self.stream_timer.stop()
        if not self.is_recording:
            return
            
        self.status_update.emit("Processing Audio...")
        
        # Keep showing ASR model during processing
        if self.asr_engine:
             self.active_model.emit(f"ASR: {self.asr_engine.model_name}")
        try:
            audio_data = self.audio_capture.stop_recording()
        except Exception as e:
            self.error.emit(f"Audio Error: {e}")
            self.is_recording = False
            return

        self.is_recording = False
        
        if audio_data is None or len(audio_data) == 0:
            self.error.emit("No audio recorded")
            return
            
        # 1. Transcribe
        self.status_update.emit("Transcribing...")
        try:
            if not self.asr_engine:
                 self.error.emit("ASR Engine not loaded")
                 return
            text = self.asr_engine.transcribe(audio_data)
            print(f"Transcribed: {text}")
        except Exception as e:
            self.error.emit(f"ASR Error: {e}")
            return

        if not text:
            self.error.emit("No speech detected")
            return

        self.finished.emit(text)

    @Slot(str, str, str)
    def refine_selection(self, current_ui_text, custom_prompt, lang_code):
        # Signal active LLM model
        if self.llm_engine:
             self.active_model.emit(f"LLM: {self.llm_engine.model_name}")
             
        context_text = ""
        
        # Priority 1: Use text currently in the window (e.g. just dictated)
        if current_ui_text:
            self.status_update.emit("Refining Input...")
            target_text = current_ui_text
        else:
            # Priority 2: Use Clipboard
            self.status_update.emit("Reading Clipboard...")
            try:
                context_text = pyperclip.paste()
            except Exception as e:
                 self.error.emit(f"Clipboard Error: {e}")
                 return

            if not context_text:
                self.error.emit("Clipboard is empty")
                return
            target_text = "" # Will be handled by process_text logic

        self.status_update.emit("Refining...")
        try:
            if not self.llm_engine:
                 self.error.emit("LLM Engine not loaded")
                 return
            
            # Callback for streaming
            def on_stream(partial_text):
                self.stream_text.emit(partial_text)
                
            # Append language instruction to custom prompt if needed
            # For now we assume custom_prompt handles it or we rely on system prompt.
            # But user asked for language consistency.
            lang_instruction = ""
            if lang_code == "zh":
                lang_instruction = "IMPORTANT: Output in Chinese (Simplified)."
            elif lang_code == "en":
                lang_instruction = "IMPORTANT: Output in English."
            
            final_prompt = custom_prompt
            if lang_instruction:
                if final_prompt:
                    final_prompt += f"\n{lang_instruction}"
                else:
                    final_prompt = lang_instruction
            
            final_text = self.llm_engine.process_text(
                target_text, 
                context=context_text, 
                custom_prompt=final_prompt,
                stream_callback=on_stream
            )
        except Exception as e:
            self.error.emit(f"LLM Error: {e}")
            return
            
        self.finished.emit(final_text)

class HotkeyBridge(QObject):
    activated = Signal()

class MainWindow(FloatingWindow):
    start_loading_signal = Signal()
    start_recording_worker_signal = Signal()
    stop_recording_worker_signal = Signal()
    refine_selection_worker_signal = Signal(str, str, str)

    def __init__(self):
        super().__init__()
        
        # Threading
        self.worker_thread = QThread()
        self.worker = ModelWorker()
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker.status_update.connect(self.update_status_safe)
        self.worker.finished.connect(self.handle_result_safe)
        self.worker.error.connect(self.handle_error_safe)
        self.worker.audio_level.connect(self.update_audio_level_safe)
        self.worker.model_loaded.connect(self.handle_model_loaded_safe)
        self.worker.active_model.connect(self.handle_active_model_safe)
        self.worker.stream_text.connect(self.handle_stream_text_safe)
        
        # Connect control signals
        self.start_loading_signal.connect(self.worker.load_models)
        self.start_recording_worker_signal.connect(self.worker.start_recording)
        self.stop_recording_worker_signal.connect(self.worker.stop_recording_and_process)
        self.refine_selection_worker_signal.connect(self.worker.refine_selection)
        
        # Connect GUI signals
        self.refine_selection_signal.connect(self.on_refine_selection_ui)
        
        # Start thread
        self.worker_thread.start()
        
        # Trigger loading
        self.start_loading_signal.emit()
        
        # Global Hotkey (F9)
        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.activated.connect(self.toggle_recording_safe)
        
        self.listener = keyboard.GlobalHotKeys({
            '<f9>': self.on_hotkey
        })
        self.listener.start()

    def on_hotkey(self):
        self.hotkey_bridge.activated.emit()

    @Slot(str, str)
    def on_refine_selection_ui(self, text, prompt):
        # Infer language from UI state (stored in FloatingWindow)
        # But we are in MainWindow which inherits FloatingWindow.
        # FloatingWindow has self.current_lang ("en" or "zh")
        lang_code = self.current_lang 
        self.refine_selection_worker_signal.emit(text, prompt, lang_code)

    @Slot()
    def toggle_recording_safe(self):
        # This runs in main thread
        self.toggle_recording()

    # Override start/stop to emit signals to worker
    def start_recording(self):
        super().start_recording() # Updates UI
        self.start_recording_worker_signal.emit()

    def stop_recording(self):
        super().stop_recording() # Updates UI
        self.stop_recording_worker_signal.emit()

    @Slot(str)
    def update_status_safe(self, status):
        self.status_label.setText(status)
        if status == "Ready":
            self.set_models_ready(True)
        
    @Slot(float)
    def update_audio_level_safe(self, level):
        if self.is_recording:
             self.waveform_view.setVisible(True)
             self.waveform_view.add_level(level)
        else:
             self.waveform_view.setVisible(False)
             # Clear levels to reset
             self.waveform_view.levels = []
             self.waveform_view.update()

    @Slot(str)
    def handle_stream_text_safe(self, partial_text):
        self.update_text(partial_text, is_final=False)
        # Maybe scroll to bottom?
        # self.text_area.moveCursor(QTextCursor.End)

    @Slot(str)
    def handle_result_safe(self, text):
        self.update_text(text)
        # update_text in FloatingWindow already handles UI state

    @Slot(str)
    def handle_error_safe(self, error_msg):
        self.handle_error(error_msg)
        # handle_error in FloatingWindow already handles UI state

    @Slot(str)
    def handle_model_loaded_safe(self, model_info):
        self.model_label.setText(model_info)

    @Slot(str)
    def handle_active_model_safe(self, model_info):
        self.model_label.setText(model_info)

    def closeEvent(self, event):
        self.listener.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Important for tray apps
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
