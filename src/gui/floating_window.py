import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QTextEdit, QSystemTrayIcon, QMenu, QFrame, QGraphicsDropShadowEffect, QInputDialog, QLineEdit, QToolButton, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QSize
from PySide6.QtGui import QIcon, QAction, QCursor, QColor, QPainter, QPainterPath, QFont, QPixmap

# Prompt Presets
PROMPT_PRESETS = {
    "agent": {
        "name_en": "Agent Coding (Default)",
        "name_zh": "Agent Coding (默认)",
        "prompt": "Strictly preserve the user's original intent. Do not add new features or information not present in the source. Fix terminology and structure only." 
    },
    "email": {
        "name_en": "Email Polish",
        "name_zh": "邮件润色",
        "prompt": "Refine the text into a professional email. Strictly adhere to the original meaning. Do not add new information or hallucinate details. Fix grammar and tone only."
    },
    "meeting": {
        "name_en": "Meeting Minutes",
        "name_zh": "会议纪要",
        "prompt": "Summarize into meeting minutes based ONLY on the provided text. Do not invent discussion points. Identify key decisions and actions present in the text."
    },
    "comments": {
        "name_en": "Code Comments",
        "name_zh": "代码注释",
        "prompt": "Generate code comments based strictly on the provided logic. Do not assume functionality not present in the text. Use standard technical terminology."
    },
    "requirements": {
        "name_en": "Requirement Breakdown",
        "name_zh": "需求拆解",
        "prompt": "Break down the requirements into technical tasks. Strictly follow the user's scope. Do not add features or assumptions not explicitly stated."
    },
    "summary": {
        "name_en": "Key Points",
        "name_zh": "要点提炼",
        "prompt": "Extract key points from the text. Strictly maintain the original facts. Do not add external information."
    }
}

# Localization Dictionary
TRANSLATIONS = {
    "en": {
        "status_ready": "TalkBubble",
        "status_listening": "Listening...",
        "status_processing": "Processing...",
        "status_refining": "Refining...",
        "status_done": "Done",
        "status_error": "Error",
        "status_copied": "Copied!",
        "btn_record": "Record",
        "btn_stop": "Stop",
        "btn_refine": "Refine",
        "btn_copy": "Copy",
        "btn_exit": "Exit",
        "placeholder_text": "Spoken text will appear here...",
        "placeholder_prompt": "Custom instruction (Default: Agent Coding Logic)...",
        "tooltip_close": "Minimize",
        "tooltip_quit": "Quit",
        "tooltip_settings": "Settings",
        "settings_title": "Settings",
        "language_label": "Language",
        "status_loading_model": "Models Loading...",
    },
    "zh": {
        "status_ready": "TalkBubble",
        "status_listening": "正在听...",
        "status_processing": "处理中...",
        "status_refining": "优化中...",
        "status_done": "完成",
        "status_error": "错误",
        "status_copied": "已复制!",
        "btn_record": "录音",
        "btn_stop": "停止",
        "btn_refine": "润色",
        "btn_copy": "复制",
        "btn_exit": "退出",
        "placeholder_text": "识别的文字将显示在这里...",
        "placeholder_prompt": "自定义指令 (默认: Agent Coding 逻辑)...",
        "tooltip_close": "最小化",
        "tooltip_quit": "退出",
        "tooltip_settings": "设置",
        "settings_title": "设置",
        "language_label": "语言",
        "status_loading_model": "模型加载中...",
    }
}

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.levels = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        # We don't need continuous update if we push data
        # self.timer.start(50) 
        self.setMinimumHeight(30)
        self.setStyleSheet("background-color: transparent;")

    def add_level(self, level):
        self.levels.append(level)
        if len(self.levels) > 40:
            self.levels.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        mid_y = height / 2
        
        if not self.levels:
            return

        # macOS voice memo style bars
        bar_width = 3
        gap = 2
        total_bars = int(width / (bar_width + gap))
        
        # Draw only latest N bars that fit
        levels_to_draw = self.levels[-total_bars:]
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FF3B30")) # macOS Red for recording
        
        for i, level in enumerate(levels_to_draw):
            # level is 0.0 to 1.0 (approx)
            # Scale height with some min height
            bar_height = max(4, level * height * 0.9)
            
            x = i * (bar_width + gap)
            y = mid_y - (bar_height / 2)
            
            painter.drawRoundedRect(x, y, bar_width, bar_height, 1.5, 1.5)

class FloatingWindow(QMainWindow):
    # Signals to communicate with logic
    start_recording_signal = Signal()
    stop_recording_signal = Signal()
    refine_selection_signal = Signal(str, str)
    quit_app_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TalkBubble")
        self.current_lang = "zh" 
        
        # Window flags for floating behavior
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main widget container for shadow
        self.container_widget = QWidget()
        self.setCentralWidget(self.container_widget)
        self.main_layout = QVBoxLayout(self.container_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20) # Space for shadow
        
        # The actual visible frame
        self.frame = QFrame()
        self.frame.setObjectName("MainFrame")
        self.main_layout.addWidget(self.frame)
        
        # Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 8)
        self.frame.setGraphicsEffect(shadow)
        
        # Layout inside frame
        self.layout = QVBoxLayout(self.frame)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)
        
        # Style
        self.update_stylesheet()
        
        # Header (Drag handle + Controls)
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(8)
        
        # Mac-style Window Controls (Left side)
        # Close (Minimize)
        self.close_btn = QPushButton("")
        self.close_btn.setFixedSize(12, 12)
        self.close_btn.setToolTip(self.tr("tooltip_close"))
        self.close_btn.setObjectName("mac_close") # Yellow/Orange for minimize
        self.close_btn.clicked.connect(self.hide_window) 
        self.header_layout.addWidget(self.close_btn)
        
        # Quit (Exit)
        self.quit_btn = QPushButton("") 
        self.quit_btn.setFixedSize(12, 12)
        self.quit_btn.setToolTip(self.tr("tooltip_quit"))
        self.quit_btn.setObjectName("mac_quit") # Red for close/quit
        self.quit_btn.clicked.connect(self.quit_app)
        self.header_layout.addWidget(self.quit_btn)

        # Settings (Hamburger Menu)
        self.settings_btn = QPushButton()
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setIcon(self.create_hamburger_icon())
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.setToolTip(self.tr("tooltip_settings"))
        # Clean style: Transparent background, subtle hover
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.settings_btn.clicked.connect(self.show_settings_menu)
        self.header_layout.addWidget(self.settings_btn)
        
        # Title/Status Centered
        self.status_label = QLabel(self.tr("status_ready"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #DDDDDD; letter-spacing: 0.5px;")
        self.header_layout.addWidget(self.status_label, 1) # Stretch to center
        
        self.layout.addWidget(self.header)
        
        # Waveform View
        self.waveform_view = WaveformWidget()
        self.waveform_view.setVisible(False)
        self.waveform_view.setFixedHeight(30)
        self.layout.addWidget(self.waveform_view)
        
        # Text Area (Hidden initially)
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText(self.tr("placeholder_text"))
        self.text_area.setVisible(False)
        self.text_area.setMaximumHeight(100)
        self.layout.addWidget(self.text_area)
        
        # Store custom prompt text
        self.custom_prompt_text = ""

        # Controls
        self.controls = QWidget()
        self.controls_layout = QHBoxLayout(self.controls)
        self.controls_layout.setContentsMargins(0, 4, 0, 0)
        self.controls_layout.setSpacing(12)
        
        # Main Actions
        self.record_btn = QPushButton(self.tr("btn_record"))
        self.record_btn.setIcon(QIcon()) # Remove if any
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.controls_layout.addWidget(self.record_btn)
        
        # Refine Button with Dropdown Menu
        self.refine_btn = QToolButton()
        self.refine_btn.setText(self.tr("btn_refine"))
        self.refine_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.refine_btn.setPopupMode(QToolButton.MenuButtonPopup)
        self.refine_btn.setCursor(Qt.PointingHandCursor)
        self.refine_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.refine_btn.clicked.connect(self.on_refine_clicked)
        
        # Build Menu
        self.refine_menu = QMenu(self.refine_btn)
        self.refine_menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007AFF;
            }
        """)
        
        # Add presets to menu
        for key, data in PROMPT_PRESETS.items():
            name = data["name_zh"] if self.current_lang == "zh" else data["name_en"]
            action = QAction(name, self)
            # Use lambda to capture key
            action.triggered.connect(lambda checked=False, k=key: self.set_prompt_mode(k))
            self.refine_menu.addAction(action)
            
        self.refine_btn.setMenu(self.refine_menu)
        self.controls_layout.addWidget(self.refine_btn)
        
        self.copy_btn = QPushButton(self.tr("btn_copy"))
        self.copy_btn.setVisible(False)
        self.copy_btn.clicked.connect(self.copy_text)
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.controls_layout.addWidget(self.copy_btn)
        
        self.layout.addWidget(self.controls)

        # Model Status Label (Footer)
        self.model_label = QLabel("Loading models...")
        self.model_label.setAlignment(Qt.AlignRight)
        self.model_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 2px;")
        self.layout.addWidget(self.model_label)
        
        # Drag logic
        self.old_pos = None
        
        # State
        self.is_recording = False
        self.is_model_ready = False
        
        # Tray Icon setup with dynamic icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.update_tray_icon()
        self.tray_icon.show()
        
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

    def update_tray_icon(self):
        # Create a "T" icon for TalkBubble
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background circle
        painter.setBrush(QColor("#4CAF50"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        
        # Letter "T"
        painter.setPen(QColor("white"))
        font = QFont("Arial", 32, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "T")
        
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
        self.setWindowIcon(QIcon(pixmap))

    def create_hamburger_icon(self):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("white"))
        
        # Draw 3 bars
        # 24x24 canvas
        # Bar width: 18px
        # Bar height: 2px
        # Gap: 4px
        # Vertical centering: Total height = 2*3 + 4*2 = 14px. Top padding = (24-14)/2 = 5px
        
        w = 18
        h = 2
        x = 3
        y_start = 5
        gap = 4
        
        painter.drawRoundedRect(x, y_start, w, h, 1, 1)
        painter.drawRoundedRect(x, y_start + h + gap, w, h, 1, 1)
        painter.drawRoundedRect(x, y_start + 2*(h + gap), w, h, 1, 1)
        
        painter.end()
        return QIcon(pixmap)

    def show_settings_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 6px 24px;
                border-radius: 4px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #007AFF; /* macOS Blue */
                color: white;
            }
        """)
        
        # Language Toggle
        lang_text = "Switch to English" if self.current_lang == "zh" else "切换到中文"
        lang_action = QAction(lang_text, self)
        lang_action.triggered.connect(self.toggle_language)
        menu.addAction(lang_action)
        
        # Custom Prompt Input
        prompt_text = "Set Custom Prompt..." if self.current_lang == "en" else "设置自定义指令..."
        prompt_action = QAction(prompt_text, self)
        prompt_action.triggered.connect(self.open_prompt_dialog)
        menu.addAction(prompt_action)
        
        menu.exec(self.settings_btn.mapToGlobal(QPoint(0, self.settings_btn.height() + 5)))

    def open_prompt_dialog(self):
        title = "Custom Prompt" if self.current_lang == "en" else "自定义指令"
        label = "Enter instruction (e.g. 'Translate to English'):" if self.current_lang == "en" else "输入指令 (例如 '翻译成英文'):"
        text, ok = QInputDialog.getText(self, title, label, QLineEdit.Normal, self.custom_prompt_text)
        if ok:
            self.custom_prompt_text = text

    def hide_window(self):
        self.hide()
        # Ensure tray icon is visible
        self.tray_icon.show()
        self.tray_icon.showMessage(
            "TalkBubble", 
            self.tr("tooltip_close"), 
            QSystemTrayIcon.Information, 
            2000
        )

    def tr(self, key):
        return TRANSLATIONS.get(self.current_lang, TRANSLATIONS["en"]).get(key, key)

    def on_tray_activated(self, reason):
        # Click on tray icon should restore window
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()
            self.activateWindow()
            
    def update_stylesheet(self):
        self.setStyleSheet("""
            /* Main Frame */
            QFrame#MainFrame {
                background-color: rgba(40, 40, 40, 240); /* Dark translucent */
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
            }
            
            /* Text Area */
            QTextEdit {
                background-color: rgba(0, 0, 0, 40);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-size: 13px;
                padding: 6px;
            }
            
            /* Action Buttons (Record, Refine, Copy) */
            QPushButton, QToolButton {
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 10);
                border-radius: 6px;
                color: #FFFFFF;
                font-family: -apple-system, sans-serif;
                font-size: 13px;
                font-weight: 500;
                padding: 6px 12px;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: rgba(255, 255, 255, 25);
            }
            QPushButton:pressed, QToolButton:pressed {
                background-color: rgba(255, 255, 255, 10);
            }
            
            /* Specific Button Colors */
            QToolButton::menu-button {
                 border-left: 1px solid rgba(255,255,255,30);
                 width: 16px;
            }
            QPushButton#stop_btn {
                background-color: rgba(255, 59, 48, 0.8); /* Mac Red */
                color: white;
                border: none;
            }
            QPushButton#stop_btn:hover {
                background-color: rgba(255, 59, 48, 1.0);
            }
            
            /* Mac Window Controls (Traffic Lights) */
            QPushButton#mac_quit {
                background-color: #FF5F57;
                border-radius: 6px;
                border: none;
            }
            QPushButton#mac_quit:hover {
                background-color: #FF3B30;
            }
            
            QPushButton#mac_close {
                background-color: #FFBD2E;
                border-radius: 6px;
                border: none;
            }
            QPushButton#mac_close:hover {
                background-color: #FF9F0A;
            }
            
            QPushButton#mac_maximize {
                background-color: #28C840;
                border-radius: 6px;
                border: none;
            }
            QPushButton#mac_maximize:hover {
                background-color: #30D158;
            }
            
            /* Settings Panel */
            QFrame#SettingsPanel {
                background-color: rgba(0, 0, 0, 30);
                border-radius: 8px;
            }
            QPushButton#LangBtn {
                background-color: rgba(255, 255, 255, 10);
                font-size: 11px;
                border-radius: 4px;
            }
            QTextEdit#PromptInput {
                font-size: 12px;
                background-color: rgba(0, 0, 0, 40);
            }
        """)

    def update_ui_text(self):
        # Update all labels
        self.status_label.setText(self.tr("status_ready") if not self.is_recording else self.tr("status_listening"))
        self.close_btn.setToolTip(self.tr("tooltip_close"))
        self.quit_btn.setToolTip(self.tr("tooltip_quit"))
        self.settings_btn.setToolTip(self.tr("tooltip_settings"))
        
        if self.is_recording:
             self.record_btn.setText(self.tr("btn_stop"))
        else:
             self.record_btn.setText(self.tr("btn_record"))
             
        self.refine_btn.setText(self.tr("btn_refine"))
        self.copy_btn.setText(self.tr("btn_copy"))
        
        self.text_area.setPlaceholderText(self.tr("placeholder_text"))

    def toggle_language(self):
        self.current_lang = "en" if self.current_lang == "zh" else "zh"
        self.update_ui_text()

    def toggle_settings(self):
        self.settings_panel.setVisible(not self.settings_panel.isVisible())
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def set_models_ready(self, ready: bool):
        self.is_model_ready = ready
        # self.record_btn.setEnabled(ready) # User wants it clickable with prompt
        # self.refine_btn.setEnabled(ready) # User wants it clickable with prompt
        if ready:
             self.status_label.setText(self.tr("status_ready"))

    def toggle_recording(self):
        if not self.is_model_ready:
            self.status_label.setText(self.tr("status_loading_model"))
            # Use lambda with weak ref or check state to avoid crash if window closed
            QTimer.singleShot(1500, self.reset_status_if_waiting)
            return

        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def reset_status_if_waiting(self):
        if self.status_label.text() == self.tr("status_loading_model"):
            self.status_label.setText(self.tr("status_ready"))

    def start_recording(self):
        self.is_recording = True
        self.status_label.setText(self.tr("status_listening"))
        self.record_btn.setText(self.tr("btn_stop"))
        self.record_btn.setObjectName("stop_btn")
        self.record_btn.setStyleSheet(self.record_btn.styleSheet()) # Force update
        self.text_area.setVisible(False)
        self.copy_btn.setVisible(False)
        self.start_recording_signal.emit()

    def stop_recording(self):
        self.is_recording = False
        self.status_label.setText(self.tr("status_processing"))
        self.record_btn.setText(self.tr("btn_record"))
        self.record_btn.setObjectName("")
        self.record_btn.setStyleSheet(self.record_btn.styleSheet())
        self.stop_recording_signal.emit()

    def set_prompt_mode(self, mode_key):
        preset = PROMPT_PRESETS.get(mode_key)
        if not preset:
            return
            
        # Update custom prompt text
        self.custom_prompt_text = preset["prompt"]
        
        # Update UI feedback (Optional: Toast or Tooltip)
        name = preset["name_zh"] if self.current_lang == "zh" else preset["name_en"]
        self.refine_btn.setToolTip(f"Mode: {name}")
        
        # Show a temporary status
        self.status_label.setText(f"Mode: {name}")
        QTimer.singleShot(1500, self.update_ui_text) # Reset after 1.5s

    def on_refine_clicked(self):
        if not self.is_model_ready:
            self.status_label.setText(self.tr("status_loading_model"))
            QTimer.singleShot(1500, self.reset_status_if_waiting)
            return

        if self.is_recording:
            return
        
        current_text = self.text_area.toPlainText().strip()
        custom_prompt = self.custom_prompt_text.strip()
        
        self.status_label.setText(self.tr("status_refining"))
        self.text_area.setVisible(False)
        self.copy_btn.setVisible(False)
        self.refine_btn.setEnabled(False)
        self.refine_selection_signal.emit(current_text, custom_prompt)

    def quit_app(self):
        # Force quit immediately
        import os
        import signal
        os.kill(os.getpid(), signal.SIGKILL)

    def update_text(self, text, is_final=True):
        self.text_area.setVisible(True)
        
        scrollbar = self.text_area.verticalScrollBar()
        # Check if user is near the bottom (allow some pixel tolerance)
        was_at_bottom = (scrollbar.value() >= (scrollbar.maximum() - 20))
        
        # Save old value to try to restore relative position if needed
        old_val = scrollbar.value()
        
        self.text_area.setText(text)
        
        if is_final:
             # Always scroll to end for final result
             scrollbar.setValue(scrollbar.maximum())
        elif was_at_bottom:
             # Auto-scroll if user was at bottom
             scrollbar.setValue(scrollbar.maximum())
        else:
             # User was scrolling up, keep position
             scrollbar.setValue(old_val)

        self.copy_btn.setVisible(True)
        self.refine_btn.setEnabled(True)
        
        if is_final:
            self.status_label.setText(self.tr("status_done"))
            
            # Reset recording UI if needed
            self.record_btn.setText(self.tr("btn_record"))
            self.record_btn.setObjectName("")
            self.record_btn.setStyleSheet(self.record_btn.styleSheet())
            self.is_recording = False
            
            self.adjustSize()
    
    def handle_error(self, msg):
        self.status_label.setText(self.tr("status_error"))
        self.text_area.setVisible(True)
        self.text_area.setText(msg)
        self.refine_btn.setEnabled(True)
        self.record_btn.setEnabled(True)
        self.record_btn.setText(self.tr("btn_record"))
        self.is_recording = False

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_area.toPlainText())
        self.status_label.setText(self.tr("status_copied"))
        QTimer.singleShot(2000, lambda: self.status_label.setText(self.tr("status_ready")))
