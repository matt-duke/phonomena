import sys
import os

# Restore PyQt5 debug behaviour (print exception) https://stackoverflow.com/questions/33736819/pyqt-no-error-msg-traceback-on-exit
if __debug__:
    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)

    sys.excepthook = except_hook

def run():
    from gui import main
    import common
    common.importSettings()
    common.init()

    main.start()

if __name__ == '__main__':
    if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
        #running as bundle
        try:
            run()
        except Exception as e:
            print(e)
            input()
    else:
        run()
