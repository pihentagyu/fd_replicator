 
import logging
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QTimer, QThreadPool, QRunnable, pyqtSlot
from PyQt5.QtGui import QPalette, QTextCursor, QPixmap, QIntValidator
import re
import sys 
import time
import traceback

from fd_replicator_main import ReplicatorMain
from widgets.help_widget import HelpWidget
from widgets.log_widget import LogWidget
from widgets.email_setup_window import EmailSetupWidget

from config.config import *


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(tuple)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        #while True:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class DeviceStatus:
    def __init__(self):
        self.progress_bar = None
        self.icon = None
        self.status = None

    def new_device(self):
        self.progress_bar = QProgressBar() 
        self.icon = QLabel()
        self.icon.setPixmap(QPixmap(ICON_GREY_LED).scaled(15,15))
        self.progress_bar.setMaximum(100)
        
class DeviceWidget:
    def __init__(self, **kwargs):
        self.replicator_main = ReplicatorMain()
        self.usb_ports = USB_PORTS if isinstance(USB_PORTS, list) or isinstance(USB_PORTS, tuple) else []
        self.progress_bars = {}

    def add_progress_bar(self, progress_bars, row, col):
        device_status = DeviceStatus()
        device_status.new_device()
        progress_bars[(row, col)] = device_status
        return progress_bars

    def create_base_table(self):
        self.tab_widget = QTabWidget()
        self.all_ports = {}
        self.num_dev_labels = {}
        for hub in self.usb_ports:
            all_ports = set()
            print(hub)
            self.hub_widget = QWidget()
            self.hub_widget.resize(200, self.hub_widget.height())
            self.hub_grid = QGridLayout()
            self.hub_widget.setLayout(self.hub_grid)

            hub_progress_bars = {}
            for col in (0,1):
                new_col = col * 3
                for row in range(HUB_ROWS):
                    text_label = QLabel()
                    text_label.clear()
                    text_label.setText(str(row + 1))
                    all_ports.add((row, col))
                    hub_progress_bars = self.add_progress_bar(hub_progress_bars, row, col)
                    if col == 0:
                        self.hub_grid.addWidget(text_label, row, new_col)
                        self.hub_grid.addWidget(hub_progress_bars[(row, col)].icon, row, new_col+1)
                        self.hub_grid.addWidget(hub_progress_bars[(row, col)].progress_bar, row, new_col+2)
                    else:
                        self.hub_grid.addWidget(text_label, row, new_col+2)
                        self.hub_grid.addWidget(hub_progress_bars[(row, col)].icon, row, new_col+1)
                        self.hub_grid.addWidget(hub_progress_bars[(row, col)].progress_bar, row, new_col)
            self.all_ports[hub] = all_ports

            self.progress_bars[hub] = hub_progress_bars
            num_dev_label = QLabel()
            num_dev_label.clear()
            num_dev_label.setText('No Devices')
            num_dev_label.setAlignment(Qt.AlignRight)
            self.num_dev_labels[hub] = num_dev_label
            self.hub_grid.addWidget(num_dev_label, 28, 3)

            self.tab_widget.addTab(self.hub_widget, str(hub))
        return self.tab_widget

    def get_active_devices(self, hub):
        self.active_devices = set()
        for device in self.devices[hub]:
            row, col = device[2]
            new_col = col * 2
            self.active_devices.add((row, col))
            progress_bar = self.progress_bars[hub][(row, col)]
            icon = progress_bar.icon
            prog_bar = progress_bar.progress_bar
            #prog_bar.setValue(0)
            icon.clear()
            '''If status is 0 (Success) or None (Not finished)'''
            icon.setPixmap(QPixmap(ICON_GREEN_LED).scaled(15,15)) if not progress_bar.status else icon.setPixmap(QPixmap(ICON_RED_LED).scaled(15,15))


    def set_led_on_active(self):
        '''Checks devices, then updates the progress bars and leds accordingly'''

        '''Get the hubs and devices'''
        self.hubs, self.devices = self.replicator_main.get_devices()

        '''Update if there are devices available, else clear all'''
        if self.hubs and self.devices:
            for hub in self.hubs:
                '''Change the icon to green on active devices'''
                self.get_active_devices(hub)
                for row, col in self.all_ports[hub] - self.active_devices:
                    progress_bar = self.progress_bars[hub][(row, col)]
                    icon = progress_bar.icon
                    prog_bar = progress_bar.progress_bar
                    prog_bar.reset()
                    icon.clear()
                    icon.setPixmap(QPixmap(ICON_RED_LED).scaled(15,15)) if progress_bar.status == 1 else icon.setPixmap(QPixmap(ICON_GREY_LED).scaled(15,15))
                num_devices = len(self.devices[hub])
                self.num_dev_labels[hub].clear()
                self.num_dev_labels[hub].setText(f'{num_devices} Devices') if num_devices != 1 else self.num_dev_labels[hub].setText(f'{num_devices} Device')
        else:
            self.reset_all()

    def reset_all(self):
        for hub in USB_PORTS:
            for col in (0,1):
                new_col = col * 2
                for row in range(HUB_ROWS):
                    self.progress_bars[hub][(row,col)].progress_bar.reset()
                    self.progress_bars[hub][(row,col)].icon.clear()
                    self.progress_bars[hub][(row,col)].status = None

class MainWidget(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWidget, self).__init__(*args, **kwargs)
        self.replicator_main = ReplicatorMain()
        self.debug = False
        QMainWindow.__init__(self)
        self.source_object = None
        self.checksums=True
        self.init_ui()

    def init_ui(self):
        self.thread_num = self.replicator_main.get_prev_thread_count()
        self.init_config()
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.setWindowTitle('Devices')    
        self._create_actions()
        self._create_menubar()
        self._create_grid()

        '''Actions'''

        '''File Actions'''

    def _create_actions(self):
        self.refresh_action = QAction('&Refresh', self)
        self.refresh_action.setShortcut('Ctrl+R')
        self.refresh_action.setStatusTip('Refresh')
        self.refresh_action.triggered.connect(self.refresh)

        self.reset_action = QAction('&Reset Devices', self)
        self.reset_action.setShortcut('Ctrl+Alt+R')
        self.reset_action.setStatusTip('Reset Devices')
        self.reset_action.triggered.connect(self.reset_devices)
        
        self.copy_action = QAction('&Copy To Devices', self)
        self.copy_action.setShortcut('Ctrl+C')
        self.copy_action.setEnabled(False)
        self.copy_action.setStatusTip('Copy To Devices')
        self.copy_action.triggered.connect(self.copy_to_devices)

        self.logs_action = QAction('&Logs', self)
        self.logs_action.setShortcut('Ctrl+L')
        self.logs_action.setStatusTip('View Logs')
        self.logs_action.triggered.connect(self.view_logs)

        self.email_action = QAction('&Email', self)
        self.email_action.setShortcut('Ctrl+E')
        self.email_action.setStatusTip('Email')
        self.email_action.triggered.connect(self.email_notification)

        self.help_action = QAction('&Help', self)
        self.help_action.setShortcut('Ctrl+H')
        self.help_action.setStatusTip('Help')
        self.help_action.triggered.connect(self.help)

        self.exit_action = QAction('&Quit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit Application')
        self.exit_action.triggered.connect(self.exit)

    def _create_menubar(self):
        '''Menubar'''
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')

        metadata_menu = menubar.addMenu('&Devices')
        metadata_menu.addAction(self.reset_action)
        metadata_menu.addAction(self.refresh_action)
        metadata_menu.addAction(self.copy_action)

        tools_menu = menubar.addMenu('&Tools')

        report_menu = menubar.addMenu('&Run')
        metadata_menu.addAction(self.copy_action)

        help_menu = menubar.addMenu('&Help')
        help_menu.addAction(self.help_action)
        help_menu.addAction(self.logs_action)

        help_menu = menubar.addMenu('&Setup')
        help_menu.addAction(self.email_action)

    def _create_grid(self):
        self.grid = QGridLayout()
        self.main_widget.setLayout(self.grid)

        '''Buttons on left'''
        buttons = (
                None,
            {'title': 'Refresh File List', 'action': self.refresh, 'enabled': True},
            {'title': 'Reset Devices', 'action': self.reset_devices, 'enabled': True},
            {'title': 'Copy', 'action': self.copy_to_devices, 'enabled': False},
            {'title': 'View Logs', 'action': self.view_logs},
            {'title': 'Setup Notifications', 'action': self.email_notification},
            {'title': 'Help', 'action': self.help},
            {'title': 'Exit', 'action': self.exit},
            )

        self.button_dict = {}


        for row, button in enumerate(buttons):
            if button == None:
                continue
            style = button.get('style', None)
            enabled = button.get('enabled', None)
            action = button.get('action', None)
            button['widget'] = QPushButton(button['title'])
            if style != None:
                button['widget'].setStyleSheet(style)
            if enabled != None:
                button['widget'].setEnabled(enabled)
            self.button_dict[button['title']] = button['widget']
            self.grid.addWidget(button['widget'], row, 0)
            if action != None:
                button['widget'].clicked.connect(action)

        row += 1

        '''Add list widget on right. Lists files on selected dir'''

        '''Add list widget with devices'''
        self.hub_label = QLabel()
        self.hub_label.setText('Source Devices (Double-click to begin):')
        self.grid.addWidget(self.hub_label, 0, 1)

        self.add_source_list()

        self.list_widget_1 = QListWidget()
        self.list_widget_1.setMaximumHeight(70)
        self.list_widget_1.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.list_widget_1.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.grid.addWidget(self.list_widget_1, 4, 1, 4, 2)

        row +=4

        thread_label = QLabel()
        thread_label.setAlignment(Qt.AlignRight)
        thread_label.clear()
        thread_label.setText('Threads:')
        self.grid.addWidget(thread_label, row, 1)

        self.thread_line_edit = QLineEdit()
        self.thread_line_edit.setPlaceholderText(str(self.thread_num))
        self.thread_line_edit.setValidator(QIntValidator())
        self.thread_line_edit.setMaxLength(2)
        self.thread_line_edit.setAlignment(Qt.AlignRight)
        self.thread_line_edit.editingFinished.connect(self.set_workers)
        self.grid.addWidget(self.thread_line_edit, row, 2)

        widget_check_box = QCheckBox('Checksums')
        widget_check_box.setChecked(True)
        self.grid.addWidget(widget_check_box, row, 0)
        widget_check_box.stateChanged.connect(self.create_checksums)

        row += 1

        self.checksums_progress_bar = QProgressBar() 
        self.checksums_label = QLabel()
        self.checksums_label.setText('Initial Checksums Progress')
        self.grid.addWidget(self.checksums_label, row, 0)
        self.grid.addWidget(self.checksums_progress_bar, row, 1, 1, 2)

        row += 1

        self.dev_widget_row = row + 3

        self.device_widget = DeviceWidget()
        self.tab_widget = self.device_widget.create_base_table()
        self.initialize_devices()
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.grid.addWidget(self.scroll_area, self.dev_widget_row, 0, 27, 3)
        self.scroll_area.setWidget(self.tab_widget)
        #self.device_widget.set_led_on_active()
        
        self.start_timer()

    def init_config(self):
        error = self.replicator_main.check_and_create_dir(self.replicator_main.config_dir)
        if error:
            error_dialog = QErrorMessage()
            error_dialog.showMessage('An Error Occurred!')

    def initialize_devices(self):
        self.hubs, self.devices = self.replicator_main.get_devices()
        self.total_devices = sum([len(self.devices[h]) for h in self.devices])
        self.device_widget.set_led_on_active()

    def start_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_devices)
        self.timer.start(6000)

    def create_checksums(self, state):
        if state == Qt.Checked:
            self.checksums = True
        else:
            self.checksums = False
    
    def set_workers(self):
        self.thread_num = int(self.thread_line_edit.text())
        self.replicator_main.save_prev_thread_num(self.thread_num)
        #print(self.thread_num)
        
    def view_logs(self):
        self.log_window = LogWidget()
        self.log_window.show()

    def email_notification(self):
        prev_email_settings = self.replicator_main.get_email_settings()
        self.email_setup_window = EmailSetupWidget(prev_email_settings=prev_email_settings)
        self.email_setup_window.show()

    def help(self):
        self.help_window = HelpWidget()
        self.help_window.show()

    def prepare_checksums(self, **kwargs):
        '''Prepare the source object for copying - getting checksums, self.checksums is True'''
        progress_callback = kwargs.get('progress_callback')
        status = self.source_object.prepare_to_copy(checksums=self.checksums, progress_callback=progress_callback)
        return status

    def copy(self, hub, device, **kwargs):
        '''Copy files to the chip (device)'''
        dest_object = self.replicator_main.new_device(device=device[1], port=device[0], hub=hub, hub_coordinates=device[2], source_mdsums=self.source_object.source_mdsums)
        progress_callback = kwargs.get('progress_callback')
        results = dest_object.copy(self.source_object.device, self.source_object.device_dir, checksums=self.checksums, progress_callback=progress_callback)
        return dest_object, results


    def copy_to_devices(self):
        '''Initiate the copying of files to the devices. Threads here are used for preparation (checksums). '''
        confirm = QMessageBox.question(self, 'Copy Files?', 'Copy to devices?', QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.start_time = time.time()
            status = self.source_object.delete_ignored()
            if status != 0:
                logging.info('Unable to remove unnecessary files from source device')
                confirm = QMessageBox.question(self, 'Unable to remove hidden files', 'Unable to remove hidden files! Continue?', QMessageBox.Yes | QMessageBox.No)
                if confirm == QMessageBox.No:
                    QMessageBox.warning(self, 'Warning', 'Not copying files!', QMessageBox.Ok)
                    return
            self.refresh()
            self.timer.stop()
            self.finished_devices = 0
            ### MULTITHREADING
            self.threadpool = QThreadPool()
            self.checksums_threadpool = QThreadPool()
            self.threadpool.setMaxThreadCount(self.thread_num)
            self.checksums_threadpool.setMaxThreadCount(1)

            self.checksums_progress_bar.setValue(0)
            '''Prepare source, create checksums if self.checksums=True'''
            self.checksums_worker = Worker(self.prepare_checksums)
            '''If preparation was successful, this will also copy files'''
            self.checksums_worker.signals.result.connect(self.get_checksums_results)
            '''Once finished copying, calculate how many are done, etc.'''
            self.checksums_worker.signals.finished.connect(self.checksums_finished_actions)
            '''update progress bar as copying progresses'''
            self.checksums_worker.signals.progress.connect(self.update_checksums_progress_bar)
            self.checksums_threadpool.start(self.checksums_worker)

    def copy_files(self):
        '''Copy files to the devices using multithreading'''
        self.initialize_devices() # Get devices one last time
        self.failed_devices = 0 # Failed devices reset to 0
        for hub in self.hubs:
            for device in self.devices[hub]:
                self.worker = Worker(self.copy, hub, device)
                self.worker.signals.result.connect(self.update_result)
                self.worker.signals.finished.connect(self.do_completed_actions)
                self.worker.signals.progress.connect(self.update_progress_bar)
                self.threadpool.start(self.worker)

    def get_checksums_results(self, result):
        #print(result)
        if result == 0: # If success
            self.checksums_progress_bar.setValue(100) # Set progrress bar to 100%
            self.copy_files() # Start copying files
        else:
            QMessageBox.warning(self, 'Warning', 'Unable to create initial checksums! Please check logs', QMessageBox.Ok)

    def update_checksums_progress_bar(self, p):
        n = p[0]
        progress_bar = self.checksums_progress_bar
        progress_bar.setValue(n)

    def checksums_finished_actions(self):
        #print('finished')
        #self.checksums_progress_bar.setValue(100)
        pass

    def update_progress_bar(self, p):
        n, hub, hub_coordinates = p
        #print(n, hub, hub_coordinates)
        progress_bar = self.device_widget.progress_bars[hub][hub_coordinates].progress_bar
        progress_bar.setValue(n)

    def update_result(self, result):
        device_object = result[0]

        progress_info = self.device_widget.progress_bars[device_object.hub][device_object.hub_coordinates]
        progress_bar = progress_info.progress_bar
        progress_info.status = result[1]
        if result[1] == 0:
            progress_bar.setValue(100)
        else:
            self.failed_devices += 1
            led_icon = progress_info.icon
            progress_bar.reset()
            led_icon.setPixmap(QPixmap(ICON_RED_LED).scaled(15,15))

    def do_completed_actions(self):
        self.finished_devices += 1
        total_time = time.time() - self.start_time
        if self.finished_devices == self.total_devices:
            logging.info('Total devices completed: {}. Failed: {}. Time Elapsed: {}'.format(self.finished_devices, self.failed_devices, total_time))
            self.source_object.check_mountpoint()
            self.timer.start()
            self.replicator_main.send_notification(self.finished_devices, self.failed_devices, total_time, self.file_list)
            QMessageBox.information(self, 'Finished', 'Copied {} devices. Failures: {}. Time Elapsed {}'.format(self.finished_devices, self.failed_devices, total_time), QMessageBox.Ok)

    def get_source_dir_label(self):
        label = self.source_directory if self.source_directory else ''
        self.source_dir_label.clear()
        self.source_dir_label.setText(f'{label}')

        '''Delete selected items'''

    def get_source_object(self):
        source_object = self.replicator_main.new_device(port=self.list_widget_0.currentItem().text())    
        source_object.get_device_from_port()
        return source_object

    def select_source(self):
        self.source_object = self.get_source_object()
        logging.info(self.source_object.device)
        if self.source_object.device:
            self.button_dict['Copy'].setEnabled(True) # Enable copy button
            self.copy_action.setEnabled(True)
            self.add_list()
            self.check_devices()

    def add_list(self):
        success = self.refresh() # Populate the list
        if success:
            self.show_list = True
            self.list_widget_1.show()

    def __del__(self):
        '''Restore sys.stdout'''
        sys.stdout = sys.__stdout__


    def refresh(self):
        success = False
        self.file_list = []
        self.list_widget_1.clear()
        out = None
        #try:
        if not self.source_object:
            return False
        if self.source_object.device:
            out = self.source_object.get_file_list()
        else:
            QMessageBox.warning(self, 'Warning', 'Please choose a port before refreshing', QMessageBox.Ok)
            return False
        if out:
            self.file_list = out
            '''get a list of missing files'''
            for f in self.file_list:
                item = QListWidgetItem(f)
                self.list_widget_1.addItem(item)
            success = True
        else:
            QMessageBox.warning(self, 'Error', 'Error: No files found!', QMessageBox.Ok)
            success = False
        return success

    def add_source_list(self):
        success = True
        self.list_widget_0 = QListWidget()
        self.list_widget_0.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.list_widget_0.itemActivated.connect(self.select_source)
        self.grid.addWidget(self.list_widget_0, 1, 1, 3, 2)

        devices = self.replicator_main.get_direct_dev()

        try:
            self.source_ports = list(devices.values())
        except AttributeError:
            self.source_ports = []
        '''get a list of missing files'''
        for f in self.source_ports:
            item = QListWidgetItem(f)
            self.list_widget_0.addItem(item)
        self.list_widget_0.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.list_widget_0.show()
        return success

    def check_devices(self):
        #First get device information via replicator_main
        #Then open check_devices DisplayDevices() to display the devices
        self.add_source_list()
        self.device_widget.set_led_on_active()

    def reset_devices(self):
        self.checksums_progress_bar.reset()
        self.device_widget.reset_all()
        self.device_widget.set_led_on_active()

    def exit(self):
        self.close()
