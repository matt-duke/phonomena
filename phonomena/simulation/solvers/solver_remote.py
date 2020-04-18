import time
import tempfile, shutil, os
from pathlib import Path
import threading, queue
import multiprocessing as mp
from multiprocessing.managers import BaseManager

import dill
import h5py
import numpy as np
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import requests
import re

if __name__ == '__main__':
    import sys
    file = Path(__file__).resolve()
    sys.path.append(str(file.parents[2]))

from simulation import base_solver

import logging
logger = logging.getLogger(__name__)

cfg = {
    "ip": 'localhost',
    "rpc_port": 5000,
    "sync_port": 5001,
    "http_port": 80,
}

SERVER_DIR = Path.cwd().joinpath('server')
AUTHKEY = b'phonomena'
FORMAT_STR = '[%(msecs)04d]:%(levelname)s:[%(name)s:%(lineno)d]:%(message)s'
LOG_LEVEL = logging.INFO
if __debug__:
    LOG_LEVEL = logging.DEBUG
LOG_FILE = 'solver.log'

class FileServer(ThreadingHTTPServer):
    #https://gist.github.com/bradmontgomery/2219997
    class Handler(SimpleHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def do_GET(self):
            super().do_GET()

        def do_POST(self):
            logger.info("POST request received.")
            self._set_headers()
            file_length = int(self.headers['content-length'])
            data = self.rfile.read(file_length)
            filename = re.search(b'name="([\w.]+)";', data)[1]
            filename = SERVER_DIR.joinpath(filename.decode("utf-8"))

            data = re.sub(b'\A--[\W\w]+"\\r\\n\\r\\n', b'', data)
            data = re.sub(b'\\r\\n--\w+--\\r\\n$', b'', data)
            with open(filename, mode='wb') as f:
                f.write(data)

    def __init__(self, ip, port):
        os.chdir(SERVER_DIR)
        super().__init__((ip, port), FileServer.Handler)

class Server(base_solver.BaseSolver):
    def __init__(self):
        self.configureLogger()
        super().__init__(logger)
        self.name = "remote"
        self.description = "<p></p>"
        self.cfg = {**cfg, **self.cfg}

        self.set_tmpdir(SERVER_DIR)

        self.m = None
        self.g = None
        self.steps = None
        self.status = mp.Queue()
        self.running = mp.Event()
        self.progress = mp.Queue()

        self.rpc = SimpleXMLRPCServer((cfg['ip'], cfg['rpc_port']), allow_none=True)
        self.rpc.register_introspection_functions()
        self.rpc.register_function(self.testRPC)
        self.rpc.register_function(self.init)
        self.rpc.register_function(self.run)
        self.http = FileServer(
            ip=cfg['ip'],
            port=cfg['http_port']
        )

        class SyncManager(BaseManager): pass
        SyncManager.register('get_status', callable=lambda: self.status)
        SyncManager.register('get_progress', callable=lambda: self.progress)
        SyncManager.register('get_running', callable=lambda: self.running)
        self.sync = SyncManager(address=(cfg['ip'], cfg['sync_port']), authkey=AUTHKEY)

    def configureLogger(self):
        rootlogger = logging.getLogger()
        rootlogger.setLevel(LOG_LEVEL)

        logFormatter = logging.Formatter(FORMAT_STR)

        fileHandler = logging.FileHandler(LOG_FILE, mode='w')
        fileHandler.setLevel(LOG_LEVEL)
        fileHandler.setFormatter(logFormatter)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        consoleHandler.setLevel(LOG_LEVEL)

        rootlogger.addHandler(fileHandler)
        rootlogger.addHandler(consoleHandler)

        modules = []
        for m in modules:
            l = logging.getLogger(m)
            l.setLevel(logging.WARNING)

    def testRPC(self):
        return True

    def start(self):
        logger.debug("Starting rpc server.")
        rpcd = threading.Thread(target=self.rpc.serve_forever)
        rpcd.start()
        logger.debug("Starting http server.")
        httpd = threading.Thread(target=self.http.serve_forever)
        httpd.start()
        logger.debug("Starting sync server.")
        sync = threading.Thread(target=self.sync.get_server().serve_forever)
        sync.start()
        logger.info('Servers started. Remote solver ready.')

    @staticmethod
    def set_tmpdir(dir):
        temp = Path.cwd().joinpath(dir)
        if temp.is_dir():
            try:
                shutil.rmtree(temp)
                temp.mkdir()
            except Exception as e:
                logger.warning("Unable to clear tmp folder: {}".format(e))
        else:
            temp.mkdir()
        os.environ["TMPDIR"] = str(temp)

    def init(self, grid, material, steps, cfg):
        grid = SERVER_DIR.joinpath(grid)
        material = SERVER_DIR.joinpath(material)
        logger.info("Loading pickled objects.")
        g = dill.load(open(grid, mode='rb'))
        m = dill.load(open(material, mode='rb'))
        self.cfg = cfg
        super().init(g, m, steps)
        return self.file

    def run(self):
        t = threading.Thread(target=super().run)
        t.start()

class Client:
    def __init__(self):
        self.rpc = ServerProxy('http://{}:{}'.format(cfg['ip'], cfg['rpc_port']))

        class SyncManager(BaseManager): pass
        SyncManager.register('get_status')
        SyncManager.register('get_progress')
        SyncManager.register('get_running')

        self.sync = SyncManager(address=(cfg['ip'], cfg['sync_port']), authkey=AUTHKEY)
        self.sync.connect()
        self.status = self.sync.get_status()
        self.running = self.sync.get_running()
        self.progress = self.sync.get_progress()

    def send_obj(self, obj, file):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()
        with open(tmp_file.name, mode='wb') as f:
            dill.dump(obj, f)
        url = 'http://{}:{}/post'.format(cfg['ip'], cfg['http_port'])
        logger.debug("Sending file: {}".format(url))
        with open(tmp_file.name, mode='rb') as f:
            requests.post(url, files={file: f})
        os.remove(tmp_file.name)

    def get_file(self, file):
        url = 'http://{}:{}/{}'.format(cfg['ip'],cfg['http_port'],file)
        logger.debug("Downloading file: {}".format(url))
        r = requests.get(url, allow_redirects=True)
        f = tempfile.NamedTemporaryFile()
        f.close()
        with open(f.name, 'wb') as f:
            f.write(r.content)

    def testRPC(self):
        return self.rpc.testRPC()


class Solver(base_solver.BaseSolver):

    def __init__(self):
        super().__init__(logger)
        self.name = "remote"
        self.description = "<p></p>"
        self.cfg = {**cfg, **self.cfg}

    def init(self, grid, material, steps):
        global cfg
        cfg = self.cfg

        grid.buildMesh()
        grid.update()
        material.update()

        self.client = Client()
        self.client.send_obj(grid, 'grid.dill')
        self.client.send_obj(material, 'material.dill')
        self.file = self.client.rpc.init('grid.dill', 'material.dill', steps, self.cfg)

    def run(self, *args, **kwargs):
        try:
            signals = kwargs['signals']
        except KeyError:
            from gui.worker import WorkerSignals
            signals = WorkerSignals()

        self.client.rpc.run()
        self.client.running.wait()
        self.running.set()
        while self.client.running.is_set():
            if not self.running.is_set():
                self.cancel()
                self.logger.warning("Simulation cancelled.")
                break
            try:
                msg = str(self.client.status.get(block=False))
                signals.status.emit(msg)
                logger.info("status: {}".format(msg))
                progess = str(self.client.progress.get(block=False))
                signals.progress.emit(progress)
                logger.info("progress: {}".format(msg))
                time.sleep(0.1)
            except queue.Empty:
                pass
        signals.progress.emit(100)
        self.client.get_file(self.file)
        self.running.clear()

if __name__ == '__main__':
    s = Server()
    s.start()
