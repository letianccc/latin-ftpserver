#coding=utf-8

# import sys
# print(sys.path, flush=True)

import unittest

from v2.ftp.client_ import Client
from v2.ftp.config import *
from v2.util import kill_port, kill_python_process, log


from test_util import ServerThread, setup_clear, BaseTest
import os
import re
import shutil




class TestServer(BaseTest):

    def test_RETR(self):
        request = 'RETR %s\r\n' % self.target_filename
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        data = self.client.recv_data()
        with open(self.server_path, 'rb') as f:
            self.assertEqual(data, f.read())
        resp = self.client.get_response(request)
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        self.assertIsNone(self.client.data_sock)

    def test_BLOCK_RETR(self):
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        self.client.send_request(request)
        resp = self.client.get_response(request)

        request = 'RETR %s\r\n' % self.target_filename
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        data = self.client.recv_block()
        with open(self.server_path, 'rb') as f1:
            self.assertEqual(f1.read(), data)
        resp = self.client.get_response(request)
        self.assertEqual('250 Requested file action okay, completed', resp)
        self.assertNotEqual(-1, self.client.data_sock.fileno())

    def clear_file(self):
        dir = 'server_fs'
        names = os.listdir(dir)
        names.remove('index')
        paths = [dir+'/'+name for name in names]
        for path in paths:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        dir = 'client_fs'
        names = os.listdir(dir)
        names.remove('index')
        paths = [dir+'/'+name for name in names]
        for path in paths:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    def init_file(self):
        self.target_filename = 'p'
        self.server_path = 'server_fs/%s' % self.target_filename
        with open('client_fs/index', 'rb') as source:
            with open(self.server_path, 'wb') as target:
                target.write(source.read())

if __name__ == '__main__':
    unittest.main()
