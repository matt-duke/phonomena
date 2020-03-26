import logging
from PyQt5.QtWidgets import *

FORMAT_STR = '[%(msecs)04d]:%(levelname)s:[%(name)s:%(lineno)d]:%(message)s'
LOG_LEVEL = logging.INFO
if __debug__:
    LOG_LEVEL = logging.DEBUG

class QPlainTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()

        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(FORMAT_STR)
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        msg = "{}\n".format(msg)
        self.widget.textCursor().insertText(msg)

    def write(self, m):
        pass
