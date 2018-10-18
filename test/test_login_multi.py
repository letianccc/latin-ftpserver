#coding=utf-8

import unittest
from v2.test.test_util import BaseTest, assert_response
# from v2.ftp.config import *
from v2.ftp.client_ import Client
from v2.util import log
from multiprocessing import Pool
import json



def login(username, password):
    req1 = 'USER %s\r\n' % username
    req2 = 'PASS %s\r\n' % password
    reqs = [req1, req2]
    resp1 = '331 User name okay, need password'
    resp2 = '230 User logged in, proceed'
    resps = [resp1, resp2]
    assert_response(username, password, reqs, resps)


def wrong_user(unusable_arg):
    username = 'wrong_username'
    password = 'wrong_password'
    reqs = ['USER %s\r\n' % username]
    resps = ['530 Not logged in']
    assert_response(username, password, reqs, resps)


def wrong_pswd(username):
    password = 'wrong_password'
    req1 = 'USER %s\r\n' % username
    req2 = 'PASS %s\r\n' % password
    reqs = [req1, req2]
    resp1 = '331 User name okay, need password'
    resp2 = '530 Not logged in'
    resps = [resp1, resp2]
    assert_response(username, password, reqs, resps)

def without_login(unusable_arg):
    username = 'wrong_username'
    password = 'wrong_password'
    resps = ['530 Not logged in']
    pathname = 'p'
    requests = ['STOR %s\r\n' % pathname]
    assert_response(username, password, requests, resps)


class TestServer(BaseTest):
    def test_login(self):
        args = []
        prefix = 'admin'
        for i in range(100):
            name = '%s%d' % (prefix, i)
            user = (name, i)
            args.append(user)
        with Pool() as pool:
            pool.starmap(login, args)

    def test_wrong_user(self):
        with Pool() as pool:
            pool.map(wrong_user, range(100))

    def test_wrong_password(self):
        prefix = 'admin'
        usernames = ['%s%d' % (prefix, i) for i in range(100)]
        with Pool() as pool:
            pool.map(wrong_pswd, usernames)

    def test_without_login(self):
        with Pool() as pool:
            pool.map(without_login, range(100))

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
