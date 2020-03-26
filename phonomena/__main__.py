
def run():
    import common
    common.configureLogger()
    common.set_tmpdir()
    common.importSettings()
    common.init()

    from gui import main
    main.start()

if __name__ == '__main__':
    run()
