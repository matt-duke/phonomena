import sys
import os
import cProfile

# Restore PyQt5 bedug behaviour (print exception) https://stackoverflow.com/questions/33736819/pyqt-no-error-msg-traceback-on-exit
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

def run():
    from gui import main
    import common
    common.import_settings()
    common.init()

    main.start()


if __name__ == '__main__':

    if __debug__:
        import sys
        sys.excepthook = except_hook

    if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
        #running as bundle
        try:
            run()
        except Exception as e:
            print(e)
            input()
    else:
        #settings_path = os.path.join('..', settings_path)
        #cProfile.run('run()')
        run()
