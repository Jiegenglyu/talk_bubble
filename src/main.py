import sys
import threading
import queue
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot, QThread, Qt

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

    def __init__(self):
        super().__init__()
        self.asr_engine = None
        self.llm_engine = None
        self.audio_capture = AudioCapture(level_callback=self.on_audio_level)
        self.is_recording = False
        
    def on_audio_level(self, level):
        self.audio_level.emit(level)

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
        self.audio_capture.start_recording()
        self.is_recording = True
        
    @Slot()
    def stop_recording_and_process(self):
        if not self.is_recording:
            return
            
        self.status_update.emit("Processing Audio...")
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

    @Slot(str, str)
    def refine_selection(self, current_ui_text, custom_prompt):
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
            
            final_text = self.llm_engine.process_text(target_text, context=context_text, custom_prompt=custom_prompt)
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
    refine_selection_worker_signal = Signal(str, str)

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
        self.refine_selection_worker_signal.emit(text, prompt)

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
