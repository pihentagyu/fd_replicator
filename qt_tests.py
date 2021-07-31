import sys
import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QTextEdit, QPushButton, QProgressBar, QLabel, QTabWidget, QListWidgetItem, QStackedWidget
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, pyqtSignal
from widgets.help_widget import HelpWidget
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
    def setUp(self):
        self.mw = MainWidget()

    def test_defaults(self):
        ## buttons
        self.assertEqual(self.mw.copy_action.isEnabled(), False)
        self.assertEqual(self.mw.button_dict['Refresh File List'].isEnabled(), True)
        self.assertEqual(self.mw.button_dict['Reset Devices'].isEnabled(), True)
        self.assertEqual(self.mw.button_dict['Copy'].isEnabled(), False)
        self.assertEqual(self.mw.button_dict['Help'].isEnabled(), True)
        self.assertEqual(self.mw.button_dict['Exit'].isEnabled(), True)


        ## List
        self.assertEqual(self.mw.list_widget_1.maximumHeight(), 70)
        self.assertEqual(self.mw.source_object, None)

    @patch('fd_replicator_main.ReplicatorMain.new_device', return_value=MagicMock())
    def test_select_source(self, mock_new_device):
        main_widget = MainWidget()
        item = QListWidgetItem('1')
        self.mw.list_widget_0.addItem(item)
        self.mw.list_widget_0.setCurrentItem(item)
        #self.mw.list_widget_0.currentItem().text = MagicMock(return_value='1')
        self.assertEqual(self.mw.list_widget_0.currentItem().text(), '1')
        source_object = mock_new_device(port=self.mw.list_widget_0.currentItem().text())    
        #source_object.get_device_from_port = MagicMock(return_value='/dev/sda')
        source_object.device = '/dev/sda'

        self.mw.get_source_object = MagicMock(return_value=source_object)
        source = self.mw.select_source()

        self.assertEqual(self.mw.source_object.device, '/dev/sda')
        self.assertEqual(self.mw.button_dict['Copy'].isEnabled(), True)
        self.assertEqual(self.mw.copy_action.isEnabled(), True)


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

        

if __name__ == '__main__':
    unittest.main()
