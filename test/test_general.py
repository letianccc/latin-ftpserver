#coding=utf-8

import unittest
from v2.test.test_util import BaseTest, assert_response
from v2.ftp.config import *
from v2.ftp.client_ import Client
from v2.util import log
from multiprocessing import Pool
import json



def bad_sequence(unusable_arg):
    username = 'wrong_username'
    password = 'wrong_password'
    reqs = ['PASS %s\r\n' % password]
    resps = ['503 Bad sequence of commands']
    assert_response(username, password, reqs, resps)

def bad_command(unusable_arg):
    username = 'wrong_username'
    password = 'wrong_password'
    reqs = ['GET username\r\n']
    resps = ['502 Command not implemented']
    assert_response(username, password, reqs, resps)

class TestServer(BaseTest):

    def test_bad_sequence(self):
        with Pool() as pool:
            pool.map(bad_sequence, range(100))

    def test_bad_sequence(self):
        with Pool() as pool:
            pool.map(bad_command, range(100))

    def tearDown(self):
        self.client.clear()
        self.server.stop()

    def client_clear(self):
        self.client.clear()
    def init_login(self):
        pass

    def init_data_connect(self):
        pass

    def init_file(self):
        pass


if __name__ == '__main__':
    unittest.main()
