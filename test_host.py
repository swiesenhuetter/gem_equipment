import sys
import os
import logging
from os import link

from secsgem.common import state_machine
import secsgem.gem
import secsgem.hsms
from secsgem.secs.data_items import ACKC5, ALCD
from secsgem.secs.variables import U4

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QLineEdit, QPushButton, QHBoxLayout, QTextEdit, QComboBox
)
from secsgem.hsms import HsmsMessage
from secsgem.secs.data_items import ACKC5

secsgem_logger = logging.getLogger("secsgem")


class LogHandler(QObject, logging.Handler):
    new_log = Signal(str)
    def __init__(self, window):
        QObject.__init__(self)
        logging.Handler.__init__(self)
        self.new_log.connect(window.append_log)
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        secsgem_logger.addHandler(self)

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
        self.enable_button.clicked.connect(self.enable_host)
        self.control_layout.addWidget(self.enable_button)
        
        self.disable_button = QPushButton("Disable Host")
        self.disable_button.clicked.connect(self.disable_host)
        self.control_layout.addWidget(self.disable_button)
        
        self.layout.addLayout(self.control_layout)

        self.recipe_label = QLabel("Recipe Name:")
        self.layout.addWidget(self.recipe_label)
        
        # Recipe Input and Verify Button Layout
        self.recipe_layout = QHBoxLayout()
        
        self.recipe_input = QLineEdit()
        self.recipe_input.setText("example_recipe.rcp")
        self.recipe_layout.addWidget(self.recipe_input)
        
        self.send_button = QPushButton("Verify Recipe")
        self.send_button.clicked.connect(self.on_send_command)
        self.recipe_layout.addWidget(self.send_button)
        
        self.layout.addLayout(self.recipe_layout)
        
        self.request_recipes_button = QPushButton("Request Recipe List (S7F19)")
        self.request_recipes_button.clicked.connect(self.on_request_recipes)
        self.layout.addWidget(self.request_recipes_button)
        
        self.rcp_label = QLabel("Wafer Recipes (.rcp):")
        self.layout.addWidget(self.rcp_label)
        self.rcp_combo = QComboBox()
        self.layout.addWidget(self.rcp_combo)
        
        self.job_label = QLabel("Batch Jobs (.job):")
        self.layout.addWidget(self.job_label)
        self.job_combo = QComboBox()
        self.layout.addWidget(self.job_combo)
        
        # Log Area
        self.log_label = QLabel("Communication Log:")
        self.layout.addWidget(self.log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.layout.addWidget(self.log_area)
        
        # Setup Logging

        self.settings = secsgem.hsms.HsmsSettings(
            address="127.0.0.1",
            port=5000,
            connect_mode=secsgem.hsms.HsmsConnectMode.ACTIVE,
            session_id=0,
            t6 = 5  # Wait 5 seconds for a response
        )

        self.host = TestHost(self.settings)
        self.enable_host()
        
    def append_log(self, text):
        self.log_area.append(text)
        # Auto scroll to bottom
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def enable_host(self):
        self.append_log("Enabling host...")
        try:
            self.host.enable()
        except state_machine.WrongSourceStateError:
            self.append_log("Error: Host is already enabled.")


    def disable_host(self):
        self.append_log("Disabling host...")
        try:
            self.host.disable()
        except state_machine.WrongSourceStateError:
            self.append_log("Error: Host is not enabled.")

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

    def on_request_recipes(self):
        try:
            response = self.host.get_process_program_list()
            self.append_log(f"Received S7F20 Reply: {response}")
            
            self.rcp_combo.clear()
            self.job_combo.clear()
            
            for r in response:
                name = os.path.basename(r)
                if name.lower().endswith('.rcp'):
                    self.rcp_combo.addItem(name, r)
                elif name.lower().endswith('.job'):
                    self.job_combo.addItem(name, r)

        except Exception as e:
            self.append_log(f"Error sending command: {e}")
        


    def closeEvent(self, event):
        self.disable_host()
        super().closeEvent(event)

class TestHost(secsgem.gem.GemHostHandler):

    def __init__(self, settings):
        super().__init__(settings)
        self.register_stream_function(6, 11, TestHost.event_handler)

    def _on_alarm_received(self, handler, alarm_id, alarm_status, alarm_text):
        secsgem_logger.info(f"Received event id:{alarm_id.get()} str:{alarm_text.get()} status:{alarm_status.get()}")
        if alarm_status.get() & ALCD.ALARM_SET:
            secsgem_logger.info(f"Alarm {alarm_id} is set")
        else:
            secsgem_logger.info(f"Alarm {alarm_id} is cleared")

        return ACKC5.ACCEPTED

    @staticmethod
    def on_connect(event):
        secsgem_logger.info(f"Connected Handler: {event["connection"].connection_state.current}")

    def event_handler(self, message: HsmsMessage):
        secsgem_logger.info(f"Received S6F11 Event: {message}")
        """Handle S6F11 (Event Report) - just acknowledge."""
        self.send_response(self.stream_function(6, 12)(0), message.header.system)
        return None


    # # Override to ignore unhandled event reports
    # def _on_s06f11(self, handler, message):
    #     secsgem_logger.info(f"Received S6F11 Event: {message}")
    #     """Handle S6F11 (Event Report) - just acknowledge."""
    #     self.send_response(self.stream_function(6, 12)(0), message.header.system)
    #     return None



if __name__ == "__main__":
    # Configure secsgem logger to capture all messages
    secsgem_logger.setLevel(logging.DEBUG)
    app = QApplication(sys.argv)
    window = TestHostWindow()
    log_handler = LogHandler(window)
    window.show()
    sys.exit(app.exec())
