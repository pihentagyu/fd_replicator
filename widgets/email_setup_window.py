from PyQt5.QtWidgets import *


class EmailForm(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        #self.form_widget = QWidget(self)
        self.form_group_box = QGroupBox('Email Setup')
        #self.grid = QGridLayout()

        self.setWindowTitle('Edit Email Info')    
        self.load_data()

        self.form_group_box.setLayout(self.form_layout)
        scroll = QScrollArea()
        scroll.setWidget(self.form_group_box)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(200)
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        layout.addStretch()

        from_email_label = QLabel(self)
        from_email_label.setText('From')
        self.form_layout.addRow(from_email_label)

        to_email_label = QLabel(self)
        to_email_label.setText('To')
        self.form_layout.addRow(to_email_label)

        cc_email_label = QLabel(self)
        cc_email_label.setText('CC')
        self.form_layout.addRow(cc_email_label)

        bcc_email_label = QLabel(self)
        bcc_email_label.setText('BCC')
        self.form_layout.addRow(bcc_email_label)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save)

        self.reset_button = QPushButton('Restore Defaults')
        self.reset_button.clicked.connect(self.reset)
        
        layout.addWidget(self.save_button)
        layout.addWidget(self.reset_button)

    def load_data(self):
        self.form_layout = QFormLayout()

    def save(self):
        pass

    def reset(self):
        pass

class EmailSetupWidget(QWidget):
    def __init__(self, **kwargs):
        self.email_form = EmailForm()
        QWidget.__init__(self)
        self.popup_widget = QWidget(self)
        self.popup_widget.resize(600,800)
        self.setWindowTitle('Email Setup Window')    

        grid = QGridLayout()
        self.popup_widget.setLayout(grid)
        grid.addWidget(self.email_form, 0,0)
        close_button = QPushButton('Close')
        grid.addWidget(close_button, 5,0)
        close_button.clicked.connect(self.close)

