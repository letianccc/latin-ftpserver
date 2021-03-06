
import threading
from v2.ftp.server_ import FTPServer
import os
import subprocess
from v2.ftp.config import *
import unittest
from v2.ftp.client_ import Client
import shutil




class BaseTest(unittest.TestCase):
    def setUp(self):
        setup_clear()
        self.init_file()
        self.init_end()
        self.init_login()
        self.init_data_connect()
        self.clients = []

    def tearDown(self):
        self.clear_file()
        self.clear_client()
        self.server.stop()
        # thread.join()
        # kill_python_process()
        # kill_port()
        # kill_python_process()

    def clear_client(self):
        self.client.clear()

    def init_end(self):
        # server_addr = (SERVER_IP, SERVER_PORT)
        thread = self.run_server(SERVER_ADDR)
        self.server = thread.server
        self.init_client()
        # self.client = Client(SERVER_ADDR)
        # self.client.connect(SERVER_ADDR)

    def init_client(self):
        self.client = Client(SERVER_ADDR)
        self.client.connect(SERVER_ADDR)


    def init_login(self):
        request = 'USER %s\r\n' % DEFAULT_USERNAME
        self.client.send_request(request)
        resp = self.client.get_response(request)

        request = 'PASS %s\r\n' % DEFAULT_PASSWORD
        self.client.send_request(request)
        resp = self.client.get_response(request)

    def init_data_connect(self):
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)

    def init_file(self):
        self.target_filename = 'p'
        self.server_path = 'server_fs/%s' % self.target_filename

    def run_server(self, server_addr):
        thread = ServerThread(server_addr)
        thread.daemon = True
        thread.start()
        while not thread.is_run():
            pass
        return thread

class ServerThread(threading.Thread):
    def __init__(self, server_addr):
        super(ServerThread, self).__init__()
        self.server_addr = server_addr
        self.server = None

    def run(self):
        self.server = FTPServer()
        self.server.listen(self.server_addr)
        self.server.run()

    def is_run(self):
        if self.server:
            return self.server.is_run()
        return False

open('output', 'w').close()
def log(*args, **kwargs):
    print(*args, **kwargs)
    with open('output', 'a+') as f:
        try:
            s = ' '.join(args) + '\n'
        except:
            s = ' '.join(str(args[0])) + '\n'
        f.write(s)

def init_server_files(usernames):
    for name in usernames:
        dir = 'server_fs/%s' % name
        if not os.path.exists(dir):
            os.makedirs(dir)
    filename = 'index'
    with open('client_fs/index', 'rb') as source:
        for name in usernames:
            dir = 'server_fs/%s' % name
            path = dir + '/' + filename
            with open(path, 'wb') as target:
                target.write(source.read())
            source.seek(0)

def init_server_dir(usernames):
    for name in usernames:
        dir = 'server_fs/%s' % name
        if not os.path.exists(dir):
            os.makedirs(dir)

def clear_dir(dir):
    names = os.listdir(dir)
    names.remove('index')
    paths = [dir+'/'+name for name in names]
    for path in paths:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

def get_free_port():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
    sock.bind(('', 0))
    addr = sock.getsockname()[0]
    port = sock.getsockname()[1]
    sock.close()
    return addr, port

def assert_response(username, password, requests, target_responses):
    client = Client(SERVER_ADDR, username, password)
    client.connect(SERVER_ADDR)
    try:
        for i in range(len(requests)):
            target = target_responses[i]
            req = requests[i]
            client.send_request(req)
            resp = client.get_response(req)
            assert resp == target
    finally:
        client.clear()


def kill_port():
    ports = ['20', '21']
    for port in ports:
        command = ["netstat -tlnp |grep :%s" % port]
        a = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

        # print(a.stdout.decode())

        result = a.stdout.decode()
        rows = result.split('\n')
        # print(result)
        target = []
        rows = rows[:-1]
        for r in rows:
            cols = r.split()
            pid_col = cols[-1]
            trailing = '/python3'
            if pid_col.endswith(trailing):
                pid = pid_col[:-len(trailing)]
                target.append(pid)
            else:
                raise Exception

        for pid in target:
            command = ['kill', '-9', pid]
            subprocess.run(command, stdout=subprocess.PIPE)

def kill_python_process():
    command = ["ps -C python3"]
    a = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

    result = a.stdout.decode()
    rows = result.split('\n')
    target = []
    rows = rows[1:-1]
    cur_pid = str(os.getpid())
    for r in rows:
        cols = r.split()
        pid = cols[0]
        if pid != cur_pid:
            target.append(pid)

    for pid in target:
        command = ['kill', '-9', pid]
        subprocess.run(command, stdout=subprocess.PIPE)

def setup_clear():
    pass
    # kill_port()
    # kill_python_process()
