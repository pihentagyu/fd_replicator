import sys
import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QTextEdit, QPushButton
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, pyqtSignal
from widgets.help_widget import HelpWidget
from widgets.main_widget import MainWidget, WorkerSignals, Worker
import widgets.help_widget

app = QApplication(sys.argv)


class WorkerSignalsTests(unittest.TestCase):
    def setUp(self):
        worker_signals = WorkerSignals()
        self.assertIsInstance(worker_signals.finished, pyqtSignal)
        self.assertIsInstance(worker_signals.error, pyqtSignal)
        self.assertIsInstance(worker_signals.result, pyqtSignal)
        self.assertIsInstance(worker_signals.progress, pyqtSignal)

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.x = lambda x: x
        self.worker = Worker(self.x)
        self.worker.signals = MagicMock()
        self.worker.fn = MagicMock()
    
    def test_run(self):
        #self.worker.signals.finished = MagicMock()
        self.worker.run()
        self.worker.fn.assert_called_with(self.x) 
        



class MainWidgetTests(unittest.TestCase):
    def setUp(self):
        pass



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
