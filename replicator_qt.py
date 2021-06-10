#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# GUI backend for fd_replicator, based on QT5.
import logging
import os
import sys

from config.config import LOGFILE
from PyQt5.QtWidgets import QApplication
from widgets.main_widget import FdMainWidget

def logging_init():
    log_dir = os.path.split(LOGFILE)[0]
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(filename=LOGFILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    #except KeyError:
    #    #cs.initial_setup()
    #    self.get_vars()
    #        #self.local_settings = cs.startup()

def window():
    logging_init()
    app = QApplication(sys.argv)
    ex = GochipMainWidget()
    ex.show()
    ret = app.exec_()
    #sys.exit(ret)
    return ex


if __name__ == '__main__':
    window()    
