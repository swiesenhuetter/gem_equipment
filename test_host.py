import sys
import time
import logging
import secsgem.common
import secsgem.gem
import secsgem.hsms
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QLineEdit, QPushButton, QHBoxLayout, QTextEdit
)

class LogHandler(QObject, logging.Handler):
    new_log = Signal(str)

    def __init__(self):
        QObject.__init__(self)
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.new_log.emit(msg)

class TestHostWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SECS/GEM Host Simulator")
        self.resize(800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        
        # Host Control Buttons
        self.control_layout = QHBoxLayout()
        self.enable_button = QPushButton("Enable Host")
        self.enable_button.clicked.connect(self.on_enable_host)
        self.control_layout.addWidget(self.enable_button)
        
        self.disable_button = QPushButton("Disable Host")
        self.disable_button.clicked.connect(self.on_disable_host)
        self.control_layout.addWidget(self.disable_button)
        
        self.layout.addLayout(self.control_layout)

        self.recipe_label = QLabel("Recipe Name:")
        self.layout.addWidget(self.recipe_label)
        
        self.recipe_input = QLineEdit()
        self.recipe_input.setText("example_recipe.rcp")
        self.layout.addWidget(self.recipe_input)
        
        self.send_button = QPushButton("Send Remote Command")
        self.send_button.clicked.connect(self.on_send_command)
        self.layout.addWidget(self.send_button)
        
        # Log Area
        self.log_label = QLabel("Communication Log:")
        self.layout.addWidget(self.log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.layout.addWidget(self.log_area)
        
        # Setup Logging
        self.log_handler = LogHandler()
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.log_handler.new_log.connect(self.append_log)
        
        # Configure secsgem logger to capture all messages
        secsgem_logger = logging.getLogger("secsgem")
        secsgem_logger.setLevel(logging.DEBUG)
        secsgem_logger.addHandler(self.log_handler)
        
        self.settings = secsgem.hsms.HsmsSettings(
            address="127.0.0.1",
            port=5000,
            connect_mode=secsgem.hsms.HsmsConnectMode.ACTIVE,
            session_id=0
        )
        
        self.host = TestHost(self.settings)
        self.host.enable()
        
    def append_log(self, text):
        self.log_area.append(text)
        # Auto scroll to bottom
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_enable_host(self):
        self.append_log("Enabling host...")
        self.host.enable()

    def on_disable_host(self):
        self.append_log("Disabling host...")
        self.host.disable()

    def on_send_command(self):
        recipe_name = self.recipe_input.text()
        # Send S2F41 (Host Command)
        self.append_log(f"Sending VerifyRecipe with RecipeName={recipe_name}")
        
        # send_remote_command waits for the S2F42 reply and returns it
        try:
            response = self.host.send_remote_command("VerifyRecipe", [("RecipeName", recipe_name)])
            self.append_log(f"Received S2F42 Reply: {response}")
        except Exception as e:
            self.append_log(f"Error sending command: {e}")

    def closeEvent(self, event):
        self.host.disable()
        super().closeEvent(event)

class TestHost(secsgem.gem.GemHostHandler):

    def __init__(self, settings):
        super().__init__(settings)

    # Override to ignore unhandled event reports
    def _on_s06f11(self, handler, message):
        """Handle S6F11 (Event Report) - just acknowledge."""
        self.send_response(self.stream_function(6, 12)(0), message.header.system)
        return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestHostWindow()
    window.show()
    sys.exit(app.exec())
