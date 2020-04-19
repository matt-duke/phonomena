
def run():
    import common
    from gui import main
    common.startupTasks()
    common.findSolvers()
    common.loadSettings()
    main.start()

if __name__ == '__main__':
    run()
