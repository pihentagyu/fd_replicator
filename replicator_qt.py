#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# GUI backend for fd_replicator, based on QT5.
import logging
import os
import sys

from config.config import LOGFILE
from PyQt5.QtWidgets import QApplication
from widgets.main_widget import MainWidget

def logging_init():
    log_dir = os.path.split(LOGFILE)[0]
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(filename=LOGFILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def window():
    '''Initiate the logging and open the main widget window'''
    logging_init()
    app = QApplication(sys.argv)
    ex = MainWidget()
    ex.show()
    ret = app.exec_()
    return ex

if __name__ == '__main__':
    window()    
