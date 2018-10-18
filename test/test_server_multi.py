#coding=utf-8

import unittest
from test_util import BaseTest, log
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

def mode(username, password):
    client = Client(SERVER_ADDR, username, password)
    client.connect(SERVER_ADDR)
    try:
        login(client)
        assert client.mode == 'S'
        req = 'MODE %s-%s\r\n' % ('B', 'Block')
        target = '200 Command okay'
        client.send_request(req)
        resp = client.get_response(req)
        assert resp == target
        assert client.mode == 'B'
    finally:
        client.clear()

def mode_fail(username, password):
    client = Client(SERVER_ADDR, username, password)
    client.connect(SERVER_ADDR)
    try:
        login(client)
        assert client.mode == 'S'
        req = 'MODE ABCDEF\r\n'
        target = '501 Syntax error in parameters or arguments'
        client.send_request(req)
        resp = client.get_response(req)
        assert resp == target
        assert client.mode == 'S'
    finally:
        client.clear()

def port(username, password):
    client = Client(SERVER_ADDR, username, password)
    try:
        client.connect(SERVER_ADDR)
        login(client)

        addr = client.get_free_port()
        client.make_data_connect(addr)
        request = 'PORT %s,%s\r\n' % addr
        client.send_request(request)
        resp = client.get_response(request)
        assert resp == '200 Command okay'
        assert client.data_sock.fileno() != -1

        addr = client.get_free_port()
        client.make_data_connect(addr)
        request = 'PORT %s,%s\r\n' % addr
        client.send_request(request)
        resp = client.get_response(request)
        assert resp == '200 Command okay'
        assert client.data_sock.fileno() != -1
    finally:
        client.clear()

def port_fail(username, password):
    client = Client(SERVER_ADDR, username, password)
    try:
        client.connect(SERVER_ADDR)
        login(client)

        addr = client.get_free_port()
        request = 'PORT %s,%s\r\n' % addr
        client.send_request(request)
        resp = client.get_response(request)
        assert resp == '501 Syntax error in parameters or arguments'
    finally:
        client.clear()

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

def mkd(username, password):
    client = Client(SERVER_ADDR, username, password)
    client.connect(SERVER_ADDR)
    try:
        login(client)
        dirname = username
        request = 'MKD %s\r\n' % dirname
        client.send_request(request)
        resp = client.get_response(request)
        dir_path = 'server_fs/%s' % dirname
        assert os.path.isdir(dir_path)
        assert '257 "%s" created' % dir_path == resp
    finally:
        client.clear()

def mkd_fail(username, password):
    client = Client(SERVER_ADDR, username, password)
    client.connect(SERVER_ADDR)
    try:
        login(client)
        dirname = username
        request = 'MKD %s\r\n' % dirname
        client.send_request(request)
        resp = client.get_response(request)
        dir_path = 'server_fs/%s' % dirname
        assert os.path.isdir(dir_path)
        assert '550 Requested action not taken.File unavailable' == resp
    finally:
        client.clear()

def exec_cwd(username, password):
    client = Client(SERVER_ADDR, username, password)
    client.connect(SERVER_ADDR)
    try:
        login(client)
        target_pwd = 'server_fs/%s' % username
        request = 'CWD %s\r\n' % target_pwd
        client.send_request(request)
        resp = client.get_response(request)
        assert '250 Requested file action okay, completed.' == resp
    finally:
        client.clear()

def exec_cdup(username, password):
    client = Client(SERVER_ADDR, username, password)
    client.connect(SERVER_ADDR)
    try:
        login(client)
        pwd = 'server_fs/%s' % client.name
        client.send_CWD(pwd)
        request = 'CDUP\r\n'
        client.send_request(request)
        resp = client.get_response(request)
        assert '250 Requested file action okay, completed.' == resp
    finally:
        client.clear()


class TestServer(BaseTest):

    def test_MODE(self):
        args = []
        prefix = 'admin'
        currency = 100
        for i in range(currency):
            name = '%s%d' % (prefix, i)
            user = (name, i)
            args.append(user)
        with Pool() as pool:
            pool.starmap(mode, args)
        handles = self.server.get_handlers_copy()
        assert len(handles) == currency
        for h in handles:
            assert h.mode == 'B'

    def test_MODE_fail(self):
        args = []
        prefix = 'admin'
        currency = 100
        for i in range(currency):
            name = '%s%d' % (prefix, i)
            user = (name, i)
            args.append(user)
        with Pool() as pool:
            pool.starmap(mode_fail, args)
        handles = self.server.get_handlers_copy()
        assert len(handles) == currency
        for h in handles:
            assert h.mode == 'S'

    def test_PORT(self):
        args = []
        prefix = 'admin'
        currency = 100
        for i in range(currency):
            name = '%s%d' % (prefix, i)
            user = (name, i)
            args.append(user)
        with Pool() as pool:
            pool.starmap(port, args)

    def test_PORT_fail(self):
        args = []
        prefix = 'admin'
        currency = 100
        for i in range(currency):
            name = '%s%d' % (prefix, i)
            user = (name, i)
            args.append(user)
        with Pool() as pool:
            pool.starmap(port_fail, args)

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

    def test_MKD(self):
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
        with Pool() as pool:
            pool.starmap(mkd, args)

    def test_MKD_fail(self):
        args = []
        prefix = 'admin'
        currency = 100
        usernames = []
        for i in range(currency):
            name = '%s%d' % (prefix, i)
            usernames.append(name)
        test_util.init_server_dir(usernames)
        for i in range(currency):
            name = usernames[i]
            user = (name, i)
            args.append(user)
        with Pool() as pool:
            pool.starmap(mkd_fail, args)

    def test_CWD(self):
        args = []
        prefix = 'admin'
        currency = 100
        usernames = []
        for i in range(currency):
            name = '%s%d' % (prefix, i)
            usernames.append(name)
        test_util.init_server_dir(usernames)
        for i in range(currency):
            name = usernames[i]
            user = (name, i)
            args.append(user)
        with Pool() as pool:
            pool.starmap(exec_cwd, args)
        parent = 'server_fs/'
        pwds = []
        for name in usernames:
            pwd = parent + name
            pwds.append(pwd)
        for handler in self.server.get_handlers_copy():
            assert handler.pwd in pwds

    def test_CDUP(self):
        args = []
        prefix = 'admin'
        currency = 100
        usernames = []
        for i in range(currency):
            name = '%s%d' % (prefix, i)
            usernames.append(name)
        test_util.init_server_dir(usernames)
        for i in range(currency):
            name = usernames[i]
            user = (name, i)
            args.append(user)
        with Pool() as pool:
            pool.starmap(exec_cdup, args)
        pwd = 'server_fs'
        for handler in self.server.get_handlers_copy():
            assert handler.pwd == pwd

    def login(self, username, password):
        client = Client(SERVER_ADDR, username, password)


    def init_client(self):
        pass

    def init_login(self):
        pass

    def init_data_connect(self):
        pass

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

    def clear_client(self):
        pass


if __name__ == '__main__':
    unittest.main()
