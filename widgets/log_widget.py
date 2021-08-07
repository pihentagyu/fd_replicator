import sys
from PyQt5.QtWidgets import QWidget, QTextEdit, QGridLayout, QPushButton, QPlainTextEdit
import logging

# Uncomment below for terminal log messages
# logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(name)s - %(levelname)s - %(message)s')

class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class LogWidget(QWidget):
    def __init__(self):

        QWidget.__init__(self)
        self.popup_widget = QWidget(self)
        self.popup_widget.resize(600,800)
        self.setWindowTitle('FD Devices Log Window')    

        log_text_box = QTextEditLogger(self)
        # You can format what is printed to text box
        #logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(log_text_box)
        # You can control the logging level
        logging.getLogger().setLevel(logging.INFO)
        logging.info('hello, this is a test')

        grid = QGridLayout()
        self.popup_widget.setLayout(grid)
        grid.addWidget(log_text_box.widget, 0,0)
        close_button = QPushButton('Close')
        grid.addWidget(close_button, 10,0)
        close_button.clicked.connect(self.close)

