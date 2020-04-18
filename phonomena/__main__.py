import multiprocessing as mp

def run():
    import common
    from gui import main
    common.configureLogger()
    common. setTempdir()
    common.init()
    common.loadSettings()
    main.start()

if __name__ == '__main__':
    mp.freeze_support()
    mp.set_start_method('spawn')
    run()
