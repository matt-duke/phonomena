import sys
import os
import cProfile

settings_path = "data/settings.ini"

def run():
    from gui import main
    import common
    common.import_settings(settings_path)
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
        settings_path = os.path.join('..', settings_path)
        #cProfile.run('run()')
        run()
