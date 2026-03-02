
import sys
from PySide6.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)
        
        self.full_think = "This is a long thinking process that should be collapsed initially."
        self.answer = "This is the actual answer."
        self.think_expanded = False
        
        self.update_display()
        
        self.btn = QPushButton("Simulate Stream")
        self.btn.clicked.connect(self.simulate_stream)
        self.layout.addWidget(self.btn)
        
    def update_display(self):
        if self.think_expanded:
            html = f"""
            <div style='color: #888;'>
                {self.full_think} 
                <a href='toggle_think' style='color: #FFF; text-decoration: none;'>[Collapse]</a>
            </div>
            <br>
            <div>{self.answer}</div>
            """
        else:
            short_think = self.full_think[:10]
            html = f"""
            <div style='color: #888;'>
                {short_think}... 
                <a href='toggle_think' style='color: #FFF; text-decoration: none;'>[Expand]</a>
            </div>
            <br>
            <div>{self.answer}</div>
            """
        
        self.text_edit.setHtml(html)
        
        # Connect anchor click if not already (QTextEdit doesn't have a direct signal for this in setHtml, 
        # need to handle interaction)
        # Actually QTextEdit handles links if setReadOnly(True) and setOpenExternalLinks(False)
        # We need to catch the link click.
        
    def simulate_stream(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = TestWindow()
    w.show()
    
    # We need to hook into the anchorClicked signal of the viewport or similar? 
    # QTextBrowser has anchorClicked. QTextEdit does not. 
    # But we can subclass or use text interaction.
    
    sys.exit(app.exec())
