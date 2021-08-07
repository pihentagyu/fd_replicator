import sys
import unittest
from unittest.mock import MagicMock, patch, call
from PyQt5.QtGui import QPixmap, QTextCursor 
from PyQt5.QtWidgets import QApplication, QTextEdit, QPushButton, QProgressBar, QLabel, QTabWidget, QListWidgetItem, QStackedWidget, QGridLayout, QMessageBox
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, pyqtSignal
from widgets.help_widget import HelpWidget
from widgets.log_widget import QTextEditLogger, LogWidget
from widgets.main_widget import MainWidget, WorkerSignals, Worker, DeviceStatus, DeviceWidget
import widgets.main_widget as main_widget

app = QApplication(sys.argv)

from config.config import *
from replicator_qt import window

        
class WorkerSignalsTests(unittest.TestCase):
    def setUp(self):
        worker_signals = WorkerSignals()
        self.assertIsInstance(worker_signals.finished, pyqtSignal)
        self.assertIsInstance(worker_signals.error, pyqtSignal)
        self.assertIsInstance(worker_signals.result, pyqtSignal)
        self.assertIsInstance(worker_signals.progress, pyqtSignal)

class WorkerTests(unittest.TestCase):
    @patch('widgets.main_widget.WorkerSignals')
    def setUp(self, mock_WorkerSignals):
        self.fn = MagicMock()
        self.worker = Worker(self.fn)
        self.assertEqual(self.worker.fn, self.fn)
        self.assertEqual(self.worker.signals, mock_WorkerSignals())
    
    @patch('widgets.main_widget.traceback')
    @patch('widgets.main_widget.sys.exc_info', return_value=['exctype', 'value'])
    def test_run(self, mock_exc_info, mock_traceback):
        self.worker.run()
        self.worker.fn.assert_called()
        self.worker.signals.result.emit.assert_called()
        self.assertEqual(len(self.worker.signals.finished.mock_calls), 1)

        self.worker.fn = MagicMock(side_effect=Exception)
        self.worker.run()
        mock_traceback.print_exc.assert_called()
        mock_exc_info.assert_called()
        self.worker.signals.error.emit.assert_called()
        self.assertEqual(len(self.worker.signals.finished.mock_calls), 2)

class DeviceStatusTests(unittest.TestCase):
    def setUp(self):
        self.device_status = DeviceStatus()
        self.assertEqual(self.device_status.progress_bar, None)
        self.assertEqual(self.device_status.icon, None)
        self.assertEqual(self.device_status.status, None)

    def test_new_device(self):
        self.device_status.new_device()
        self.assertIsInstance(self.device_status.progress_bar, QProgressBar)
        self.assertIsInstance(self.device_status.icon, QLabel)
        self.assertEqual(self.device_status.icon.pixmap().width(), 15)
        self.assertEqual(self.device_status.icon.pixmap().height(), 15)

class DeviceWidgetTests(unittest.TestCase):
    @patch('widgets.main_widget.ReplicatorMain')
    def setUp(self, mock_replicator_main):
        self.device_widget = DeviceWidget()
        self.device_widget.replicator_main = MagicMock()
        self.device_widget.replicator_main.get_devices = MagicMock(return_value=(['01', '02'], 
            {'01': [('2.6', '/dev/sdh', (5, 1))],
                '02': [('2.1', '/dev/sdp', (3, 1))]})
            )
        self.mock_replicator_main = mock_replicator_main
        self.mock_replicator_main.assert_called()
        

    def test_add_progress_bar(self):
        with patch('widgets.main_widget.DeviceStatus') as mock_DeviceStatus:
            device_status = MagicMock()
            mock_DeviceStatus.return_value = device_status
            progress_bars = {}
            progress_bars = self.device_widget.add_progress_bar(progress_bars, 0, 0)
            print(progress_bars)
            self.assertIsInstance(progress_bars, dict)
            main_widget.DeviceStatus.assert_called()
            device_status.new_device.assert_called()
            self.assertEqual(progress_bars[(0,0)], device_status)

        with patch('widgets.main_widget.DeviceStatus') as mock_DeviceStatus:
            device_status = MagicMock()
            mock_DeviceStatus.return_value = device_status
            progress_bars = self.device_widget.add_progress_bar(progress_bars, 0, 1)
            self.assertEqual(len(progress_bars), 2)
            self.assertIn((0,0), progress_bars.keys())
            self.assertIn((0,1), progress_bars.keys())
            self.assertEqual(progress_bars[(0,1)], device_status)


    def test_create_base_table(self):
        #device_status = MagicMock()
        self.device_widget.usb_ports = ['01','02' ]
        self.base_table = self.device_widget.create_base_table()
        self.assertIsInstance(self.device_widget.tab_widget, QTabWidget)
        self.assertIsInstance(self.device_widget.progress_bars, dict)
        self.assertIsInstance(self.device_widget.all_ports, dict)
        self.assertEqual(len(self.device_widget.all_ports['01']), 54)
        self.assertEqual(self.device_widget.tab_widget.count(), 2)
        self.assertIsInstance(self.device_widget.tab_widget.children()[0], QStackedWidget)
        self.assertEqual(self.device_widget.tab_widget.tabText(0), '01')
        self.assertEqual(self.device_widget.tab_widget.tabText(1), '02')

    def test_get_active_devices(self):
        self.device_widget.progress_bars = {'01': {(5,1): MagicMock()}, '02': {(3,1): MagicMock()}}
        self.device_widget.devices = {'01': [('2.6', '/dev/sdh', (5, 1))],
                '02': [('2.1', '/dev/sdp', (3, 1))]}
        self.device_widget.get_active_devices('01')
        print(self.device_widget.active_devices)

    def test_set_led_on_active(self):
        self.device_widget.all_ports = {'01': {(5,1)}, '02': {(3,1), (4,2)}}
        self.device_widget.replicator_main.get_devices = MagicMock(return_value=(['01', '02'], 
            {'01': [('2.6', '/dev/sdh', (5, 1))],
                '02': [
                    ('2.1', '/dev/sdp', (3, 1)),
                    ('2.2', '/dev/sdp', (4, 2))
                    ]})
            )
        self.device_widget.progress_bars = {'01': {(5,1): MagicMock()}, '02': {(3,1): MagicMock(), (4,2): MagicMock()}}
        self.device_widget.num_dev_labels = {}
        for hub in ['01', '02']:
            num_dev_label = MagicMock()
            num_dev_label.clear = MagicMock()
            num_dev_label.setText = MagicMock()
            self.device_widget.num_dev_labels[hub] = num_dev_label
        self.device_widget.set_led_on_active()

        self.device_widget.num_dev_labels['01'].setText.assert_called_with('1 Device')
        self.device_widget.num_dev_labels['02'].setText.assert_called_with('2 Devices')

    def test_reset_all(self):
        main_widget.USB_PORTS = ['01', '02']
        for hub in ['01', '02']:
            for col in (0,1):
                for row in range(HUB_ROWS):
                    device_status = MagicMock()
                    device_status.progress_bar = MagicMock()
                    device_status.icon = MagicMock()
                    if not self.device_widget.progress_bars.get(hub):
                        self.device_widget.progress_bars[hub] = {(row, col): device_status}
                    else:
                        self.device_widget.progress_bars[hub][(row, col)] = device_status
        self.device_widget.reset_all()
        self.device_widget.progress_bars['01'][(0,0)].progress_bar.reset.assert_called()
        self.device_widget.progress_bars['02'][(26,0)].progress_bar.reset.assert_called()
        self.device_widget.progress_bars['01'][(0,0)].icon.clear.assert_called()
        self.device_widget.progress_bars['02'][(26,0)].icon.clear.assert_called()
        self.assertEqual(self.device_widget.progress_bars['01'][(0,0)].status, None)
        self.assertEqual(self.device_widget.progress_bars['02'][(26,0)].status, None)


class MainWidgetTests(unittest.TestCase):
    @patch('widgets.main_widget.ReplicatorMain')
    @patch('widgets.main_widget.MainWidget.init_ui')
    def setUp(self, mock_init_ui,  mock_ReplicatorMain):
        self.mw = MainWidget()
        self.mock_init_ui = mock_init_ui
        self.mock_ReplicatorMain = mock_ReplicatorMain

    def test_init(self):
        self.mock_ReplicatorMain.assert_called()
        self.mock_init_ui.assert_called()
        self.assertEqual(self.mw.debug, False)
        self.assertEqual(self.mw.source_object, None)
        self.assertEqual(self.mw.checksums, True)
        self.mock_init_ui.assert_called()

    def test_defaults(self):
        self.mw.replicator_main.get_prev_thread_count = MagicMock(return_value=5)
        self.mw.init_config = MagicMock()
        self.mw.initialize_devices = MagicMock()
        self.add_source_list = MagicMock()
        self.mw.init_ui()

        self.mw.replicator_main.get_prev_thread_count.assert_called()
        self.assertEqual(self.mw.thread_num, 5)
        self.mw.init_config.assert_called()

        self.assertEqual(self.mw.windowTitle(), 'Devices')

        '''Actions defaults tests'''
        self.assertEqual(self.mw.refresh_action.text(), '&Refresh')
        self.assertEqual(self.mw.refresh_action.shortcut(), 'Ctrl+R')
        self.assertEqual(self.mw.refresh_action.statusTip(), 'Refresh')

        self.assertEqual(self.mw.reset_action.text(), '&Reset Devices')
        self.assertEqual(self.mw.reset_action.shortcut(), 'Ctrl+Alt+R')
        self.assertEqual(self.mw.reset_action.statusTip(), 'Reset Devices')

        self.assertEqual(self.mw.copy_action.text(), '&Copy To Devices')
        self.assertEqual(self.mw.copy_action.shortcut(), 'Ctrl+C')
        self.assertEqual(self.mw.copy_action.statusTip(), 'Copy To Devices')
        self.assertEqual(self.mw.copy_action.isEnabled(), False)

        self.assertEqual(self.mw.logs_action.text(), '&Logs')
        self.assertEqual(self.mw.logs_action.shortcut(), 'Ctrl+L')
        self.assertEqual(self.mw.logs_action.statusTip(), 'View Logs')

        self.assertEqual(self.mw.email_action.text(), '&Email')
        self.assertEqual(self.mw.email_action.shortcut(), 'Ctrl+E')
        self.assertEqual(self.mw.email_action.statusTip(), 'Email')

        self.assertEqual(self.mw.help_action.text(), '&Help')
        self.assertEqual(self.mw.help_action.shortcut(), 'Ctrl+H')
        self.assertEqual(self.mw.help_action.statusTip(), 'Help')

        self.assertEqual(self.mw.exit_action.text(), '&Quit')
        self.assertEqual(self.mw.exit_action.shortcut(), 'Ctrl+Q')
        self.assertEqual(self.mw.exit_action.statusTip(), 'Exit Application')

        '''Menu defaults tests'''

        self.assertIsInstance(self.mw.main_widget.layout(), QGridLayout)

        '''buttons''' 

        self.assertEqual(self.mw.button_dict['Refresh File List'].isEnabled(), True)
        self.assertEqual(self.mw.button_dict['Reset Devices'].isEnabled(), True)
        self.assertEqual(self.mw.button_dict['Copy'].isEnabled(), False)
        self.assertEqual(self.mw.button_dict['Help'].isEnabled(), True)
        self.assertEqual(self.mw.button_dict['Exit'].isEnabled(), True)

        '''Label''' 

        self.assertEqual(self.mw.hub_label.text(), 'Source Devices (Double-click to begin):')

        '''List'''

        self.assertEqual(self.mw.list_widget_1.maximumHeight(), 70)
        self.assertEqual(self.mw.source_object, None)

    @patch('widgets.main_widget.QErrorMessage')
    def test_init_config(self, mock_QErrorMessage):
        self.mw.replicator_main.check_and_create_dir = MagicMock(return_value=1)
        self.mw.init_config()
        mock_QErrorMessage.assert_called()


    def test_initialize_devices(self):
        self.mw.replicator_main.get_devices = MagicMock(return_value=(['01', '02'], 
            {'01': [('2.6', '/dev/sdh', (5, 1))],
                '02': [
                    ('2.1', '/dev/sdp', (3, 1)),
                    ('2.2', '/dev/sdp', (4, 2))
                    ]})
            )
        self.mw.device_widget = MagicMock()
        self.mw.device_widget.set_led_on_active = MagicMock()
        self.mw.initialize_devices()
        self.mw.replicator_main.get_devices.assert_called()
        self.assertEqual(self.mw.total_devices, 3)
        self.mw.device_widget.set_led_on_active.assert_called()

    @patch('widgets.main_widget.QTimer')
    def test_start_timer(self, mock_QTimer):
        self.mw.check_devices = MagicMock()
        self.mw.start_timer()
        mock_QTimer.assert_called()
        self.mw.timer.timeout.connect.assert_called_with(self.mw.check_devices)
        self.mw.timer.start.assert_called_with(6000)

    def test_create_checksums(self):
        state = Qt.Checked
        self.mw.create_checksums(state)
        self.assertEqual(self.mw.checksums, True)
        state = ''
        self.mw.create_checksums(state)
        self.assertEqual(self.mw.checksums, False)

    def test_set_workers(self):
        self.mw.thread_line_edit = MagicMock()
        self.mw.thread_line_edit.text = MagicMock(return_value='5')
        self.mw.replicator_main.save_prev_thread_num = MagicMock()
        self.mw.set_workers()
        self.assertEqual(self.mw.thread_num, 5)
        self.mw.replicator_main.save_prev_thread_num.assert_called_with(5)

    @patch('widgets.main_widget.LogWidget')
    def test_view_logs(self, mock_LogWidget):
        self.mw.view_logs()
        mock_LogWidget.assert_called()
        self.mw.log_window.show.assert_called()

    @patch('widgets.main_widget.EmailSetupWidget')
    def test_email_notification(self, mock_EmailSetupWidget):
        email_settings = {'from_addr': 'foobar@baz', 'to_addr': 'foobar2@baz'}
        self.mw.replicator_main.get_email_settings = MagicMock(return_value=email_settings)
        self.mw.email_notification()
        self.mw.replicator_main.get_email_settings.assert_called()
        mock_EmailSetupWidget.assert_called_with(prev_email_settings=email_settings)
        self.mw.email_setup_window.show.assert_called()

    @patch('widgets.main_widget.HelpWidget')
    def test_help(self, mock_HelpWidget):
        self.mw.help()
        self.mw.help_window.show.assert_called()

    def test_prepare_checksums(self):
        self.mw.source_object = MagicMock()
        self.mw.source_object.prepare_to_copy = MagicMock(return_value=0)
        self.mw.checksums = False
        fn = MagicMock()
        worker = Worker(fn)
        status = self.mw.prepare_checksums(progress_callback=worker.signals.progress)
        self.mw.source_object.prepare_to_copy.assert_called_with(checksums=False, progress_callback=worker.signals.progress)
        self.assertEqual(status, 0)

    def test_copy(self):
        hub = '01'
        device = ('2.6', '/dev/sdh', (5, 1))
        self.mw.source_object = MagicMock()
        self.mw.source_object.device = MagicMock()
        self.mw.source_object.device_dir = MagicMock()
        self.mw.source_object.source_mdsums = MagicMock()
        self.mw.checksums = True
        new_device = MagicMock()
        self.mw.replicator_main.new_device = MagicMock(return_value=new_device)
        fn = MagicMock()
        worker = Worker(fn)
        progress_callback = worker.signals.progress

        dest_object, results = self.mw.copy(hub, device, progress_callback=progress_callback)
        self.mw.replicator_main.new_device.assert_called_with(device='/dev/sdh', port='2.6', hub='01', hub_coordinates=(5,1), source_mdsums=self.mw.source_object.source_mdsums)
        new_device.copy.assert_called_with(self.mw.source_object.device, self.mw.source_object.device_dir, checksums=True, progress_callback=progress_callback)
        
    @patch('widgets.main_widget.QMessageBox.question', return_value=QMessageBox.Yes)
    @patch('widgets.main_widget.QThreadPool', side_effect=[MagicMock(), MagicMock()])
    @patch('widgets.main_widget.Worker')
    def test_copy_to_devices(self, mock_Worker, mock_QThreadPool, mock_question):
        self.mw.source_object = MagicMock()
        self.mw.source_object.delete_ignored = MagicMock(return_value=0)
        self.mw.refresh = MagicMock()
        self.mw.timer = MagicMock()
        self.mw.thread_num = 7
        self.mw.checksums_progress_bar = MagicMock()
        self.mw.prepare_checksums = MagicMock()
        self.mw.checksums_finished_actions = MagicMock()
        self.mw.update_checksums_progress_bar = MagicMock()

        self.mw.copy_to_devices()

        self.mw.source_object.delete_ignored.assert_called()
        self.mw.refresh.assert_called()
        self.mw.timer.stop.assert_called()
        self.assertEqual(self.mw.finished_devices, 0)
        self.assertEqual(len(mock_QThreadPool.call_args_list), 2)
        self.mw.threadpool.setMaxThreadCount.assert_called_with(7)
        self.mw.checksums_threadpool.setMaxThreadCount.assert_called_with(1)
        self.mw.checksums_progress_bar.setValue.assert_called_with(0)
        mock_Worker.assert_called_with(self.mw.prepare_checksums)
        self.mw.checksums_worker.signals.finished.connect.assert_called_with(self.mw.checksums_finished_actions)
        self.mw.checksums_worker.signals.progress.connect.assert_called_with(self.mw.update_checksums_progress_bar)
        self.mw.checksums_threadpool.start.assert_called_with(self.mw.checksums_worker)


    @patch('widgets.main_widget.Worker', side_effect=[MagicMock(), MagicMock()])
    def test_copy_files(self, mock_Worker):
        self.mw.initialize_devices = MagicMock()
        self.mw.hubs = ['01', '02']
        self.mw.devices =  {'01': [('2.6', '/dev/sdh', (5, 1))],
                '02': [('2.1', '/dev/sdp', (3, 1))]}
        self.mw.threadpool = MagicMock()
        self.mw.update_result = MagicMock()
        self.mw.do_completed_actions = MagicMock()
        self.mw.update_checksums_progress_bar = MagicMock()
        
        self.mw.copy_files()

        self.assertEqual(len(mock_Worker.call_args_list), 2)
        self.mw.worker.signals.result.connect.assert_called_with(self.mw.update_result)
        self.mw.worker.signals.finished.connect.assert_called_with(self.mw.do_completed_actions)
        self.mw.worker.signals.progress.connect.assert_called_with(self.mw.update_progress_bar)
        self.mw.threadpool.start.assert_called_with(self.mw.worker)

    @patch('widgets.main_widget.QMessageBox.warning')
    @patch('widgets.main_widget.QMessageBox.Ok')
    def test_get_checksums_results(self, mock_Ok, mock_warning):
        self.mw.checksums_progress_bar = MagicMock()
        self.mw.copy_files = MagicMock()

        self.mw.get_checksums_results(0)

        self.mw.checksums_progress_bar.setValue.assert_called_with(100)
        self.mw.copy_files.assert_called()
        mock_warning.assert_not_called()

        self.mw.checksums_progress_bar = MagicMock()
        self.mw.copy_files = MagicMock()

        self.mw.get_checksums_results(1)

        self.mw.checksums_progress_bar.setValue.assert_not_called()
        self.mw.copy_files.assert_not_called()
        mock_warning.assert_called_with(self.mw, 'Warning', 'Unable to create initial checksums! Please check logs', mock_Ok)

    def test_update_checksums_progress_bar(self):
        self.mw.checksums_progress_bar = MagicMock()

        self.mw.update_checksums_progress_bar([50])

        self.mw.checksums_progress_bar.setValue.assert_called_with(50)
        

    def test_checksums_finished_actions(self):
        pass 

    def test_update_progress_bar(self):
        self.mw.device_widget = MagicMock()

        self.mw.update_progress_bar([50, '01', (5,1)])

        self.mw.device_widget.progress_bars['01'][(5,1)].progress_bar.setValue.assert_called_with(50)

    @patch('widgets.main_widget.QPixmap')
    def test_update_result(self, mock_QPixmap):
        device_object = MagicMock()
        device_object.hub = '01'
        device_object.hub_coordinates = (5,1)
        result = [device_object, 0]
        self.mw.device_widget = MagicMock()

        self.mw.update_result(result)
        
        self.assertEqual(self.mw.device_widget.progress_bars['01'][(5,1)].status, 0)
        self.mw.device_widget.progress_bars['01'][(5,1)].progress_bar.setValue.assert_called_with(100)

        ########

        device_object = MagicMock()
        device_object.hub = '01'
        device_object.hub_coordinates = (5,1)
        result = [device_object, 1]
        self.mw.device_widget = MagicMock()
        led_icon  = self.mw.device_widget.progress_bars['01'][(5,1)].icon
        self.mw.failed_devices = 0

        self.mw.update_result(result)
        
        self.assertEqual(self.mw.failed_devices, 1)
        self.assertEqual(self.mw.device_widget.progress_bars['01'][(5,1)].status, 1)
        self.mw.device_widget.progress_bars['02'][(5,1)].progress_bar.reset.assert_called()
        mock_QPixmap.assert_called_with('config/icons/led-circle-red.png')
        mock_QPixmap().scaled.assert_called_with(15,15)
        led_icon.setPixmap.assert_called_with(mock_QPixmap().scaled())

    @patch('widgets.main_widget.time.time', return_value = 1000)
    @patch('widgets.main_widget.QMessageBox')
    def test_do_completed_actions(self, mock_QMessageBox, mock_time):
        self.mw.finished_devices = 0
        self.mw.start_time = 500
        self.mw.total_devices = 54

        self.mw.do_completed_actions()

        self.assertEqual(self.mw.finished_devices, 1)
        
        self.mw.finished_devices = 53
        self.mw.total_devices = 54
        self.mw.start_time = 500
        self.mw.source_object = MagicMock()
        self.mw.timer = MagicMock()
        self.mw.replicator_main = MagicMock()
        self.mw.file_list = ['file1', 'file2', 'file3']
        self.mw.failed_devices = 5

        self.mw.do_completed_actions()

        self.assertEqual(self.mw.finished_devices, 54)
        self.mw.source_object.check_mountpoint.assert_called()
        self.mw.timer.start.assert_called()
        self.mw.replicator_main.send_notification.assert_called_with(54, 5, 500, self.mw.file_list)
        mock_QMessageBox.information.assert_called_with(self.mw, 'Finished', 'Copied 54 devices. Failures: 5. Time Elapsed 500', mock_QMessageBox.Ok)

    def test_get_source_dir_label(self):
        self.mw.source_directory = '/media'
        self.mw.source_dir_label = MagicMock()

        self.mw.get_source_dir_label()
        self.mw.source_dir_label.clear.assert_called()
        self.mw.source_dir_label.setText.assert_called_with('/media')

    def test_get_source_object(self):
        self.mw.replicator_main = MagicMock()
        self.mw.list_widget_0 = MagicMock()
        source_object = MagicMock()
        self.mw.replicator_main.new_device = MagicMock(return_value=source_object)

        result = self.mw.get_source_object()

        self.assertEqual(result, source_object)
        self.mw.replicator_main.new_device.assert_called_with(port=self.mw.list_widget_0.currentItem().text())
        source_object.get_device_from_port.assert_called()

    @patch('widgets.main_widget.logging')
    def test_select_source(self, mock_logging):
        self.mw.get_source_object = MagicMock()
        self.mw.button_dict = {'Copy': MagicMock()}
        self.mw.copy_action = MagicMock()
        self.mw.add_list = MagicMock()
        self.mw.check_devices = MagicMock()

        self.mw.select_source()

        mock_logging.info.assert_called_with(self.mw.source_object.device)
        self.mw.button_dict['Copy'].setEnabled.assert_called_with(True)
        self.mw.copy_action.setEnabled.assert_called_with(True)
        self.mw.add_list.assert_called()
        self.mw.check_devices.assert_called()

    @patch('widgets.main_widget.QListWidgetItem')
    def test_refresh(self, mock_QListWidgetItem):
        self.mw.list_widget_1 = MagicMock()
        self.mw.source_object = MagicMock()
        self.mw.source_object.device = '/dev/sda'
        self.mw.source_object.get_file_list = MagicMock(return_value=['a.avi', 'b.avi'])

        self.mw.refresh()

        self.mw.list_widget_1.clear.assert_called()
        self.mw.source_object.get_file_list.assert_called()
        self.assertEqual(self.mw.file_list, ['a.avi', 'b.avi'])
        self.assertEqual(mock_QListWidgetItem.mock_calls[0], call('a.avi'))
        self.assertEqual(mock_QListWidgetItem.mock_calls[1], call('b.avi'))
        self.assertEqual(len(self.mw.list_widget_1.addItem.mock_calls), 2)

    def test_add_source_list(self):
        self.mw.replicator_main.get_direct_dev = MagicMock(return_value={'/dev/sda': '01'})
        self.mw.grid = MagicMock()

        result = self.mw.add_source_list()

        self.assertEqual(result, True)
        self.assertEqual(self.mw.list_widget_0.contextMenuPolicy(), 2)
        self.mw.grid.addWidget.assert_called_with(self.mw.list_widget_0, 1,1,3,2)
        self.mw.replicator_main.get_direct_dev.assert_called()
        self.assertEqual(self.mw.source_ports, ['01'])
        self.assertEqual(self.mw.list_widget_0.count(), 1)
        self.assertEqual(self.mw.list_widget_0.item(0).text(), '01')
        self.assertEqual(self.mw.list_widget_0.selectionMode(), 3)


    def test_check_devices(self):
        self.mw.add_source_list = MagicMock()
        self.mw.device_widget = MagicMock()

        self.mw.check_devices()

        self.mw.add_source_list.assert_called()
        self.mw.device_widget.set_led_on_active.assert_called()

    def test_reset_devices(self):
        self.mw.checksums_progress_bar = MagicMock()
        self.mw.device_widget = MagicMock()

        self.mw.reset_devices()

        self.mw.checksums_progress_bar.reset.assert_called()
        self.mw.device_widget.reset_all.assert_called()
        self.mw.device_widget.set_led_on_active.assert_called()

    def test_exit(self):
        self.mw.close = MagicMock()
        self.mw.exit()
        self.mw.close.assert_called
            

class HelpWidgetTests(unittest.TestCase):
    @patch('widgets.help_widget.ReplicatorMain')
    @patch('widgets.help_widget.HelpWidget.init_ui')
    def setUp(self, mock_init_ui, mock_ReplicatorMain):
        #HelpWidget.init_ui = MagicMock()
        self.help_widget = HelpWidget()
        mock_init_ui.assert_called()

    def test_init_ui(self):
        self.help_widget.close = MagicMock()
        self.help_widget.replicator_main.get_text_from_file = MagicMock(return_value='This is the text')
        self.help_widget.init_ui()
        popup_widget = self.help_widget.popup_widget
        self.assertEqual(popup_widget.size().height(), 800)
        self.assertEqual(popup_widget.size().width(), 600)
        self.assertEqual(self.help_widget.windowTitle(), 'Device Replicator Help Window')
        help_text = self.help_widget.help_text
        self.assertEqual(help_text.isReadOnly(), True)
        self.assertEqual(help_text.toPlainText(), 'This is the text')
        grid = self.help_widget.grid
        self.assertIsInstance(grid.itemAtPosition(0,0).widget(), QTextEdit)
        self.assertIsInstance(grid.itemAtPosition(10,0).widget(), QPushButton)
        close_button = self.help_widget.close_button
        QTest.mouseClick(close_button, Qt.LeftButton)
        self.help_widget.close.assert_called()

        
class QTextEditLoggerTests(unittest.TestCase):
    def setUp(self):
        self.log_widget = LogWidget()
        self.logger = QTextEditLogger(self.log_widget)

    def test_defaults(self):
        self.assertEqual(self.logger.widget.isReadOnly(), True)

class LogWidgetTests(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
