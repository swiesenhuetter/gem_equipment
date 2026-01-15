import sys
import time
import secsgem.common
import secsgem.gem
import secsgem.hsms
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QLineEdit, QPushButton, QHBoxLayout
)

class TestHostWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SECS/GEM Host Simulator")
        
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
        
        self.settings = secsgem.hsms.HsmsSettings(
            address="127.0.0.1",
            port=5000,
            connect_mode=secsgem.hsms.HsmsConnectMode.ACTIVE,
            session_id=0
        )
        
        self.host = TestHost(self.settings)
        self.host.enable()
        
    def on_enable_host(self):
        print("Enabling host...")
        self.host.enable()

    def on_disable_host(self):
        print("Disabling host...")
        self.host.disable()

    def on_send_command(self):
        recipe_name = self.recipe_input.text()
        # Send S2F41 (Host Command)
        print(f"Sending VerifyRecipe with RecipeName={recipe_name}")
        self.host.send_remote_command("VerifyRecipe", [("RecipeName", recipe_name)])

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
