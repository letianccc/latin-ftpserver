#coding=utf-8

import unittest
from test_util import *
import os
import re
import shutil
from multiprocessing import Pool, Manager, Queue, Barrier
from v2.ftp.client_ import Client
from v2.ftp.config import *
from multiprocessing.managers import BaseManager
import test_util

def login(client):
    req = 'USER %s\r\n' % client.name
    client.send_request(req)
    resp = client.get_response(req)
    assert '331 User name okay, need password' == resp
    req = 'PASS %s\r\n' % client.pswd
    client.send_request(req)
    resp = client.get_response(req)
    assert '230 User logged in, proceed' == resp

def exec_pasv(username, password):
    client = Client(SERVER_ADDR, username, password)
    client.connect(SERVER_ADDR)
    try:
        login(client)
        addr = client.get_free_port()
        client.make_data_connect(addr)
        request = 'PORT %s,%s\r\n' % addr
        client.send_request(request)
        client.get_response(request)

        request = 'PASV\r\n'
        client.send_request(request)
        resp = client.get_response(request)
        pattern = '(?P<response>.*) (?P<addr>(\d|.)*),(?P<port>\d+)'
        rs = re.match(pattern, resp)
        resp = rs.group('response')
        addr = rs.group('addr'), int(rs.group('port'))
        assert '227 Entering Passive Mode.' == resp
        client.make_data_connect(addr, True)
        client.data_sock.getpeername() == addr
    finally:
        client.clear()





class TestServer(BaseTest):

    def test_PASV(self):
        args = []
        prefix = 'admin'
        currency = 100
        usernames = []
        for i in range(currency):
            name = '%s%d' % (prefix, i)
            usernames.append(name)
        for i in range(currency):
            name = usernames[i]
            user = (name, i)
            args.append(user)
        with Pool(100) as pool:
            pool.starmap(exec_pasv, args)



    def login(self, username, password):
        client = Client(SERVER_ADDR, username, password)


    def init_client(self):
        pass

    def init_login(self):
        pass

    def init_data_connect(self):
        pass

    def clear_file(self):
        # return
        dir = 'server_fs'
        test_util.clear_dir(dir)
        dir = 'client_fs'
        test_util.clear_dir(dir)

    def clear_client(self):
        pass


if __name__ == '__main__':
    unittest.main()
