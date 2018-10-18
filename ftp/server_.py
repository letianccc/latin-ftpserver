
from select import *
from socket import *
from .util import log
import re
from .entity.exception import CommandError
from .handler import ControlHandler
from time import sleep
from v2.ftp.config import *
import sys
import traceback

bufsize = 65536

class FTPServer:
    def __init__(self):
        self.epoll_fd = epoll()
        self.sock_list = {}
        self.ctrl_handler = None
        self.is_runing = False
        self.handlers = {}
        self.login_users = {}
        self.handlers_copy = []
        self.data_listeners = {}

    def listen(self, server_addr):
        self.ctrl_listen = self.create_listener(server_addr)

    def create_listener(self, server_addr):
        sock = self.get_socket(server_addr)
        sock.listen()
        self.register(sock)
        return sock

    def create_data_listener(self, handler):
        addr = self.get_free_port()
        sock = self.create_listener(addr)
        fd = sock.fileno()
        self.handlers[fd] = handler
        self.data_listeners[fd] = sock
        return addr

    def get_free_port(self):
        addr = ('localhost', 0)
        sock = self.get_socket(addr)
        addr = sock.getsockname()[0]
        port = sock.getsockname()[1]
        sock.close()
        return addr, port

    def connect(self, client_addr, server_addr):
        sock = self.get_socket(server_addr)
        try:
            sock.connect(client_addr)
        except ConnectionRefusedError:
            sock.close()
            raise ConnectionRefusedError
        sock.setblocking(True)
        return sock

    def get_socket(self, server_addr):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        sock.bind(server_addr)
        return sock

    def register(self, socket):
        fd = socket.fileno()
        self.sock_list[fd] = socket
        self.epoll_fd.register(fd, EPOLLIN)

    def unregister(self, fd):
        self.epoll_fd.unregister(fd)
        sock = self.sock_list.pop(fd)
        return sock

    def run(self):
        self.is_runing = True
        try:
            while self.is_run():
                epoll_list = self.epoll_fd.poll()
                for fd, event in epoll_list:
                    if self.is_listener(fd):
                        self.handle_listener(fd)
                    else:
                        self.handle_control(fd)
        except ValueError:
            pass
        except Exception as e:
            log(traceback.format_exc())
            raise e

    def is_listener(self, fd):
        if fd == self.ctrl_listen.fileno():
            return True
        if fd in self.data_listeners:
            return True
        return False

    def get_listener(self, fd):
        if fd == self.ctrl_listen.fileno():
            sock = self.ctrl_listen
        else:
            sock = self.data_listeners[fd]
        return sock

    def handle_listener(self, fd):
        listener = self.get_listener(fd)
        client, addr = listener.accept()
        # setblock暂时不可去
        #TODO 将setblock去掉
        client.setblocking(False)
        if listener == self.ctrl_listen:
            self.register_handler(client)
        else:
            self.handle_data_listener(listener, client)

    def handle_data_listener(self, listener, client):
        fd = listener.fileno()
        handler = self.handlers.pop(fd)
        handler.data_sock = client
        self.data_listeners.pop(fd)
        self.unregister(fd)
        listener.close()

    def register_handler(self, sock):
        self.register(sock)
        fd = sock.fileno()
        h = ControlHandler(sock, self)
        self.handlers[fd] = h
        self.handlers_copy.append(h)

    def handle_control(self, fd):
        self.set_handler(fd)
        self.ctrl_handler.handle(fd)

    def set_handler(self, fd):
        # sock = self.sock_list[fd]
        # self.ctrl_handler.set_socket(sock, fd)
        self.ctrl_handler = self.handlers[fd]

    def validate(self, path):
        # for test
        if path == '/500':
            raise ServerError
        if path == '/404':
            raise NotFound
        if path == '/403':
            raise Forbidden
        if path == '/400':
            raise BadRequest

        if not self.exist_file(path):
            raise NotFound
        if not self.have_read_permission(path):
            raise Forbidden

    def can_disconnect(self):
        return self.ctrl_handler.is_connected()

    def have_read_permission(self, path):
        if path == 'index.html':
            return True
        mode = stat(path).st_mode
        return mode & S_IRUSR or mode & S_IRGRP or mode & S_IROTH

    def exist_file(self, path):
        # if path == None or not isfile(path):
        #     return False
        # return True
        if path is not None:
            if path == 'index.html':
                return True
        return False

    def disconnect(self, sock):
        # unregister 放在最后 因为test线程检测sock_list决定是否退出
        # fd = self.ctrl_handler.sock.fileno()
        fd = sock.fileno()
        if sock == self.ctrl_handler.sock:
            self.handlers.pop(fd)
        self.ctrl_handler.disconnect(sock)
        sock = self.unregister(fd)

    def clear(self):
        fd = self.ctrl_listen.fileno()
        self.unregister(fd)
        self.ctrl_listen.close()
        for fd, sock in self.data_listeners.items():
            self.unregister(fd)
        # if self.data_listen:
        #     fd = self.data_listen.fileno()
        #     self.unregister(fd)
        #     self.data_listen.close()

    def is_run(self):
        return self.is_runing

    def stop(self):
        self.clear()
        while len(self.sock_list) != 0:
            sleep(0.01)
        self.epoll_fd.close()



    def get_handler(self):
        return list(self.handlers.values())[0]

    def get_handler_by_name(self, username):
        return self.login_users.get(username, None)

    def get_handlers_copy(self):
        return self.handlers_copy
