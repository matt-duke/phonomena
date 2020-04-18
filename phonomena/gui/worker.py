from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import traceback, sys
from threading import Event

class WorkerSignals(QtCore.QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data - function finished

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    quit
        No data - force close thread

    '''
    finished = pyqtSignal()
    success = pyqtSignal()
    error = pyqtSignal(tuple)
    warning = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    quit = pyqtSignal()

class Worker(QtCore.QRunnable):
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
        # Function fn should have *args and **kwargs defined at minimum
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['signals'] = self.signals

        self.setAutoDelete(True)

        try:
            callback_fns = self.kwargs['callback_fns']
            self.signals.error.connect(callback_fns['error'])
            self.signals.status.connect(callback_fns['status'])
            self.signals.progress.connect(callback_fns['progress'])
        except KeyError:
            pass

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
            self.signals.success.emit()  # No errors
        finally:
            self.signals.finished.emit()  # Done
