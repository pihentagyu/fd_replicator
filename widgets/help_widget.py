from PyQt5.QtWidgets import QWidget, QTextEdit, QGridLayout, QPushButton

from config.config import HELP_FILE
from fd_replicator_main import ReplicatorMain

class HelpWidget(QWidget):
    def __init__(self):
        self.replicator_main = ReplicatorMain()
        QWidget.__init__(self)
        self.popup_widget = QWidget(self)
        self.init_ui()

    def init_ui(self):
        self.popup_widget.resize(600,800)
        self.setWindowTitle('Device Replicator Help Window')    

        self.help_text = QTextEdit()
        text = self.replicator_main.get_text_from_file(HELP_FILE)
        self.help_text.setHtml(text)
        self.help_text.setReadOnly(True)

        #self.help_text.setLineWrapMode(QTextEdit.NoWrap);
        #self.help_text.setStyleSheet('background-color:grey')
        self.grid = QGridLayout()
        self.popup_widget.setLayout(self.grid)
        self.grid.addWidget(self.help_text, 0,0)
        self.close_button = QPushButton('Close')
        self.grid.addWidget(self.close_button, 10,0)
        self.close_button.clicked.connect(self.close)

